# gui_app.py
# Entry point for the AI D&D Game Master Streamlit app.
# This file is intentionally thin: it wires together modules from the package
# and handles the top-level Streamlit lifecycle.
#
# Module map:
#   config.py          — Constants, model list, default campaign data
#   database.py        — Supabase client + load/save/delete helpers
#   state_helpers.py   — Pure-Python character-state utilities
#   ai_engine.py       — OpenRouter client, prompts, campaign summary
#   styles.py          — Dark Fantasy CSS theme
#   ui/sidebar.py      — Character sheet, spells, vault controls
#   ui/chat_display.py — Chat history, rewind/edit popovers, auto-scroll
#   ui/dice_roller.py  — Dice roller expander + queued-action logic

import copy
import re

import streamlit as st

# --- PAGE CONFIGURATION (must be the very first Streamlit call) ---
st.set_page_config(
    page_title="AI D&D Game Master",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Local imports (after set_page_config)
from config import DEFAULT_CAMPAIGN
from database import init_supabase, load_db_campaign, save_db_campaign
from ai_engine import init_openai_client, call_openrouter, build_system_prompt, update_campaign_summary
from state_helpers import process_and_strip_character_state
from styles import inject_styles
from ui.sidebar import render_sidebar
from ui.chat_display import render_chat
from ui.dice_roller import render_dice_roller

# =============================================================================
# SECRETS & CLIENT SETUP
# =============================================================================

OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if not OPENROUTER_API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    st.error(
        "🔑 Secrets missing! Please set OPENROUTER_API_KEY, SUPABASE_URL, "
        "and SUPABASE_KEY in Streamlit Secrets."
    )
    st.stop()

supabase = init_supabase(SUPABASE_URL, SUPABASE_KEY)
client = init_openai_client(OPENROUTER_API_KEY)

# =============================================================================
# SESSION STATE — load campaign from DB on first run
# =============================================================================

if "campaign_data" not in st.session_state:
    db_data = load_db_campaign(supabase)
    st.session_state.campaign_data = db_data if db_data else DEFAULT_CAMPAIGN.copy()

campaign_data = st.session_state.campaign_data

# =============================================================================
# DETERMINE GAME PHASE & BUILD SYSTEM PROMPT
# =============================================================================

system_instruction, current_phase_name = build_system_prompt(campaign_data)

world_info = campaign_data.get("world_codex", "")
world_exists = bool(world_info.strip())
game_state = campaign_data.get("campaign_state", {})
character_created = game_state.get("player", {}).get("species") != "Unknown"

# =============================================================================
# APPLY THEME
# =============================================================================

inject_styles()

# =============================================================================
# SIDEBAR
# =============================================================================

render_sidebar(
    campaign_data=campaign_data,
    supabase=supabase,
    system_instruction=system_instruction,
    game_state=game_state,
    world_exists=world_exists,
    character_created=character_created,
)

# =============================================================================
# INITIALIZE CAMPAIGN MEMORY (first-ever load — no messages yet)
# =============================================================================

if not campaign_data.get("messages"):
    if not world_exists:
        opening_prompt = (
            "Greetings, World Architect! I am ready to build my new campaign setting. "
            "Please present me with the world-building questions to design our setting!"
        )
    else:
        opening_prompt = (
            "Greetings! I am ready for character creation. "
            "Please ask me for my character's details!"
        )

    opening_context = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": opening_prompt},
    ]

    try:
        response = call_openrouter(client, opening_context, st.session_state.get("current_model_slug"))
        opening_reply = response.choices[0].message.content
        campaign_data["messages"].append({
            "role": "assistant",
            "content": opening_reply,
            "text": opening_reply,
        })
        save_db_campaign(supabase, campaign_data)
        st.rerun()
    except Exception as e:
        st.error(f"Failed to connect to Game Master AI: {e}")

# =============================================================================
# HERO CAMPAIGN BANNER
# =============================================================================

current_location = game_state.get("current_location", "Unknown Lands")

st.markdown(
    f"""
<div class="hero-campaign-banner">
    <div>
        <h1 class="hero-banner-title">🎲 Chronicles of the Realm</h1>
        <p class="hero-banner-subtitle">Immersive AI Virtual Tabletop &bull; D&D 5e Solo Adventure</p>
    </div>
    <div class="hero-banner-badges">
        <span class="hero-phase-badge">🏛️ {current_phase_name}</span>
        <span class="hero-loc-badge">📍 {current_location}</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# =============================================================================
# CHAT HISTORY
# =============================================================================

render_chat(
    campaign_data=campaign_data,
    supabase=supabase,
    system_instruction=system_instruction,
)

# =============================================================================
# DICE ROLLER + CHAT INPUT
# =============================================================================

stats = game_state.get("player", {}).get(
    "stats", {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10}
)
queued_text = render_dice_roller(stats)

# --- Chat input form ---
with st.form(key="chat_form", clear_on_submit=True):
    col_text, col_btn = st.columns([0.88, 0.12])

    with col_text:
        user_input = st.text_area(
            "What do you do?",
            value=queued_text,
            height=85,
            key="user_action_input",
            placeholder=(
                "Describe your actions, speech, or cast a spell... "
                "(e.g. 'I draw my blade and inspect the ancient runes.')"
            ),
            label_visibility="collapsed",
        )

    with col_btn:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        submit_action = st.form_submit_button("⚔️ Send", use_container_width=True)

# =============================================================================
# HANDLE PLAYER SUBMISSION
# =============================================================================

if submit_action and user_input.strip():
    clean_user_input = str(user_input).strip()

    with st.chat_message("user"):
        st.write(clean_user_input)

    campaign_data["messages"].append({
        "role": "user",
        "content": clean_user_input,
        "text": clean_user_input,
    })

    with st.chat_message("assistant"):
        with st.spinner("The Game Master is narrating..."):
            MAX_HISTORY_TURNS = 8
            recent_history = campaign_data["messages"][-MAX_HISTORY_TURNS:]

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
                response = call_openrouter(client, api_messages, st.session_state.get("current_model_slug"))
                reply = response.choices[0].message.content
            except Exception as e:
                st.error(f"Failed to generate GM response: {e}")
                reply = None

    if reply:
        # Snapshot player state before the AI's CHARACTER_STATE block is applied so
        # that a future Rewind or Edit GM action can restore it cleanly.
        player_snapshot = copy.deepcopy(campaign_data["campaign_state"]["player"])
        reply = process_and_strip_character_state(reply, campaign_data)

        # Extract WORLD_CODEX if present (Phase 1 → Phase 2 transition)
        if "<WORLD_CODEX>" in reply.upper():
            pattern_codex = r"<WORLD_CODEX>(.*?)</WORLD_CODEX>"
            match_codex = re.search(pattern_codex, reply, re.DOTALL | re.IGNORECASE)
            if match_codex:
                campaign_data["world_codex"] = match_codex.group(1).strip()
            reply = re.sub(pattern_codex, "", reply, flags=re.DOTALL | re.IGNORECASE).strip()

        campaign_data["messages"].append({
            "role": "assistant",
            "content": reply,
            "text": reply,
            "player_state_before": player_snapshot,
        })

        # Periodically refresh the campaign summary (every 10 turns)
        if "turn_counter" not in st.session_state:
            st.session_state.turn_counter = 0
        st.session_state.turn_counter += 1

        if st.session_state.turn_counter % 10 == 0:
            with st.spinner("Recording chronicle into memory..."):
                update_campaign_summary(
                    client,
                    campaign_data,
                    st.session_state.get("current_model_slug"),
                    supabase,
                )

        save_db_campaign(supabase, campaign_data)
        st.rerun()