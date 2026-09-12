# ui/dice_roller.py
# Renders the collapsible tabletop dice roller expander and handles queued actions.

import random

import streamlit as st

from state_helpers import calculate_mod_str


def render_dice_roller(stats: dict) -> str:
    """Renders the 🎲 Quick Dice Roller expander.

    Returns any action text that was queued by the player clicking "Send to GM",
    or an empty string if nothing was queued this run.
    """
    with st.expander("🎲 Quick Dice Roller", expanded=False):
        col_d1, col_d2, col_d3, col_d4, col_d5, col_d6, col_mod = st.columns(
            [1, 1, 1, 1, 1, 1, 2.2]
        )

        rolled_sides = None
        if col_d1.button("d20", use_container_width=True, help="Roll d20 (Checks, Attacks, Saves)"):
            rolled_sides = 20
        if col_d2.button("d12", use_container_width=True, help="Roll d12"):
            rolled_sides = 12
        if col_d3.button("d10", use_container_width=True, help="Roll d10"):
            rolled_sides = 10
        if col_d4.button("d8", use_container_width=True, help="Roll d8"):
            rolled_sides = 8
        if col_d5.button("d6", use_container_width=True, help="Roll d6"):
            rolled_sides = 6
        if col_d6.button("d4", use_container_width=True, help="Roll d4"):
            rolled_sides = 4

        with col_mod:
            stat_mod_options = ["None (Flat)"]
            for s_name in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
                if s_name in stats:
                    s_val = stats[s_name]
                    s_mod = calculate_mod_str(s_val)
                    stat_mod_options.append(f"{s_name} ({s_mod})")
                else:
                    stat_mod_options.append(s_name)

            chosen_stat_label = st.selectbox(
                "Stat Bonus:",
                stat_mod_options,
                index=0,
                key="dice_mod_select",
                label_visibility="collapsed",
            )

        if rolled_sides:
            raw_roll = random.randint(1, rolled_sides)
            bonus_val = 0
            bonus_label = ""
            chosen_stat_key = (
                chosen_stat_label.split()[0]
                if not chosen_stat_label.startswith("None")
                else "None"
            )

            if chosen_stat_key != "None" and chosen_stat_key in stats:
                score = stats[chosen_stat_key]
                bonus_val = (score - 10) // 2
                sign = "+" if bonus_val >= 0 else ""
                bonus_label = f" {sign}{bonus_val} ({chosen_stat_key})"

            total_roll = raw_roll + bonus_val
            crit_msg = ""
            if rolled_sides == 20:
                if raw_roll == 20:
                    crit_msg = " 🔥 NATURAL 20! CRITICAL SUCCESS!"
                elif raw_roll == 1:
                    crit_msg = " 💀 NATURAL 1! CRITICAL FUMBLE!"

            roll_summary = (
                f"🎲 Rolled d{rolled_sides}: {raw_roll}{bonus_label} = **{total_roll}**{crit_msg}"
            )
            st.session_state["last_roll_text"] = roll_summary

        if "last_roll_text" in st.session_state:
            col_res, col_send = st.columns([0.75, 0.25])
            with col_res:
                st.markdown(
                    f"<div style='background:rgba(212,175,55,0.18); border:1px solid #d4af37; "
                    f"padding:8px 12px; border-radius:8px; color:#fce38a; font-size:0.9rem;'>"
                    f"{st.session_state['last_roll_text']}</div>",
                    unsafe_allow_html=True,
                )
            with col_send:
                if st.button("📤 Send to GM", key="send_roll_btn", type="primary", use_container_width=True):
                    st.session_state["queued_action"] = (
                        f"I roll a check: {st.session_state['last_roll_text']}"
                    )
                    del st.session_state["last_roll_text"]
                    st.rerun()

    # Consume and return any queued action text from this or a previous roll send.
    return st.session_state.pop("queued_action", "")
