# state_helpers.py
# Pure-Python helpers for character state manipulation.
# No Streamlit or database dependencies — safe to unit-test in isolation.

import copy
import json
import re

import streamlit as st


def calculate_mod_str(score) -> str:
    """Calculates the D&D 5e ability modifier string from an integer score.

    Returns a string like '+2' or '-1'.
    """
    try:
        score_val = int(score)
        mod = (score_val - 10) // 2
        return f"+{mod}" if mod >= 0 else f"{mod}"
    except (ValueError, TypeError):
        return "+0"


def process_and_strip_character_state(text: str, campaign_data: dict) -> str:
    """Parses a <CHARACTER_STATE> JSON block from *text*, updates *campaign_data* in-place,
    and returns the cleaned display text with the XML tag removed.

    The function is safe to call even when no tag is present — it returns *text* unchanged.
    """
    pattern = r"<CHARACTER_STATE>(.*?)</CHARACTER_STATE>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if match:
        raw_json = match.group(1).strip()
        # Strip optional markdown code fences the model may accidentally emit.
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.lower().startswith("json"):
                raw_json = raw_json[4:]

        try:
            parsed_state = json.loads(raw_json.strip())
            campaign_data["campaign_state"]["player"] = parsed_state
        except Exception as e:
            st.warning(f"Note: Character state update could not be parsed: {e}")

        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE).strip()

    return text


def restore_player_state_from_snapshot(snapshot: dict | None, campaign_data: dict):
    """Restores the campaign player state from a previously saved snapshot dict.

    Call this before re-processing a GM response to undo any spell slot, HP,
    or inventory changes that the original AI turn wrote to the character state.
    If *snapshot* is None or not a dict this is a no-op (safe to call unconditionally).
    """
    if snapshot and isinstance(snapshot, dict):
        campaign_data["campaign_state"]["player"] = copy.deepcopy(snapshot)
