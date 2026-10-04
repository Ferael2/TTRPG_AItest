# ui/chat_display.py
# Renders the chat message history, rewind/edit popovers, and auto-scroll widget.

import copy
import re

import streamlit as st
import streamlit.components.v1 as components

from ai_engine import call_openrouter, translate_narrative
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
        english_text = msg.get("content") or msg.get("text", "")

        # If Spanish mode is active and a cached translation exists, show it;
        # otherwise fall back to English (new messages without text_es are shown
        # in English until they get translated on the next write).
        current_lang = st.session_state.get("language", "en")
        if role == "assistant" and current_lang == "es":
            text_to_display = msg.get("text_es") or english_text
        else:
            text_to_display = english_text

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
                    _render_edit_gm_popover(idx, msg, english_text, campaign_data, supabase)

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
    """Renders the ⏮️ Rewind popover for a user message at *idx*, allowing the
    player to edit their input and rewind the story from that point forward.
    """
    user_msg = campaign_data["messages"][idx]
    current_text = user_msg.get("content") or user_msg.get("text", "")
    has_subsequent = idx < len(campaign_data["messages"]) - 1

    with st.popover("⏮️ Rewind", use_container_width=True):
        st.markdown("**Rewind & Edit Turn**")
        if has_subsequent:
            st.caption("Edit your input and rewind. All messages after this turn will be deleted to preserve the chat flow.")
        else:
            st.caption("Edit your input and request a new response from the Game Master.")

        edited_input = st.text_area(
            "Your Action:",
            value=current_text,
            height=120,
            key=f"edit_rewind_{idx}",
        )

        if st.button("Confirm Rewind", key=f"btn_rewind_{idx}", type="primary"):
            new_text = edited_input.strip()
            if not new_text:
                st.warning("Action text cannot be empty.")
                return

            # Restore player state from the snapshot before this turn took effect
            snapshot_to_restore = None
            if idx + 1 < len(campaign_data["messages"]):
                next_msg = campaign_data["messages"][idx + 1]
                if isinstance(next_msg, dict) and next_msg.get("player_state_before"):
                    snapshot_to_restore = next_msg.get("player_state_before")
            elif idx > 0:
                prev_msg = campaign_data["messages"][idx - 1]
                if isinstance(prev_msg, dict) and prev_msg.get("role") in ("assistant", "model"):
                    snapshot_to_restore = prev_msg.get("player_state_before")

            if snapshot_to_restore:
                restore_player_state_from_snapshot(snapshot_to_restore, campaign_data)

            # Update the user's action with the edited text
            user_msg["content"] = new_text
            user_msg["text"] = new_text
            user_msg.pop("text_es", None)

            # Delete any messages that come after this user message
            campaign_data["messages"] = campaign_data["messages"][: idx + 1]
            save_db_campaign(supabase, campaign_data)

            api_messages = _build_api_messages(campaign_data, system_instruction)

            with st.spinner("⚔️ The Game Master is responding to your revised action..."):
                try:
                    response = call_openrouter(
                        st.session_state.client,
                        api_messages,
                        st.session_state.get("current_model_slug"),
                    )
                    reply = response.choices[0].message.content

                    # Snapshot the restored player state before the new reply's state changes are applied
                    player_snapshot = copy.deepcopy(campaign_data["campaign_state"]["player"])
                    reply = process_and_strip_character_state(reply, campaign_data)

                    # Extract WORLD_CODEX if present (Phase 1 -> Phase 2 transition)
                    if "<WORLD_CODEX>" in reply.upper():
                        pattern_codex = r"<WORLD_CODEX>(.*?)</WORLD_CODEX>"
                        match_codex = re.search(pattern_codex, reply, re.DOTALL | re.IGNORECASE)
                        if match_codex:
                            campaign_data["world_codex"] = match_codex.group(1).strip()
                        reply = re.sub(pattern_codex, "", reply, flags=re.DOTALL | re.IGNORECASE).strip()

                    new_assistant_msg = {
                        "role": "assistant",
                        "content": reply,
                        "text": reply,
                        "player_state_before": player_snapshot,
                    }

                    # Translate GM reply if Spanish mode is active
                    if st.session_state.get("language", "en") == "es":
                        with st.spinner("🌐 Traduciendo al Español..."):
                            translated = translate_narrative(
                                st.session_state.client,
                                reply,
                                "es",
                                st.session_state.get("current_model_slug"),
                            )
                            new_assistant_msg["text_es"] = translated

                    campaign_data["messages"].append(new_assistant_msg)
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
