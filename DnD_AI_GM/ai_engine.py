# ai_engine.py
# OpenRouter client setup, API call helper, 3-phase system prompt builder,
# and campaign summary updater.

import json

import streamlit as st
from openai import OpenAI

from config import MODEL_OPTIONS, MAX_HISTORY_TURNS

# Supported language options: code → display name
SUPPORTED_LANGUAGES = {
    "en": "🇬🇧 English",
    "es": "🇲🇽 Español",
}

# Translation prompt template
_TRANSLATION_PROMPT = {
    "es": (
        "You are a professional literary translator specializing in tabletop roleplaying game narratives. "
        "Translate the following D&D Game Master text from English to Latin American Spanish.\n\n"
        "STRICT RULES:\n"
        "1. Preserve all proper nouns EXACTLY as-is: character names, place names, spell names, item names, faction names.\n"
        "2. Maintain the second-person dramatic fantasy tone (\"You...\" → \"Tú...\" or \"Usted...\" — prefer \"Tú\").\n"
        "3. Translate idioms and metaphors by their meaning and emotional weight, NOT literally.\n"
        "4. Preserve paragraph breaks, emphasis, and markdown formatting (bold, italic) exactly.\n"
        "5. Output ONLY the translated text. No explanations, no commentary, no prefixes.\n\n"
        "TEXT TO TRANSLATE:\n"
    ),
}



def init_openai_client(api_key: str) -> OpenAI:
    """Creates (or reuses from session state) the OpenAI-compatible OpenRouter client."""
    if "client" not in st.session_state:
        st.session_state.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return st.session_state.client


def call_openrouter(client: OpenAI, messages: list, selected_model_slug: str | None = None):
    """Calls the OpenRouter API with automatic model fallback.

    Tries *selected_model_slug* first, then falls through the full MODEL_OPTIONS list
    until a successful response is obtained.  Raises the last exception if all models fail.
    """
    fallback_queue = []
    if selected_model_slug:
        fallback_queue.append(selected_model_slug)

    for slug in MODEL_OPTIONS.values():
        if slug not in fallback_queue:
            fallback_queue.append(slug)

    last_error = None
    for model_name in fallback_queue:
        try:
            return client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=1500
            )
        except Exception as e:
            last_error = e
            continue

    raise last_error


def translate_narrative(client: OpenAI, text: str, target_lang: str, model_slug: str | None = None) -> str:
    """Translates GM narrative text into *target_lang* using a context-aware LLM call.

    Uses the same OpenRouter client so no extra API key is needed.
    Falls back to the original English text if translation fails.

    Args:
        client: The OpenAI-compatible OpenRouter client.
        text: English GM narrative to translate (CHARACTER_STATE tags must be pre-stripped).
        target_lang: ISO-639-1 language code (e.g. 'es'). 'en' is a no-op.
        model_slug: Preferred model slug; falls back to the default list if None.

    Returns:
        The translated text, or *text* unchanged if an error occurs.
    """
    if target_lang == "en" or target_lang not in _TRANSLATION_PROMPT:
        return text

    prompt_prefix = _TRANSLATION_PROMPT[target_lang]
    messages = [
        {
            "role": "user",
            "content": prompt_prefix + text,
        }
    ]

    try:
        response = call_openrouter(client, messages, model_slug)
        translated = response.choices[0].message.content.strip()
        return translated if translated else text
    except Exception:
        return text  # Gracefully degrade to English on failure


def build_system_prompt(campaign_data: dict) -> tuple[str, str]:
    """Determines the current game phase and returns (system_instruction, phase_name).

    Phase 1 — World Architect: no world codex exists yet.
    Phase 2 — Character Creator: world exists but character has not been created.
    Phase 3 — Active Game Master: world and character are both set up.
    """
    world_info = campaign_data.get("world_codex", "")
    world_exists = bool(world_info.strip())

    game_state = campaign_data.get("campaign_state", {})
    character_created = game_state.get("player", {}).get("species") != "Unknown"

    if not world_exists:
        phase_name = "Phase 1: World Creation"
        instruction = """
You are an expert TTRPG World Architect.
The player is starting a new campaign, but no world codex exists yet.

INSTRUCTIONS:
1. Ask the player 3-4 concise questions about Genre/Setting, Tone, Magic/Tech level, and Key Factions.
2. When the player answers, synthesize their choices inside <WORLD_CODEX>...</WORLD_CODEX>.
3. Right after closing </WORLD_CODEX>, welcome them to the setting and ask Character Creation questions: Name, Species, Class, Stats, Proficiencies, Equipment, and Backstory hooks.
"""

    elif not character_created:
        phase_name = "Phase 2: Character Creation"
        instruction = f"""
You are an expert D&D Character Creator.

WORLD SETTING:
{world_info}

CRITICAL FORMATTING INSTRUCTIONS:
1. If the player is a spellcaster, ask for their spell choices FIRST before outputting character state.
2. YOU MUST WRAP THE JSON STRICTLY INSIDE <CHARACTER_STATE> AND </CHARACTER_STATE> TAGS.
3. DO NOT USE MARKDOWN CODE BLOCKS (```json). OUTPUT THE RAW TAGS DIRECTLY IN TEXT.

Exact Required Output Format:
<CHARACTER_STATE>
{{
    "name": "William Clark",
    "species": "Vampire",
    "class": "Sorcerer",
    "level": 1,
    "hp": 7,
    "max_hp": 7,
    "ac": 15,
    "stats": {{"STR": 8, "DEX": 16, "CON": 14, "INT": 12, "WIS": 10, "CHA": 16}},
    "proficiencies": ["Persuasion", "Investigation"],
    "backstory": "Character backstory...",
    "inventory": ["Reinforced Coat", "Surgical Kit"],
    "spellcasting": {{
        "cantrips": ["Fire bolt", "Mage hand", "Friends", "Prestidigitation"],
        "prepared_spells": ["Shield", "Magic Missile"],
        "spell_slots": {{
            "level_1": {{"current": 2, "max": 2}}
        }}
    }}
}}
</CHARACTER_STATE>

Right below </CHARACTER_STATE>, begin the campaign's opening scene.
"""

    else:
        phase_name = "Phase 3: Active Campaign"
        campaign_summary = game_state.get("summary", "The campaign has just begun.")
        instruction = f"""
You are an expert TTRPG Game Master running a solo campaign.

WORLD SETTING & LORE:
{world_info}

PLAYER CHARACTER & STATS:
{json.dumps(game_state.get('player', {}), indent=2)}

CAMPAIGN SUMMARY & RECENT EVENTS:
{campaign_summary}

CURRENT GAME STATE:
{json.dumps(game_state, indent=2)}

GAME RULES:
1. Speak in 2nd person ("You enter...", "You see...").
2. Describe scenes with rich sensory details and immersive prose (aim for 3–4 descriptive paragraphs per response).
3. Refer strictly to CAMPAIGN SUMMARY for NPC statuses.
4. When the player attempts something risky, ask for D&D skill checks based on their stats and proficiencies.
5. LEVEL-UP, MULTICLASSING & SPELL SELECTION:
   - When the player levels up or chooses new spells/features, YOU MUST IMMEDIATELY OUTPUT AN UPDATED <CHARACTER_STATE>...</CHARACTER_STATE> JSON BLOCK containing the updated "level", "hp", "max_hp", "spellcasting", and "features".
   - Never acknowledge a level-up or new spells in narrative without emitting the <CHARACTER_STATE> block.
6. ARMOR CLASS (AC) & EQUIPMENT TRACKING:
   - Calculate and update "ac" inside <CHARACTER_STATE> whenever the player equips, dons, doffs, or acquires new armor, a shield, or magical equipment, or when their Dexterity modifier changes.
7. GM-DRIVEN SPELL SLOT MANAGEMENT:
   - When the player casts a leveled spell or consumes resources (e.g. spell slots, sorcery points), YOU MUST ALWAYS EMIT AN UPDATED <CHARACTER_STATE>...</CHARACTER_STATE> JSON BLOCK.
   - Do NOT simply write state changes as markdown bullet points. You must output the full <CHARACTER_STATE> JSON block so the sidebar updates automatically.
8. The player is allowed to romance NPCs.
9. Scenes with NSFW content are allowed.
10. End EVERY response with 2–3 logical options or ask "What do you do?".
"""

    return instruction.strip(), phase_name


def update_campaign_summary(client: OpenAI, campaign_data: dict, model_slug: str | None, supabase) -> str:
    """Calls the AI to produce an updated campaign summary and persists it.

    Returns the new summary string, or the existing one if the call fails.
    """
    existing_summary = campaign_data["campaign_state"].get("summary", "The campaign has just begun.")
    messages_to_use = campaign_data.get("messages", [])

    if not messages_to_use:
        return existing_summary

    recent_msgs = messages_to_use[-15:]
    formatted_recent = "\n".join([
        f"{m.get('role', 'user')}: {m.get('content') or m.get('text', '')}"
        for m in recent_msgs if isinstance(m, dict) and m.get("role") != "system"
    ])

    summary_prompt = [
        {"role": "system", "content": "You are an assistant summarizing a TTRPG campaign session."},
        {"role": "user", "content": f"""
UPDATE THE CAMPAIGN SUMMARY.

EXISTING SUMMARY:
{existing_summary}

RECENT EVENTS:
{formatted_recent}

INSTRUCTIONS:
Create an updated, concise summary under 250 words focusing on major plot developments and NPC statuses.
"""}
    ]

    try:
        response = call_openrouter(client, summary_prompt, model_slug)
        new_summary = response.choices[0].message.content.strip()
        campaign_data["campaign_state"]["summary"] = new_summary
        from database import save_db_campaign
        save_db_campaign(supabase, campaign_data)
        return new_summary
    except Exception:
        return existing_summary
