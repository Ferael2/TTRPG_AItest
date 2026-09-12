# ui/sidebar.py
# Renders the full sidebar: character sheet card, spells & inventory panels,
# model picker, campaign vault controls, and reset button.

import copy
import json

import streamlit as st

from ai_engine import call_openrouter, update_campaign_summary
from config import MODEL_OPTIONS
from database import save_db_campaign, delete_db_campaign
from state_helpers import calculate_mod_str, process_and_strip_character_state


def render_sidebar(
    campaign_data: dict,
    supabase,
    system_instruction: str,
    game_state: dict,
    world_exists: bool,
    character_created: bool,
):
    """Renders the full sidebar panel.

    Mutates *campaign_data* in-place when actions (retry, import, reset) are taken
    and calls st.rerun() as appropriate.
    """
    with st.sidebar:
        st.markdown(
            "<h2 class='rpg-title' style='color:#fce38a; margin-bottom:4px;'>⚔️ Character Sheet</h2>",
            unsafe_allow_html=True,
        )

        player_info = game_state.get("player", {})
        name = player_info.get("name", "Hero")
        species = player_info.get("species", "Unknown")
        p_class = player_info.get("class", "Adventurer")
        level = player_info.get("level", 1)
        hp = player_info.get("hp", 10)
        max_hp = player_info.get("max_hp", 10)
        ac = player_info.get("ac", 10)
        stats = player_info.get(
            "stats", {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10}
        )

        # --- Health bar colour ---
        hp_pct = max(0, min(100, int((hp / max_hp * 100) if max_hp > 0 else 0)))
        if hp_pct > 50:
            hp_grad = "linear-gradient(90deg, #10b981, #059669)"
        elif hp_pct > 25:
            hp_grad = "linear-gradient(90deg, #f59e0b, #d97706)"
        else:
            hp_grad = "linear-gradient(90deg, #ef4444, #dc2626)"

        # --- Character sheet card ---
        stat_boxes_html = "".join([
            f'<div class="stat-box"><div class="s-name">{k}</div>'
            f'<div class="s-val">{v}</div>'
            f'<div class="s-mod">{calculate_mod_str(v)}</div></div>'
            for k, v in stats.items()
        ])

        card_html = (
            f'<div class="character-sheet-card">'
            f'<div class="char-name-badge">'
            f'<div class="char-name-text">{name}</div>'
            f'<div class="char-level-badge">'
            f'<span class="char-level-label">Lv</span>'
            f'<span class="char-level-num">{level}</span>'
            f'</div></div>'
            f'<div class="char-tags">'
            f'<span class="tag-pill">🧬 {species}</span>'
            f'<span class="tag-pill">🗡️ {p_class}</span>'
            f'</div>'
            f'<div class="vitals-row">'
            f'<div class="hp-gauge">'
            f'<div class="hp-meta">'
            f'<span style="color:#ef4444;">❤️ Vitality</span>'
            f'<span style="color:#f8fafc;">{hp}/{max_hp} HP</span>'
            f'</div>'
            f'<div class="hp-bar-bg">'
            f'<div class="hp-bar-fill" style="width:{hp_pct}%; background:{hp_grad};"></div>'
            f'</div></div>'
            f'<div class="ac-shield-box">'
            f'<div class="ac-num">{ac}</div>'
            f'<div class="ac-label">AC</div>'
            f'</div></div>'
            f'<div class="stats-grid">{stat_boxes_html}</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        # --- Inventory expander ---
        with st.expander("🎒 Equipment & Inventory", expanded=False):
            inventory = player_info.get("inventory", [])
            if inventory:
                items_html = "".join([
                    f'<div class="inv-item-row">'
                    f'<span class="inv-item-bullet">📦</span>'
                    f'<span class="inv-item-name">{item}</span>'
                    f'</div>'
                    for item in inventory
                ])
                st.markdown(f'<div class="inv-vertical-list">{items_html}</div>', unsafe_allow_html=True)
            else:
                st.info("Inventory is empty.")

        # --- Spells expander ---
        with st.expander("✨ Arcane Spells & Slots", expanded=False):
            spell_data = player_info.get("spellcasting", {})
            cantrips = spell_data.get("cantrips", [])
            spells = spell_data.get("prepared_spells", [])
            slots = spell_data.get("spell_slots", {})

            if not cantrips and not spells and not slots:
                st.info("No active spellcasting capabilities.")
            else:
                if slots:
                    st.markdown("**Spell Slots Remaining:**")
                    for slot_lvl, slot_info in slots.items():
                        lvl_title = slot_lvl.replace("_", " ").title()
                        cur = slot_info.get("current", 0)
                        mx = slot_info.get("max", 0)
                        orbs = (
                            "<span class='mana-orb'></span>" * cur
                            + "<span class='mana-orb-empty'></span>" * max(0, mx - cur)
                        )
                        slot_card = (
                            f'<div class="spell-slot-card">'
                            f'<span style="font-size:0.8rem; font-weight:600;">{lvl_title}</span>'
                            f'<div>{orbs} <span style="font-size:0.8rem; color:#94a3b8;">({cur}/{mx})</span></div>'
                            f'</div>'
                        )
                        st.markdown(slot_card, unsafe_allow_html=True)

                if cantrips:
                    st.markdown("**Cantrips (At-Will):**")
                    c_html = "".join([
                        f'<div class="spell-item-row" style="border-left-color:#8b5cf6;">'
                        f'<span style="font-size:0.9rem;">🔮</span>'
                        f'<span style="flex:1;">{c}</span></div>'
                        for c in cantrips
                    ])
                    st.markdown(
                        f'<div class="inv-vertical-list" style="margin-bottom:8px;">{c_html}</div>',
                        unsafe_allow_html=True,
                    )

                if spells:
                    st.markdown("**Prepared Spells:**")
                    s_html = "".join([
                        f'<div class="spell-item-row" style="border-left-color:#38bdf8;">'
                        f'<span style="font-size:0.9rem;">📜</span>'
                        f'<span style="flex:1;">{s}</span></div>'
                        for s in spells
                    ])
                    st.markdown(f'<div class="inv-vertical-list">{s_html}</div>', unsafe_allow_html=True)

        # --- Model picker ---
        st.markdown("---")
        st.markdown(
            "<h3 class='rpg-title' style='font-size:1.1rem; color:#fce38a;'>🤖 AI Game Master Model</h3>",
            unsafe_allow_html=True,
        )
        selected_label = st.selectbox(
            "Choose Game Master AI Model:",
            options=list(MODEL_OPTIONS.keys()),
            index=0,
            label_visibility="collapsed",
        )
        st.session_state.current_model_slug = MODEL_OPTIONS[selected_label]

        # --- Campaign vault status ---
        st.markdown("---")
        st.markdown(
            "<h3 class='rpg-title' style='font-size:1.1rem; color:#fce38a;'>💾 Campaign Vault</h3>",
            unsafe_allow_html=True,
        )
        if world_exists and character_created:
            st.success("☁️ Cloud Sync Active (Full Lore & Game State)")
        elif not world_exists:
            st.info("🌐 Phase 1: World Architecting")
        else:
            st.info("🧙‍♂️ Phase 2: Character Creation")

        # --- Retry GM response (shown when last message is from user) ---
        messages_list = campaign_data.get("messages", [])
        if messages_list and messages_list[-1].get("role") == "user":
            st.warning("⚠️ The GM has not responded yet.")
            if st.button("🎲 Retry GM Response", use_container_width=True):
                with st.spinner("Invoking Game Master..."):
                    MAX_HISTORY_TURNS = 8
                    recent_history = messages_list[-MAX_HISTORY_TURNS:]

                    reminder_prompt = {
                        "role": "system",
                        "content": (
                            "REMINDER: Always write in 2nd person ('You...'). "
                            "Maintain strict continuity with the current scene. "
                            "Do not shift location or perspective abruptly."
                        ),
                    }

                    api_messages = (
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
                    try:
                        response = call_openrouter(
                            st.session_state.client,
                            api_messages,
                            st.session_state.get("current_model_slug"),
                        )
                        reply = response.choices[0].message.content
                        player_snapshot = copy.deepcopy(campaign_data["campaign_state"]["player"])
                        reply = process_and_strip_character_state(reply, campaign_data)
                        campaign_data["messages"].append({
                            "role": "assistant",
                            "content": reply,
                            "text": reply,
                            "player_state_before": player_snapshot,
                        })
                        save_db_campaign(supabase, campaign_data)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Retry failed: {e}")

        # --- Master save management ---
        with st.expander("⚙️ Master Save Management"):
            st.download_button(
                label="📥 Export Campaign JSON",
                data=json.dumps(campaign_data, indent=2),
                file_name="campaign_save.json",
                mime="application/json",
                use_container_width=True,
            )

            uploaded_master = st.file_uploader("📤 Import Campaign JSON", type=["json"], key="upload_master")
            if uploaded_master is not None:
                uploaded_json = json.load(uploaded_master)
                st.session_state.campaign_data = uploaded_json
                save_db_campaign(supabase, uploaded_json)
                st.success("Campaign synced to database!")
                st.rerun()

            if st.button("🔄 Summarize History", use_container_width=True):
                with st.spinner("Summarizing chronicle..."):
                    result = update_campaign_summary(
                        st.session_state.client,
                        campaign_data,
                        st.session_state.get("current_model_slug"),
                        supabase,
                    )
                    if result:
                        st.session_state["dev_summary_preview"] = result
                        st.success("Summary updated!")

        # --- Summary preview ---
        if "dev_summary_preview" in st.session_state:
            with st.expander("🔍 Summary Preview", expanded=True):
                st.write(st.session_state["dev_summary_preview"])
                if st.button("❌ Close Preview", use_container_width=True):
                    del st.session_state["dev_summary_preview"]
                    st.rerun()

        # --- Reset campaign ---
        st.markdown("---")
        if st.button("🗑️ Reset Campaign", use_container_width=True):
            from config import DEFAULT_CAMPAIGN
            delete_db_campaign(supabase)
            st.session_state.campaign_data = DEFAULT_CAMPAIGN.copy()
            st.rerun()
