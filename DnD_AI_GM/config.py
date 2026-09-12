# config.py
# Central configuration: constants, model list, and default campaign data structure.

# --- AI MODEL OPTIONS ---

# Verified, active model identifiers with automatic fallback
MODEL_OPTIONS = {
    "🧠 Meta Llama 3.3-70B (Best Instruction & Detail)": "meta-llama/llama-3.3-70b-instruct",
    "🎨 Qwen 3.5-27B (Rich Context & Storytelling)": "qwen/qwen3.5-27b",
    "⚡ DeepSeek Chat (Creative Dialogue & Roleplay)": "deepseek/deepseek-chat",
    "🌐 OpenRouter Auto (Smart Provider Fallback)": "openrouter/auto"
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
