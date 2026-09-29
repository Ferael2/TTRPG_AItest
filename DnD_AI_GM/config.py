# config.py
# Central configuration: constants, model list, and default campaign data structure.

# --- AI MODEL OPTIONS ---

# Free OpenRouter models suitable for general chat and creative roleplay.
MODEL_OPTIONS = {
    "OpenRouter Free Router (any available free model)": "openrouter/free",
    "Qwen 3.8 27B (free, general purpose)": "qwen/qwen3.8-27b:free",
    "Gemma 4 31B (free, instruction following)": "google/gemma-4-31b-it:free",
}

# Maximum number of recent conversation turns sent to the AI on each call.
MAX_HISTORY_TURNS = 8

# --- DEFAULT CAMPAIGN DATA STRUCTURE ---

DEFAULT_CAMPAIGN = {
    "world_codex": "",
    "campaign_state": {
        "player": {
            "name": "Hero",
            "species": "Unknown",
            "class": "Unknown",
            "level": 1,
            "hp": 10,
            "max_hp": 10,
            "ac": 10,
            "stats": {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
            "proficiencies": [],
            "backstory": "",
            "inventory": [],
            "spellcasting": {
                "cantrips": [],
                "prepared_spells": [],
                "spell_slots": {}
            }
        },
        "current_location": "Starting Realm",
        "key_npcs": [],
        "active_quests": [],
        "summary": "The campaign has just begun."
    },
    "messages": []
}
