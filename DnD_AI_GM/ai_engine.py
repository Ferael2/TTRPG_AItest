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


def call_openrouter(
    client: OpenAI,
    messages: list,
    selected_model_slug: str | None = None,
    max_tokens: int = 3000,
):
    """Calls the OpenRouter API with automatic model fallback.

    Tries *selected_model_slug* first, then falls through the full MODEL_OPTIONS list
    until a successful response is obtained. Raises the last exception if all models fail.
    """
    fallback_queue = []
    if selected_model_slug in MODEL_OPTIONS.values():
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
                max_tokens=max_tokens,
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
You are an expert TTRPG World Architect guiding a player through creating their custom campaign setting.
Currently, no world codex exists yet.

PHILOSOPHY & PACING RULES:
1. NEVER ASK EVERYTHING AT ONCE. The player does not need to have every detail planned in advance.
2. Guide the player ONE STEP AT A TIME using a "Core + Choose Your Focus" approach.
3. Keep your questions immersive, warm, and concise, and always provide 3-4 vivid, inspiring options or examples to make choosing effortless.
4. If the player proactively provides details for multiple steps at once, cheerfully incorporate them, and advance to the next step without repeating answered questions.
5. Do NOT generate the <WORLD_CODEX> tag until the core foundation and their chosen focus have been decided.

WORLD CREATION STEPS:
• STEP 1: Core Genre, Setting & Tone
  - Welcome the player warmly to the chronicle.
  - Ask about the core genre, setting, and atmosphere (e.g., Grimdark Gothic Horror, High Epic Fantasy, Steampunk / Magitech, Sunken Mythic Seas, Wild Mythic Frontier).
  - Provide 3-4 distinct flavor choices with vivid imagery.
  - DO NOT ask about magic rules, technology, or factions yet.

• STEP 2: Magic, Supernatural Rules & Technology
  - Build enthusiastically on their chosen genre and tone.
  - Ask about how magic and technology work in this world (e.g., Ubiquitous "wide magic" powering everyday devices vs. Rare/Forbidden perilous sorcery; Feudal medieval iron vs. Renaissance blackpowder and clockwork).
  - Provide 3-4 fitting options.

• STEP 3: The Focus Menu ("Choose What to Flesh Out")
  - Enthusiastically reflect their magic and tech choices.
  - Acknowledge that they don't need to plan every detail—they can choose what aspect of the world matters most to their story, and you will fill in the rest!
  - Present a clear menu of 4 focus areas and invite the player to pick 1 or 2 that excite them (or suggest their own idea):
      A) Gods, Pantheons & Ancient Mythos (Living deities, forgotten cosmic powers, or competing religious dogmas)
      B) Peoples, Cultures & Lineages (Unique cultural customs, unusual fantasy species, seafaring or nomadic clans)
      C) Factions, Politics & Looming War (Tyrannical empires, warring merchant guilds, insurgent rebellions)
      D) The Local Frontier & Starting Mystery (A lawless borderlands boom-town, an ancient cursed tomb, a besieged citadel)
  - Also let them know: if they prefer, they can simply say "Surprise me" or "You choose" and you will craft a cohesive setting for them.

• STEP 4: Deep-Dive Into the Player's Chosen Focus
  - Delve into the 1 or 2 focus areas the player selected with 1-2 focused, inspiring questions and rich suggestions.
  - Autonomously fill in reasonable, atmospheric background details for any aspects the player did not explicitly choose, ensuring the world feels complete and alive without burdening them.

• STEP 5: World Codex Synthesis & Transition to Character Creation
  - Once the chosen focus is explored (or if the player says they are ready / asks to begin):
  - Synthesize the complete world setting into rich lore and OUTPUT IT STRICTLY INSIDE:
    <WORLD_CODEX>
    [Comprehensive summary of the world: Setting Overview, Tone & Atmosphere, Magic & Technology, Key Factions & Peoples, and Starting Region / Mystery]
    </WORLD_CODEX>
  - IMPORTANT: In the same response immediately after </WORLD_CODEX>, celebrate the newly forged realm with an inspiring sentence.
  - Then, introduce CHARACTER CREATION STEP 1: Ask ONLY for their initial character concept, species, and class (proposing 3-4 thematic archetypes that strongly fit this newly created world). DO NOT ask for stats, equipment, proficiencies, or backstory yet!
"""

    elif not character_created:
        phase_name = "Phase 2: Character Creation"
        instruction = f"""
You are an expert D&D 5e Character Creator guiding the player to build their hero for the campaign.

WORLD SETTING & LORE:
{world_info}

CRITICAL PACING & STEP-BY-STEP RULES:
1. NEVER ASK EVERYTHING AT ONCE. Do NOT ask for name, species, class, stats, proficiencies, equipment, and backstory in a single message.
2. Guide the player ONE STEP AT A TIME. In each message, focus only on the current step.
3. Provide 2-4 evocative suggestions tailored to the world lore to inspire the player and make choices effortless.
4. If the player provides several character details at once (or says "make me an elven rogue" or "create a random character"), cheerfully accept their choices and ask only for the next missing step.
5. DO NOT OUTPUT the <CHARACTER_STATE> JSON block until the character is fully fleshed out (at minimum: Species, Class, Stats, and Spells if spellcaster) and the player is ready to begin!

CHARACTER CREATION STEPS:
• STEP 1: Character Concept, Species & Class
  - Ask what kind of adventurer they want to play in this world (Species & Class).
  - Offer 3-4 compelling archetypes that tie directly into the factions and themes of the world lore.

• STEP 2: Ability Scores / Stats & Playstyle
  - Based on their chosen species and class, propose a recommended Standard Array (15, 14, 13, 12, 10, 8) or Point Buy distribution tailored to their class's primary attributes (e.g. STR for Barbarian/Fighter, DEX for Rogue, INT for Wizard, CHA for Sorcerer/Bard/Warlock, WIS for Cleric/Druid).
  - Ask if they like this distribution or want to customize any scores.

• STEP 3: Background, Skills & Backstory Hook
  - Suggest 2-3 thematic D&D backgrounds (e.g., Criminal, Noble, Outlander, Sage, Soldier, Folk Hero) and skill proficiencies that tie them to the world's factions or ongoing conflict.
  - Ask for a brief personal goal, secret, or motivation.

• STEP 4: Equipment & Spell Selection (if spellcaster)
  - If martial: Confirm their starting weapons, armor, and gear.
  - If spellcaster: Suggest and confirm their Cantrips and 1st-level spells tailored to their class and theme before finalizing.

• STEP 5: Name & Distinguishing Details
  - If not already named, ask for their character's name and any notable physical feature, weapon nickname, or signature quirk.

• STEP 6: Final Character State & Opening Campaign Scene
  - When the character's details are established and the player is ready to begin:
  - YOU MUST OUTPUT THE FINAL STATE STRICTLY INSIDE <CHARACTER_STATE> AND </CHARACTER_STATE> TAGS.
  - DO NOT USE MARKDOWN CODE BLOCKS (```json). OUTPUT THE RAW TAGS DIRECTLY IN TEXT.

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

Immediately below </CHARACTER_STATE>, begin the campaign's opening scene:
Write an immersive, atmospheric scene (3-4 vivid paragraphs in 2nd person "You...") plunging the player directly into their first scenario in the world, and conclude with 2-3 logical options or ask "What do you do?".
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
