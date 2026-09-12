# ui/chat_display.py
# Renders the chat message history, rewind/edit popovers, and auto-scroll widget.

import copy

import streamlit as st
import streamlit.components.v1 as components

from ai_engine import call_openrouter
from database import save_db_campaign
from state_helpers import process_and_strip_character_state, restore_player_state_from_snapshot

# Number of most-recent messages shown before the "Full History" checkbox is used.
DISPLAY_LIMIT = 15


def render_chat(campaign_data: dict, supabase, system_instruction: str):
    """Renders the full chat history with rewind and edit-GM popovers.

    Also injects the auto-scroll JS widget.
    Mutates *campaign_data* in-place when rewind/edit actions are confirmed.
    """
    messages = campaign_data.get("messages", [])
    total_messages = len(messages)

    # Full-history toggle
    col_hist1, col_hist2 = st.columns([0.8, 0.2])
    with col_hist2:
        show_all = st.checkbox("📜 Full History", value=False)
    start_idx = 0 if show_all else max(0, total_messages - DISPLAY_LIMIT)

    for idx in range(start_idx, total_messages):
        msg = messages[idx]
        if not isinstance(msg, dict) or msg.get("role") == "system":
            continue

        raw_role = msg.get("role", "user")
        role = "assistant" if raw_role in ["assistant", "model"] else "user"
        text_to_display = msg.get("content") or msg.get("text", "")
        marker_class = "gm-message-marker" if role == "assistant" else "user-message-marker"

        with st.chat_message(role):
            st.markdown(
                f"<span class='{marker_class}' style='display:none;'></span>",
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns([0.88, 0.12])
            with col1:
                st.markdown(text_to_display)
            with col2:
                if role == "user":
                    _render_rewind_popover(idx, campaign_data, supabase, system_instruction)
                else:
                    _render_edit_gm_popover(idx, msg, text_to_display, campaign_data, supabase)

    # Auto-scroll anchor + JS
    st.markdown("<div id='bottom-scroll-anchor'></div>", unsafe_allow_html=True)
    components.html(
        """
        <script>
            function scrollToBottom() {
                try {
                    const parentDoc = window.parent.document;
                    const anchor = parentDoc.getElementById('bottom-scroll-anchor');
                    if (anchor) {
                        anchor.scrollIntoView({ behavior: 'smooth', block: 'end' });
                    }
                    const selectors = ['[data-testid="stMain"]', '[data-testid="stAppViewContainer"]', 'section.main'];
                    selectors.forEach(selector => {
                        const el = parentDoc.querySelector(selector);
                        if (el) el.scrollTop = el.scrollHeight;
                    });
                } catch (e) {}
            }
            scrollToBottom();
            setTimeout(scrollToBottom, 150);
            setTimeout(scrollToBottom, 400);
        </script>
        """,
        height=0,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_api_messages(campaign_data: dict, system_instruction: str, max_turns: int = 8) -> list:
    """Builds the messages list to send to the API from recent history."""
    recent_history = campaign_data["messages"][-max_turns:]
    reminder_prompt = {
        "role": "system",
        "content": (
            "REMINDER: Always write in 2nd person ('You...'). "
            "Maintain strict continuity with the current scene. "
            "Do not shift location or perspective abruptly."
        ),
    }
    return (
        [{"role": "system", "content": system_instruction}]
        + [
            {
                "role": "assistant" if m.get("role") in ["assistant", "model"] else "user",
                "content": m.get("content") or m.get("text", ""),
            }
            for m in recent_history
            if isinstance(m, dict) and m.get("role") != "system"
        ]
        + [reminder_prompt]
    )


def _render_rewind_popover(
    idx: int,
    campaign_data: dict,
    supabase,
    system_instruction: str,
):
    """Renders the ⏮️ Rewind popover for a user message at *idx*."""
    with st.popover("⏮️ Rewind", use_container_width=True):
        st.markdown("**Rewind To This Turn**")
        st.caption("Revert campaign state and retry your action from here.")
        if st.button("Confirm Rewind", key=f"btn_rewind_{idx}", type="primary"):
            # Restore player state from the snapshot stored in the preceding
            # assistant message so the rewound turn is cleanly undone.
            if idx > 0:
                prev_msg = campaign_data["messages"][idx - 1]
                if isinstance(prev_msg, dict) and prev_msg.get("role") in ("assistant", "model"):
                    restore_player_state_from_snapshot(
                        prev_msg.get("player_state_before"), campaign_data
                    )

            campaign_data["messages"] = campaign_data["messages"][: idx + 1]
            save_db_campaign(supabase, campaign_data)

            api_messages = _build_api_messages(campaign_data, system_instruction)

            try:
                response = call_openrouter(
                    st.session_state.client,
                    api_messages,
                    st.session_state.get("current_model_slug"),
                )
                reply = response.choices[0].message.content
                # Snapshot the (just-restored) player state before the new reply
                # is processed so future rewinds from this turn can also roll back.
                player_snapshot = copy.deepcopy(campaign_data["campaign_state"]["player"])
                reply = process_and_strip_character_state(reply, campaign_data)
                campaign_data["messages"].append({
                    "role": "assistant",
                    "content": reply,
                    "text": reply,
                    "player_state_before": player_snapshot,
                })
                save_db_campaign(supabase, campaign_data)
            except Exception as e:
                st.error(f"API Error during rewind: {e}")
            st.rerun()


def _render_edit_gm_popover(
    idx: int,
    msg: dict,
    text_to_display: str,
    campaign_data: dict,
    supabase,
):
    """Renders the ✏️ Edit GM popover for an assistant message at *idx*."""
    with st.popover("✏️ Edit GM", use_container_width=True):
        st.markdown("**Edit GM Response**")
        edited_gm_text = st.text_area(
            "Narrative Text:",
            value=text_to_display,
            height=160,
            key=f"edit_gm_{idx}",
        )
        if st.button("Save Edit", key=f"save_edit_{idx}", type="primary"):
            # Roll the player state back to what it was before this AI turn ran,
            # then re-apply any CHARACTER_STATE found in the edited text.
            # This ensures spell slots are restored if the edited text no longer
            # contains a spell-casting action.
            restore_player_state_from_snapshot(msg.get("player_state_before"), campaign_data)
            edited_text = process_and_strip_character_state(edited_gm_text, campaign_data)
            campaign_data["messages"][idx]["content"] = edited_text
            campaign_data["messages"][idx]["text"] = edited_text
            save_db_campaign(supabase, campaign_data)
            st.rerun()
