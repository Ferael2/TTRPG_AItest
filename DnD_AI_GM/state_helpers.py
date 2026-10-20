# state_helpers.py
# Pure-Python helpers for character state manipulation.
# No Streamlit or database dependencies — safe to unit-test in isolation.

import copy
import json
import re

import streamlit as st


def calculate_mod_int(score) -> int:
    """Calculates the integer D&D 5e ability modifier from a score."""
    try:
        score_val = int(score)
        return (score_val - 10) // 2
    except (ValueError, TypeError):
        return 0


def calculate_mod_str(score) -> str:
    """Calculates the D&D 5e ability modifier string from an integer score.

    Returns a string like '+2' or '-1'.
    """
    mod = calculate_mod_int(score)
    return f"+{mod}" if mod >= 0 else f"{mod}"


def deep_merge(target: dict, source: dict) -> dict:
    """Recursively merges source dict into target dict in-place."""
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            deep_merge(target[key], value)
        else:
            target[key] = copy.deepcopy(value)
    return target


def clean_and_parse_json(raw_text: str) -> dict | None:
    """Robustly cleans and parses a JSON string, handling code blocks,
    trailing commas, and surrounding commentary.
    """
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9]*\n?", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned).strip()

    # Strip trailing commas before closing braces/brackets
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    try:
        return json.loads(cleaned)
    except Exception:
        # Fallback: extract the outermost {...} block
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            sub = cleaned[first_brace : last_brace + 1]
            sub = re.sub(r",\s*([}\]])", r"\1", sub)
            try:
                return json.loads(sub)
            except Exception:
                pass
    return None


# Standard D&D 5e armor specifications: (base_ac, max_dex_bonus, is_shield)
ARMOR_DATABASE = {
    # Shields
    "shield": (2, None, True),
    # Light Armor (Full DEX)
    "padded": (11, None, False),
    "padded armor": (11, None, False),
    "leather": (11, None, False),
    "leather armor": (11, None, False),
    "reinforced coat": (11, None, False),
    "studded leather": (12, None, False),
    "studded leather armor": (12, None, False),
    # Medium Armor (Max +2 DEX)
    "hide": (12, 2, False),
    "hide armor": (12, 2, False),
    "chain shirt": (13, 2, False),
    "scale mail": (14, 2, False),
    "breastplate": (14, 2, False),
    "half plate": (15, 2, False),
    "half plate armor": (15, 2, False),
    # Heavy Armor (No DEX bonus)
    "ring mail": (14, 0, False),
    "chain mail": (16, 0, False),
    "splint": (17, 0, False),
    "splint armor": (17, 0, False),
    "plate": (18, 0, False),
    "plate armor": (18, 0, False),
    "full plate": (18, 0, False),
}


def calculate_best_ac(player: dict) -> int:
    """Calculates the best Armor Class based on player stats and inventory."""
    stats = player.get("stats")
    if not isinstance(stats, dict):
        stats = {}
    dex_mod = calculate_mod_int(stats.get("DEX", 10))
    con_mod = calculate_mod_int(stats.get("CON", 10))
    wis_mod = calculate_mod_int(stats.get("WIS", 10))
    p_class = str(player.get("class", "")).lower()

    # Unarmored Defense
    if "barbarian" in p_class:
        base_ac = 10 + dex_mod + con_mod
    elif "monk" in p_class:
        base_ac = 10 + dex_mod + wis_mod
    else:
        base_ac = 10 + dex_mod

    best_armor_ac = base_ac
    shield_bonus = 0

    inventory = player.get("inventory")
    if not isinstance(inventory, list):
        inventory = []
    for item in inventory:
        item_lower = str(item).strip().lower()
        for armor_name, (ac_val, max_dex, is_shield) in ARMOR_DATABASE.items():
            if armor_name in item_lower:
                if is_shield:
                    shield_bonus = max(shield_bonus, ac_val)
                else:
                    if max_dex is None:
                        calc_ac = ac_val + dex_mod
                    else:
                        calc_ac = ac_val + min(dex_mod, max_dex)
                    best_armor_ac = max(best_armor_ac, calc_ac)

    return best_armor_ac + shield_bonus


def process_and_strip_character_state(text: str, campaign_data: dict) -> str:
    """Parses a <CHARACTER_STATE> JSON block from *text*, deep-merges it into
    *campaign_data["campaign_state"]["player"]*, and returns the cleaned display text.

    Uses deep_merge so that partial updates (e.g. only spell slots or AC) do NOT wipe
    out other fields of the character sheet.
    """
    pattern = r"<CHARACTER_STATE>(.*?)</CHARACTER_STATE>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if match:
        raw_json = match.group(1).strip()
        parsed_state = clean_and_parse_json(raw_json)

        if parsed_state and isinstance(parsed_state, dict):
            current_player = campaign_data.get("campaign_state", {}).setdefault("player", {})
            deep_merge(current_player, parsed_state)
            # Ensure critical dict/list keys are never None or invalid types
            if not isinstance(current_player.get("spellcasting"), dict):
                current_player["spellcasting"] = {
                    "cantrips": [],
                    "prepared_spells": [],
                    "spell_slots": {},
                }
            else:
                sc = current_player["spellcasting"]
                if not isinstance(sc.get("cantrips"), list):
                    sc["cantrips"] = []
                if not isinstance(sc.get("prepared_spells"), list):
                    sc["prepared_spells"] = []
                if not isinstance(sc.get("spell_slots"), dict):
                    sc["spell_slots"] = {}
            if not isinstance(current_player.get("stats"), dict):
                current_player["stats"] = {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10}
            if not isinstance(current_player.get("inventory"), list):
                current_player["inventory"] = []
            if not isinstance(current_player.get("proficiencies"), list):
                current_player["proficiencies"] = []
        else:
            st.warning("Note: Character state update contained formatting issues and could not be parsed.")

        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE).strip()

    return text


def sync_character_mechanics_fallback(user_text: str, gm_text: str, campaign_data: dict):
    """Fallback safety net: if the AI forgot to emit <CHARACTER_STATE>, this inspects
    both the player's action and GM narration for spell casting, armor equipping, or rests,
    and updates character state accordingly.
    """
    player = campaign_data.get("campaign_state", {}).get("player")
    if not isinstance(player, dict) or player.get("species") == "Unknown":
        return

    combined_text = f"{user_text}\n{gm_text}".lower()

    # 1. Long Rest detection
    if re.search(r"\b(long rest|takes? a long rest|finished a long rest)\b", combined_text):
        player["hp"] = player.get("max_hp", 10)
        spellcasting = player.get("spellcasting")
        if isinstance(spellcasting, dict):
            spell_slots = spellcasting.get("spell_slots")
            if isinstance(spell_slots, dict):
                for _, slot in spell_slots.items():
                    if isinstance(slot, dict) and "max" in slot:
                        slot["current"] = slot["max"]
        return

    # 2. Spell slot deduction fallback
    spellcasting = player.get("spellcasting")
    if not isinstance(spellcasting, dict):
        spellcasting = {}
    prepared = spellcasting.get("prepared_spells") or []
    if not isinstance(prepared, list):
        prepared = []
    cantrips_raw = spellcasting.get("cantrips") or []
    if not isinstance(cantrips_raw, list):
        cantrips_raw = []
    cantrips = [str(c).lower() for c in cantrips_raw]
    spell_slots = spellcasting.get("spell_slots") or {}
    if not isinstance(spell_slots, dict):
        spell_slots = {}

    for spell in prepared:
        spell_name = str(spell).strip().lower()
        if not spell_name or spell_name in cantrips:
            continue  # Cantrips cost 0 slots

        # Look for casting verbs or explicit spell naming in user action or narration
        cast_pattern = rf"\b(cast|casts|casting|conjure|unleash)\b.*?{re.escape(spell_name)}"
        explicit_cast = re.search(cast_pattern, user_text, re.IGNORECASE) or re.search(cast_pattern, gm_text, re.IGNORECASE)
        named_in_action = re.search(rf"\b{re.escape(spell_name)}\b", user_text, re.IGNORECASE)

        if explicit_cast or named_in_action:
            # Deduct the lowest available slot level
            for level_key in sorted(spell_slots.keys()):
                slot = spell_slots[level_key]
                if isinstance(slot, dict) and slot.get("current", 0) > 0:
                    slot["current"] = max(0, slot["current"] - 1)
                    break
            break  # Deduct one spell per turn

    # 3. AC & Armor update fallback
    for armor_name in ARMOR_DATABASE:
        if re.search(rf"\b(equip|equips|dons|donning|wear|wears|wearing|purchased?|buys?)\b.*?{re.escape(armor_name)}", combined_text):
            # Ensure armor is recorded in inventory
            inv = player.get("inventory")
            if not isinstance(inv, list):
                inv = []
                player["inventory"] = inv
            title_name = armor_name.title()
            if not any(armor_name in str(item).lower() for item in inv):
                inv.append(title_name)

            best_ac = calculate_best_ac(player)
            if best_ac > player.get("ac", 10):
                player["ac"] = best_ac
            break


def restore_player_state_from_snapshot(snapshot: dict | None, campaign_data: dict):
    """Restores the campaign player state from a previously saved snapshot dict.

    Call this before re-processing a GM response to undo any spell slot, HP,
    or inventory changes that the original AI turn wrote to the character state.
    If *snapshot* is None or not a dict this is a no-op (safe to call unconditionally).
    """
    if snapshot and isinstance(snapshot, dict):
        campaign_data["campaign_state"]["player"] = copy.deepcopy(snapshot)

