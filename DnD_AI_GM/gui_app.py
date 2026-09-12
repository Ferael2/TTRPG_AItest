import json
import random
import re
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
from supabase import create_client, Client

# --- PAGE CONFIGURATION (SINGLE TOP CALL) ---
st.set_page_config(
    page_title="AI D&D Game Master",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SUPABASE & OPENROUTER SETUP ---

OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if not OPENROUTER_API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    st.error("🔑 Secrets missing! Please set OPENROUTER_API_KEY, SUPABASE_URL, and SUPABASE_KEY in Streamlit Secrets.")
    st.stop()

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

if "client" not in st.session_state:
    st.session_state.client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

# Verified, active model identifiers with automatic fallback
MODEL_OPTIONS = {
    "🧠 Meta Llama 3.3-70B (Best Instruction & Detail)": "meta-llama/llama-3.3-70b-instruct",
    "🎨 Qwen 3.5-27B (Rich Context & Storytelling)": "qwen/qwen3.5-27b",
    "⚡ DeepSeek Chat (Creative Dialogue & Roleplay)": "deepseek/deepseek-chat",
    "🌐 OpenRouter Auto (Smart Provider Fallback)": "openrouter/auto"
}

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

# --- DATABASE STORAGE FUNCTIONS ---

def load_db_campaign():
    """Loads campaign record from Supabase database."""
    try:
        response = supabase.table("campaigns").select("data").eq("id", "default_campaign").execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["data"]
    except Exception as e:
        st.error(f"Error loading from Supabase: {e}")
    return None

def save_db_campaign(data):
    """Saves full campaign record to Supabase database."""
    try:
        supabase.table("campaigns").upsert({"id": "default_campaign", "data": data}).execute()
    except Exception as e:
        st.error(f"Error saving to Supabase: {e}")

def delete_db_campaign():
    """Resets campaign record in Supabase database."""
    try:
        supabase.table("campaigns").delete().eq("id", "default_campaign").execute()
    except Exception as e:
        st.error(f"Error resetting Supabase record: {e}")

def process_and_strip_character_state(text, campaign_data):
    """Parses <CHARACTER_STATE> JSON from text, updates campaign_data, and returns clean display text."""
    pattern = r"<CHARACTER_STATE>(.*?)</CHARACTER_STATE>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        raw_json = match.group(1).strip()
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

def calculate_mod_str(score):
    """Calculates D&D 5e ability modifier string from an integer score."""
    try:
        score_val = int(score)
        mod = (score_val - 10) // 2
        return f"+{mod}" if mod >= 0 else f"{mod}"
    except (ValueError, TypeError):
        return "+0"

# Initialize Session Data from Cloud DB
if "campaign_data" not in st.session_state:
    db_data = load_db_campaign()
    if db_data:
        st.session_state.campaign_data = db_data
    else:
        st.session_state.campaign_data = DEFAULT_CAMPAIGN.copy()

campaign_data = st.session_state.campaign_data

# --- API HELPER FUNCTIONS ---

def call_openrouter(messages, selected_model_slug=None):
    fallback_queue = []
    if selected_model_slug:
        fallback_queue.append(selected_model_slug)
    
    for slug in MODEL_OPTIONS.values():
        if slug not in fallback_queue:
            fallback_queue.append(slug)

    last_error = None
    for model_name in fallback_queue:
        try:
            return st.session_state.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=1500
            )
        except Exception as e:
            last_error = e
            continue
            
    raise last_error

def update_campaign_summary():
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
        response = call_openrouter(summary_prompt, st.session_state.get("current_model_slug"))
        new_summary = response.choices[0].message.content.strip()
        campaign_data["campaign_state"]["summary"] = new_summary
        save_db_campaign(campaign_data)
        return new_summary
    except Exception as e:
        return existing_summary

# --- DYNAMIC 3-PHASE SYSTEM PROMPTS ---

world_info = campaign_data.get("world_codex", "")
world_exists = bool(world_info.strip())

game_state = campaign_data.get("campaign_state", {})
character_created = game_state.get("player", {}).get("species") != "Unknown"

if not world_exists:
    # Phase 1: World Architect
    current_phase_name = "Phase 1: World Creation"
    system_instruction = """
You are an expert TTRPG World Architect.
The player is starting a new campaign, but no world codex exists yet.

INSTRUCTIONS:
1. Ask the player 3-4 concise questions about Genre/Setting, Tone, Magic/Tech level, and Key Factions.
2. When the player answers, synthesize their choices inside <WORLD_CODEX>...</WORLD_CODEX>.
3. Right after closing </WORLD_CODEX>, welcome them to the setting and ask Character Creation questions: Name, Species, Class, Stats, Proficiencies, Equipment, and Backstory hooks.
"""

elif not character_created:
    # Phase 2: Character Creator
    current_phase_name = "Phase 2: Character Creation"
    system_instruction = f"""
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
    # Phase 3: Active Game Master
    current_phase_name = "Phase 3: Active Campaign"
    campaign_summary = game_state.get("summary", "The campaign has just begun.")
    system_instruction = f"""
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

# --- INJECT CUSTOM DARK FANTASY CSS ---

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

/* Global Font & Atmosphere */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #0b0f19 !important;
    color: #e2e8f0 !important;
}

/* Atmospheric subtle vignette */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at 50% 10%, rgba(212, 175, 55, 0.04) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
}

/* Cinzel for Titles and RPG Headers */
h1, h2, h3, .rpg-title, .cinzel-font {
    font-family: 'Cinzel', serif !important;
    letter-spacing: 0.05em !important;
}

/* Main Container Padding */
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 7rem !important;
    max-width: 95% !important;
}

/* --- SIDEBAR STYLING --- */
[data-testid="stSidebar"] {
    background-color: #0d121e !important;
    border-right: 1px solid rgba(212, 175, 55, 0.2) !important;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.5) !important;
}

[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #e5c365 !important;
}

/* Sidebar Custom Character Sheet Card */
.character-sheet-card {
    background: linear-gradient(145deg, #131a29, #101522);
    border: 1px solid rgba(212, 175, 55, 0.35);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 14px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.char-name-badge {
    font-family: 'Cinzel', serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #fce38a;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
}

.char-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}

.tag-pill {
    background: rgba(212, 175, 55, 0.15);
    border: 1px solid rgba(212, 175, 55, 0.4);
    color: #f7d774;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 9999px;
    letter-spacing: 0.03em;
}

/* Vitality & AC Row */
.vitals-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
}

.hp-gauge {
    flex: 1;
    background: #090d15;
    border-radius: 8px;
    padding: 8px 10px;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.hp-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 4px;
}

.hp-bar-bg {
    width: 100%;
    height: 8px;
    background: #1e293b;
    border-radius: 4px;
    overflow: hidden;
}

.hp-bar-fill {
    height: 100%;
    transition: width 0.4s ease;
    border-radius: 4px;
}

.ac-shield-box {
    width: 54px;
    height: 54px;
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 2px solid #38bdf8;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
}

.ac-num {
    font-family: 'Cinzel', serif;
    font-size: 1.2rem;
    font-weight: 800;
    color: #38bdf8;
    line-height: 1;
}

.ac-label {
    font-size: 0.6rem;
    font-weight: 700;
    color: #94a3b8;
    letter-spacing: 0.05em;
}

/* Ability Score 6-Card Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-top: 10px;
    margin-bottom: 12px;
}

.stat-box {
    background: #0d121c;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 6px 4px;
    text-align: center;
    transition: transform 0.15s ease, border-color 0.15s ease;
}

.stat-box:hover {
    border-color: rgba(212, 175, 55, 0.5);
    transform: translateY(-2px);
}

.stat-box .s-name {
    font-size: 0.65rem;
    font-weight: 700;
    color: #94a3b8;
    letter-spacing: 0.05em;
}

.stat-box .s-val {
    font-family: 'Cinzel', serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #f1f5f9;
}

.stat-box .s-mod {
    font-size: 0.75rem;
    font-weight: 700;
    color: #d4af37;
    background: rgba(212, 175, 55, 0.12);
    border-radius: 4px;
    display: inline-block;
    padding: 1px 4px;
    margin-top: 2px;
}

/* Spell Slots Visual Orbs */
.spell-slot-card {
    background: #0d1320;
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 8px;
    padding: 8px 10px;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.mana-orb {
    display: inline-block;
    width: 11px;
    height: 11px;
    border-radius: 50%;
    margin-right: 4px;
    background: #8b5cf6;
    box-shadow: 0 0 8px #a855f7;
}

.mana-orb-empty {
    display: inline-block;
    width: 11px;
    height: 11px;
    border-radius: 50%;
    margin-right: 4px;
    border: 1px dashed #64748b;
    background: transparent;
}

/* Inventory Item Chips */
.inv-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.78rem;
    color: #cbd5e1;
    margin: 2px 2px;
}

/* --- HERO CAMPAIGN BANNER --- */
.hero-campaign-banner {
    background: linear-gradient(135deg, rgba(19, 26, 41, 0.95), rgba(13, 18, 30, 0.95));
    border: 1px solid rgba(212, 175, 55, 0.35);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}

.hero-banner-title {
    font-family: 'Cinzel', serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #f7d774;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
    text-shadow: 0 2px 10px rgba(212, 175, 55, 0.25);
}

.hero-banner-subtitle {
    font-size: 0.85rem;
    color: #94a3b8;
    margin: 2px 0 0 0;
}

.hero-banner-badges {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

.hero-phase-badge {
    background: linear-gradient(135deg, rgba(212, 175, 55, 0.2), rgba(212, 175, 55, 0.05));
    border: 1px solid #d4af37;
    color: #fce38a;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 5px 12px;
    border-radius: 20px;
    letter-spacing: 0.04em;
}

.hero-loc-badge {
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.4);
    color: #7dd3fc;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 20px;
}

/* --- CHAT MESSAGE STYLING --- */
[data-testid="stChatMessage"] {
    background: transparent !important;
    padding: 8px 0 !important;
}

/* GM (Assistant) Message Card: Tome / Scroll Design */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) > div:nth-child(2),
[data-testid="stChatMessage"] > div:nth-child(2):has(.gm-message-marker) {
    background: linear-gradient(145deg, #131926, #0e131d) !important;
    border-left: 3px solid #d4af37 !important;
    border-top: 1px solid rgba(212, 175, 55, 0.18) !important;
    border-right: 1px solid rgba(212, 175, 55, 0.12) !important;
    border-bottom: 1px solid rgba(212, 175, 55, 0.18) !important;
    border-radius: 10px !important;
    padding: 16px 20px !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.3) !important;
}

/* Player (User) Message Card: Azure Adventurer Accent */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) > div:nth-child(2),
[data-testid="stChatMessage"] > div:nth-child(2):has(.user-message-marker) {
    background: linear-gradient(145deg, #0e1b2f, #091322) !important;
    border-left: 3px solid #38bdf8 !important;
    border-top: 1px solid rgba(56, 189, 248, 0.18) !important;
    border-right: 1px solid rgba(56, 189, 248, 0.12) !important;
    border-bottom: 1px solid rgba(56, 189, 248, 0.18) !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25) !important;
}

/* Popover & Action Buttons */
[data-testid="stChatMessage"] div[data-testid="stPopover"] > button {
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    background: rgba(255, 255, 255, 0.04) !important;
    color: #cbd5e1 !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stChatMessage"] div[data-testid="stPopover"] > button:hover {
    border-color: #d4af37 !important;
    color: #f7d774 !important;
    background: rgba(212, 175, 55, 0.1) !important;
}

/* --- DICE ROLLER & QUICK ACTIONS DOCK --- */
.quick-action-bar {
    background: #111724;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 8px 12px;
    margin-top: 12px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

/* --- CHAT INPUT FORM & COMMAND DOCK --- */
div[data-testid="stForm"] {
    background: #0f1624 !important;
    border: 1px solid rgba(212, 175, 55, 0.3) !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    box-shadow: 0 -4px 25px rgba(0, 0, 0, 0.45) !important;
}

div[data-testid="stForm"]:focus-within {
    border-color: #d4af37 !important;
    box-shadow: 0 0 16px rgba(212, 175, 55, 0.3) !important;
}

div[data-testid="stForm"] textarea {
    background: #090e18 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    color: #f8fafc !important;
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
}

div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #d4af37, #b89127) !important;
    color: #0b0f19 !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    padding: 8px 18px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 10px rgba(212, 175, 55, 0.3) !important;
}

div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, #f7d774, #d4af37) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(212, 175, 55, 0.45) !important;
}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---

with st.sidebar:
    st.markdown("<h2 class='rpg-title' style='color:#fce38a; margin-bottom:4px;'>⚔️ Character Sheet</h2>", unsafe_allow_html=True)
    
    player_info = game_state.get("player", {})
    name = player_info.get("name", "Hero")
    species = player_info.get("species", "Unknown")
    p_class = player_info.get("class", "Adventurer")
    level = player_info.get("level", 1)
    hp = player_info.get("hp", 10)
    max_hp = player_info.get("max_hp", 10)
    ac = player_info.get("ac", 10)
    stats = player_info.get("stats", {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10})
    
    # Calculate health bar percentage and color
    hp_pct = max(0, min(100, int((hp / max_hp * 100) if max_hp > 0 else 0)))
    if hp_pct > 50:
        hp_grad = "linear-gradient(90deg, #10b981, #059669)"
    elif hp_pct > 25:
        hp_grad = "linear-gradient(90deg, #f59e0b, #d97706)"
    else:
        hp_grad = "linear-gradient(90deg, #ef4444, #dc2626)"

    # Render Character Sheet Card
    stat_boxes_html = "".join([
        f"""
        <div class="stat-box">
            <div class="s-name">{k}</div>
            <div class="s-val">{v}</div>
            <div class="s-mod">{calculate_mod_str(v)}</div>
        </div>
        """
        for k, v in stats.items()
    ])

    st.markdown(f"""
    <div class="character-sheet-card">
        <div class="char-name-badge">
            <span>{name}</span>
            <span class="tag-pill">Lv {level}</span>
        </div>
        <div class="char-tags">
            <span class="tag-pill">🧬 {species}</span>
            <span class="tag-pill">🗡️ {p_class}</span>
        </div>
        <div class="vitals-row">
            <div class="hp-gauge">
                <div class="hp-meta">
                    <span style="color:#ef4444;">❤️ Vitality</span>
                    <span style="color:#f8fafc;">{hp}/{max_hp} HP</span>
                </div>
                <div class="hp-bar-bg">
                    <div class="hp-bar-fill" style="width:{hp_pct}%; background:{hp_grad};"></div>
                </div>
            </div>
            <div class="ac-shield-box">
                <div class="ac-num">{ac}</div>
                <div class="ac-label">AC</div>
            </div>
        </div>
        <div class="stats-grid">
            {stat_boxes_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🎒 Equipment & Inventory", expanded=False):
        inventory = player_info.get("inventory", [])
        if inventory:
            inv_html = "".join([f"<span class='inv-tag'>📦 {item}</span>" for item in inventory])
            st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:4px;'>{inv_html}</div>", unsafe_allow_html=True)
        else:
            st.info("Inventory is empty.")

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
                    orbs = ("<span class='mana-orb'></span>" * cur) + ("<span class='mana-orb-empty'></span>" * max(0, mx - cur))
                    st.markdown(f"""
                    <div class="spell-slot-card">
                        <span style="font-size:0.8rem; font-weight:600;">{lvl_title}</span>
                        <div>{orbs} <span style="font-size:0.8rem; color:#94a3b8;">({cur}/{mx})</span></div>
                    </div>
                    """, unsafe_allow_html=True)

            if cantrips:
                st.markdown("**Cantrips (At-Will):**")
                c_html = "".join([f"<span class='inv-tag' style='border-color:#8b5cf6;'>🔮 {c}</span>" for c in cantrips])
                st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:4px; margin-bottom:8px;'>{c_html}</div>", unsafe_allow_html=True)

            if spells:
                st.markdown("**Prepared Spells:**")
                s_html = "".join([f"<span class='inv-tag' style='border-color:#38bdf8;'>📜 {s}</span>" for s in spells])
                st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:4px;'>{s_html}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<h3 class='rpg-title' style='font-size:1.1rem; color:#fce38a;'>🤖 AI Game Master Model</h3>", unsafe_allow_html=True)
    selected_label = st.selectbox(
        "Choose Game Master AI Model:",
        options=list(MODEL_OPTIONS.keys()),
        index=0,
        label_visibility="collapsed"
    )
    st.session_state.current_model_slug = MODEL_OPTIONS[selected_label]

    st.markdown("---")
    st.markdown("<h3 class='rpg-title' style='font-size:1.1rem; color:#fce38a;'>💾 Campaign Vault</h3>", unsafe_allow_html=True)
    if world_exists and character_created:
        st.success("☁️ Cloud Sync Active (Full Lore & Game State)")
    elif not world_exists:
        st.info("🌐 Phase 1: World Architecting")
    else:
        st.info("🧙‍♂️ Phase 2: Character Creation")

    messages_list = campaign_data.get("messages", [])
    if messages_list and messages_list[-1].get("role") == "user":
        st.warning("⚠️ The GM has not responded yet.")
        if st.button("🎲 Retry GM Response", use_container_width=True):
            with st.spinner("Invoking Game Master..."):
                MAX_HISTORY_TURNS = 8
                recent_history = messages_list[-MAX_HISTORY_TURNS:]

                reminder_prompt = {
                    "role": "system",
                    "content": "REMINDER: Always write in 2nd person ('You...'). Maintain strict continuity with the current scene. Do not shift location or perspective abruptly."
                }
                
                api_messages = (
                    [{"role": "system", "content": system_instruction}] 
                    + [
                        {
                            "role": "assistant" if m.get("role") in ["assistant", "model"] else "user", 
                            "content": m.get("content") or m.get("text", "")
                        } 
                        for m in recent_history if isinstance(m, dict) and m.get("role") != "system"
                    ]
                    + [reminder_prompt]
                )
                try:
                    response = call_openrouter(api_messages, st.session_state.get("current_model_slug"))
                    reply = response.choices[0].message.content
                    campaign_data["messages"].append({"role": "assistant", "content": reply, "text": reply})
                    save_db_campaign(campaign_data)
                    st.rerun()
                except Exception as e:
                    st.error(f"Retry failed: {e}")

    with st.expander("⚙️ Master Save Management"):
        st.download_button(
            label="📥 Export Campaign JSON",
            data=json.dumps(campaign_data, indent=2),
            file_name="campaign_save.json",
            mime="application/json",
            use_container_width=True
        )

        uploaded_master = st.file_uploader("📤 Import Campaign JSON", type=["json"], key="upload_master")
        if uploaded_master is not None:
            uploaded_json = json.load(uploaded_master)
            st.session_state.campaign_data = uploaded_json
            save_db_campaign(uploaded_json)
            st.success("Campaign synced to database!")
            st.rerun()

        if st.button("🔄 Summarize History", use_container_width=True):
            with st.spinner("Summarizing chronicle..."):
                result = update_campaign_summary()
                if result:
                    st.session_state["dev_summary_preview"] = result
                    st.success("Summary updated!")

    if "dev_summary_preview" in st.session_state:
        with st.expander("🔍 Summary Preview", expanded=True):
            st.write(st.session_state["dev_summary_preview"])
            if st.button("❌ Close Preview", use_container_width=True):
                del st.session_state["dev_summary_preview"]
                st.rerun()

    st.markdown("---")
    if st.button("🗑️ Reset Campaign", use_container_width=True):
        delete_db_campaign()
        st.session_state.campaign_data = DEFAULT_CAMPAIGN.copy()
        st.rerun()

# --- INITIALIZE CAMPAIGN MEMORY ---

if not campaign_data.get("messages"):
    if not world_exists:
        opening_prompt = "Greetings, World Architect! I am ready to build my new campaign setting. Please present me with the world-building questions to design our setting!"
    else:
        opening_prompt = "Greetings! I am ready for character creation. Please ask me for my character's details!"

    opening_context = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": opening_prompt}
    ]
    
    try:
        response = call_openrouter(opening_context, st.session_state.get("current_model_slug"))
        opening_reply = response.choices[0].message.content
        campaign_data["messages"].append({"role": "assistant", "content": opening_reply, "text": opening_reply})
        save_db_campaign(campaign_data)
        st.rerun()
    except Exception as e:
        st.error(f"Failed to connect to Game Master AI: {e}")

# --- HERO CAMPAIGN BANNER ---

current_location = game_state.get("current_location", "Unknown Lands")

st.markdown(f"""
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
""", unsafe_allow_html=True)

# --- CHAT DISPLAY & EDIT/REWIND POP-OVERS ---

DISPLAY_LIMIT = 15
messages = campaign_data.get("messages", [])
total_messages = len(messages)

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
    text_to_display = msg.get("content") or msg.get("text", "")
    marker_class = "gm-message-marker" if role == "assistant" else "user-message-marker"
    
    with st.chat_message(role):
        st.markdown(f"<span class='{marker_class}' style='display:none;'></span>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([0.88, 0.12])
        with col1:
            st.markdown(text_to_display)
        with col2:
            if role == "user":
                with st.popover("⏮️ Rewind", use_container_width=True):
                    st.markdown("**Rewind To This Turn**")
                    st.caption("Revert campaign state and retry your action from here.")
                    if st.button("Confirm Rewind", key=f"btn_rewind_{idx}", type="primary"):
                        campaign_data["messages"] = campaign_data["messages"][:idx + 1]
                        save_db_campaign(campaign_data)
                        
                        MAX_HISTORY_TURNS = 8
                        recent_history = campaign_data["messages"][-MAX_HISTORY_TURNS:]
                        
                        reminder_prompt = {
                            "role": "system",
                            "content": "REMINDER: Always write in 2nd person ('You...'). Maintain strict continuity with the current scene."
                        }
                        
                        api_messages = (
                            [{"role": "system", "content": system_instruction}] 
                            + [
                                {
                                    "role": "assistant" if m.get("role") in ["assistant", "model"] else "user", 
                                    "content": m.get("content") or m.get("text", "")
                                } 
                                for m in recent_history if isinstance(m, dict) and m.get("role") != "system"
                            ]
                            + [reminder_prompt]
                        )
                        
                        try:
                            response = call_openrouter(api_messages, st.session_state.get("current_model_slug"))
                            reply = response.choices[0].message.content
                            campaign_data["messages"].append({"role": "assistant", "content": reply, "text": reply})
                            save_db_campaign(campaign_data)
                        except Exception as e:
                            st.error(f"API Error during rewind: {e}")
                        st.rerun()
            else:
                with st.popover("✏️ Edit GM", use_container_width=True):
                    st.markdown("**Edit GM Response**")
                    edited_gm_text = st.text_area("Narrative Text:", value=text_to_display, height=160, key=f"edit_gm_{idx}")
                    if st.button("Save Edit", key=f"save_edit_{idx}", type="primary"):
                        edited_text = process_and_strip_character_state(edited_gm_text, campaign_data)
                        campaign_data["messages"][idx]["content"] = edited_text
                        campaign_data["messages"][idx]["text"] = edited_text
                        save_db_campaign(campaign_data)
                        st.rerun()

# --- AUTO-SCROLL TO LATEST MESSAGE ---

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

# --- INTERACTIVE QUICK DICE ROLLER & ACTION CHIPS ---

with st.expander("🎲 Quick Dice Roller & Action Suggestions", expanded=False):
    col_d1, col_d2, col_d3, col_d4, col_d5, col_d6, col_mod = st.columns([1, 1, 1, 1, 1, 1, 2])
    
    rolled_sides = None
    if col_d1.button("d20", use_container_width=True): rolled_sides = 20
    if col_d2.button("d12", use_container_width=True): rolled_sides = 12
    if col_d3.button("d10", use_container_width=True): rolled_sides = 10
    if col_d4.button("d8", use_container_width=True): rolled_sides = 8
    if col_d5.button("d6", use_container_width=True): rolled_sides = 6
    if col_d6.button("d4", use_container_width=True): rolled_sides = 4
    
    with col_mod:
        stat_keys = ["None", "STR", "DEX", "CON", "INT", "WIS", "CHA"]
        chosen_stat = st.selectbox("Add Stat Bonus:", stat_keys, index=0, key="dice_mod_select")

    if rolled_sides:
        raw_roll = random.randint(1, rolled_sides)
        bonus_val = 0
        bonus_label = ""
        if chosen_stat != "None" and chosen_stat in stats:
            score = stats[chosen_stat]
            bonus_val = (score - 10) // 2
            sign = "+" if bonus_val >= 0 else ""
            bonus_label = f" {sign}{bonus_val} ({chosen_stat})"

        total_roll = raw_roll + bonus_val
        crit_msg = ""
        if rolled_sides == 20:
            if raw_roll == 20: crit_msg = "🔥 NATURAL 20! CRITICAL SUCCESS!"
            elif raw_roll == 1: crit_msg = "💀 NATURAL 1! CRITICAL FUMBLE!"

        roll_summary = f"🎲 Rolled d{rolled_sides}: {raw_roll}{bonus_label} = **{total_roll}** {crit_msg}"
        st.session_state["last_roll_text"] = roll_summary

    if "last_roll_text" in st.session_state:
        st.markdown(f"<div style='background:rgba(212,175,55,0.15); border:1px solid #d4af37; padding:8px 12px; border-radius:8px; margin:6px 0;'>{st.session_state['last_roll_text']}</div>", unsafe_allow_html=True)
        if st.button("📤 Send Roll Result to Game Master", key="send_roll_btn", type="primary"):
            st.session_state["queued_action"] = f"I roll a check: {st.session_state['last_roll_text']}"
            del st.session_state["last_roll_text"]
            st.rerun()

# Check for queued action from dice roll
queued_text = st.session_state.pop("queued_action", "")

# --- CHAT INPUT DOCK ---

with st.form(key="chat_form", clear_on_submit=True):
    col_text, col_btn = st.columns([0.88, 0.12])
    
    with col_text:
        user_input = st.text_area(
            "What do you do?", 
            value=queued_text,
            height=85, 
            key="user_action_input", 
            placeholder="Describe your actions, speech, or cast a spell... (e.g. 'I draw my blade and inspect the ancient runes.')",
            label_visibility="collapsed"
        )
    
    with col_btn:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        submit_action = st.form_submit_button("⚔️ Send", use_container_width=True)

if submit_action and user_input.strip():
    clean_user_input = str(user_input).strip()
    
    with st.chat_message("user"):
        st.write(clean_user_input)
    
    campaign_data["messages"].append({"role": "user", "content": clean_user_input, "text": clean_user_input})

    with st.chat_message("assistant"):
        with st.spinner("The Game Master is narrating..."):
            MAX_HISTORY_TURNS = 8
            recent_history = campaign_data["messages"][-MAX_HISTORY_TURNS:]
            
            reminder_prompt = {
                "role": "system",
                "content": "REMINDER: Always write in 2nd person ('You...'). Maintain strict continuity with the current scene. Do not shift location or perspective abruptly."
            }

            api_messages = (
                [{"role": "system", "content": system_instruction}] 
                + [
                    {
                        "role": "assistant" if m.get("role") in ["assistant", "model"] else "user", 
                        "content": m.get("content") or m.get("text", "")
                    } 
                    for m in recent_history if isinstance(m, dict) and m.get("role") != "system"
                ]
                + [reminder_prompt]
            )
            
            try:
                response = call_openrouter(api_messages, st.session_state.get("current_model_slug"))
                reply = response.choices[0].message.content
            except Exception as e:
                st.error(f"Failed to generate GM response: {e}")
                reply = None

    if reply:
        reply = process_and_strip_character_state(reply, campaign_data)
        
        if "<WORLD_CODEX>" in reply.upper():
            pattern_codex = r"<WORLD_CODEX>(.*?)</WORLD_CODEX>"
            match_codex = re.search(pattern_codex, reply, re.DOTALL | re.IGNORECASE)
            if match_codex:
                campaign_data["world_codex"] = match_codex.group(1).strip()
            reply = re.sub(pattern_codex, "", reply, flags=re.DOTALL | re.IGNORECASE).strip()

        campaign_data["messages"].append({"role": "assistant", "content": reply, "text": reply})
        
        if "turn_counter" not in st.session_state:
            st.session_state.turn_counter = 0

        st.session_state.turn_counter += 1

        if st.session_state.turn_counter % 10 == 0:
            with st.spinner("Recording chronicle into memory..."):
                update_campaign_summary()

        save_db_campaign(campaign_data)
        st.rerun()