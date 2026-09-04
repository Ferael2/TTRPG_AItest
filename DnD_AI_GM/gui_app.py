import json
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
from supabase import create_client, Client

st.set_page_config(page_title="AI D&D Game Master", page_icon="🎲", layout="wide")
st.title("🎲 AI Game Master Campaign (Cloud Saved)")

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

MODEL_OPTIONS = {
    "🌐 OpenRouter Auto (Best Available)": "openrouter/free",
    "🧠 Nemotron 120B (High Intelligence & Long Context)": "nvidia/nemotron-3-super-120b-a12b:free",
    "🎨 Gemma 31B (Rich Narrative & Storytelling)": "google/gemma-4-31b-it:free",
    "⚡ GPT-OSS 120B (Fast & Balanced)": "openai/gpt-oss-120b:free"
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
            "ac": 10,  # <-- Added default Armor Class
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
        "current_location": "Starting Location",
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
                messages=messages
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
2. Describe scenes with rich sensory details.
3. Refer strictly to CAMPAIGN SUMMARY for NPC statuses.
4. When the player attempts something risky, ask for D&D skill checks based on their stats and proficiencies.
5. LEVEL-UP, MULTICLASSING & SPELL SELECTION:
   - When leveling up, gaining a spellcasting subclass (e.g., Arcane Trickster, Eldritch Knight), or multiclassing into a magic class, ASK the player to select their new allowed spells/cantrips BEFORE finalizing the level-up.
   - Once all choices are made, output an updated <CHARACTER_STATE>...</CHARACTER_STATE> JSON block.
6. ARMOR CLASS (AC) & EQUIPMENT TRACKING:
   - Calculate and update "ac" inside <CHARACTER_STATE> whenever the player equips, dons, doffs, or acquires new armor, a shield, or magical equipment, or when their Dexterity modifier changes.
7. GM-DRIVEN SPELL SLOT MANAGEMENT:
   - When the player casts a leveled spell, deduct 1 slot from the corresponding slot level inside <CHARACTER_STATE> (e.g., reducing "level_1" "current" from 2 to 1).
   - When the player takes a Long Rest (or sleeps/rests for 8 hours), fully restore all "current" spell slots back to their "max" values inside an updated <CHARACTER_STATE> block.
8. The player is allowed to romance NPCs.
9. Scenes with NSFW content are allowed.
10. End EVERY response with 2–3 logical options or ask "What do you do?".
"""

# --- SIDEBAR CONTROLS ---

with st.sidebar:
    st.header("📊 Campaign State")
    st.subheader(f"📍 Location: {game_state.get('current_location', 'Unknown')}")
    
    with st.expander("🎒 Character & Stats", expanded=True):
        player_info = game_state.get("player", {})
        st.write(f"**Name:** {player_info.get('name', 'Hero')}")
        st.write(f"**Race/Class:** {player_info.get('species', 'Unknown')} {player_info.get('class', '')}")
        
        # Displays HP and AC side by side
        col1, col2 = st.columns(2)
        col1.write(f"**HP:** {player_info.get('hp', 10)}/{player_info.get('max_hp', 10)}")
        col2.write(f"**AC:** {player_info.get('ac', 10)}")
        
        stats = player_info.get("stats", {})
        if stats:
            cols = st.columns(3)
            for idx, (k, v) in enumerate(stats.items()):
                cols[idx % 3].metric(label=k, value=v)
                
        st.write("**Inventory:**")
        for item in player_info.get("inventory", []):
            st.write(f"• {item}")

    with st.expander("✨ Spells & Spell Slots", expanded=False):
        player_info = game_state.get("player", {})
        spell_data = player_info.get("spellcasting", {})
        
        cantrips = spell_data.get("cantrips", [])
        spells = spell_data.get("prepared_spells", [])
        slots = spell_data.get("spell_slots", {})

        if not cantrips and not spells and not slots:
            st.info("No spellcasting capabilities active.")
        else:
            if slots:
                st.write("**Spell Slots:**")
                for slot_lvl, slot_info in slots.items():
                    lvl_name = slot_lvl.replace("_", " ").title()
                    cur = slot_info.get("current", 0)
                    mx = slot_info.get("max", 0)
                    st.write(f"• **{lvl_name}:** {cur}/{mx} remaining")
                st.markdown("---")

            if cantrips:
                st.write("**Cantrips (At-Will):**")
                for c in cantrips:
                    st.write(f"• {c}")

            if spells:
                st.write("**Prepared / Known Spells:**")
                for s in spells:
                    st.write(f"• {s}")

    st.markdown("---")
    st.header("🤖 AI Model Selection")
    selected_label = st.selectbox(
        "Choose Game Master AI Model:",
        options=list(MODEL_OPTIONS.keys()),
        index=0
    )
    st.session_state.current_model_slug = MODEL_OPTIONS[selected_label]

    st.markdown("---")
    st.header("💾 Cloud Save Status")
    if world_exists and character_created:
        st.success("☁️ Cloud Save Active (World, Character & Chat)")
    elif not world_exists:
        st.info("🌐 Phase 1: World Creation Active")
    else:
        st.info("🧙‍♂️ Phase 2: Character Creation Active")

    # RESTORED: Emergency Retry Button
    messages_list = campaign_data.get("messages", [])
    if messages_list and messages_list[-1].get("role") == "user":
        st.warning("⚠️ The GM hasn't responded to your last action yet.")
        if st.button("🎲 Retry GM Response", use_container_width=True):
            with st.spinner("Retrying GM response..."):
                MAX_HISTORY_TURNS = 12
                recent_history = messages_list[-MAX_HISTORY_TURNS:]
                api_messages = [{"role": "system", "content": system_instruction}] + [
                    {
                        "role": "assistant" if m.get("role") in ["assistant", "model"] else "user", 
                        "content": m.get("content") or m.get("text", "")
                    } 
                    for m in recent_history if isinstance(m, dict) and m.get("role") != "system"
                ]
                try:
                    response = call_openrouter(api_messages, st.session_state.get("current_model_slug"))
                    reply = response.choices[0].message.content
                    campaign_data["messages"].append({"role": "assistant", "content": reply, "text": reply})
                    save_db_campaign(campaign_data)
                    st.rerun()
                except Exception as e:
                    st.error(f"Retry failed: {e}")

    with st.expander("⚙️ Manage Master Save (JSON Import/Export)"):
        st.subheader("📥 Export Campaign")
        st.download_button(
            label="Download Master Save JSON",
            data=json.dumps(campaign_data, indent=2),
            file_name="master_campaign_save.json",
            mime="application/json",
            use_container_width=True
        )

        st.markdown("---")
        st.subheader("📤 Import Campaign")
        uploaded_master = st.file_uploader("Upload Master Save JSON", type=["json"], key="upload_master")
        if uploaded_master is not None:
            uploaded_json = json.load(uploaded_master)
            st.session_state.campaign_data = uploaded_json
            save_db_campaign(uploaded_json)
            st.success("Master campaign imported and synced to Cloud Database!")
            st.rerun()

        st.markdown("---")
        # RESTORED: Catch Up Summary Button
        if st.button("🔄 Catch Up Summary", use_container_width=True):
            with st.spinner("Summarizing campaign history..."):
                result = update_campaign_summary()
                if result:
                    st.session_state["dev_summary_preview"] = result
                    st.success("Summary generated successfully!")

    if "dev_summary_preview" in st.session_state:
        with st.expander("🔍 DEV PREVIEW: Summary Output", expanded=True):
            st.write(st.session_state["dev_summary_preview"])
            if st.button("❌ Clear Preview", use_container_width=True):
                del st.session_state["dev_summary_preview"]
                st.rerun()

    st.markdown("---")
    if st.button("🗑️ Restart campaign", use_container_width=True):
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
    
    response = call_openrouter(opening_context, st.session_state.get("current_model_slug"))
    opening_reply = response.choices[0].message.content
    
    campaign_data["messages"].append({"role": "assistant", "content": opening_reply, "text": opening_reply})
    save_db_campaign(campaign_data)
    st.rerun()

# --- RESTORED: CHAT DISPLAY & EDIT/REWIND POP-OVERS ---

DISPLAY_LIMIT = 15
messages = campaign_data.get("messages", [])
total_messages = len(messages)
show_all = st.checkbox("📜 Show Full Campaign History", value=False)
start_idx = 0 if show_all else max(0, total_messages - DISPLAY_LIMIT)

for idx in range(start_idx, total_messages):
    msg = messages[idx]
    if not isinstance(msg, dict) or msg.get("role") == "system":
        continue
    
    raw_role = msg.get("role", "user")
    role = "assistant" if raw_role in ["assistant", "model"] else "user"
    text_to_display = msg.get("content") or msg.get("text", "")
    
    with st.chat_message(role):
        if role == "user":
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.write(text_to_display)
            with col2:
                with st.popover("✏️ Edit", use_container_width=True):
                    st.markdown("**Rewind Action**")
                    new_text = st.text_area("Rewrite action:", value=text_to_display, height=150, key=f"edit_{idx}")
                    if st.button("Save & Rewind", key=f"btn_{idx}", use_container_width=True):
                        campaign_data["messages"][idx]["content"] = new_text
                        campaign_data["messages"][idx]["text"] = new_text
                        campaign_data["messages"] = campaign_data["messages"][:idx + 1]
                        
                        api_messages = [{"role": "system", "content": system_instruction}] + [
                            {
                                "role": "assistant" if m.get("role") in ["assistant", "model"] else "user", 
                                "content": m.get("content") or m.get("text", "")
                            } 
                            for m in campaign_data["messages"] if isinstance(m, dict) and m.get("role") != "system"
                        ]
                        
                        try:
                            response = call_openrouter(api_messages, st.session_state.get("current_model_slug"))
                            reply = response.choices[0].message.content
                            campaign_data["messages"].append({"role": "assistant", "content": reply, "text": reply})
                            save_db_campaign(campaign_data)
                        except Exception as e:
                            st.error(f"API Error during rewind: {e}")
                        st.rerun()
        else:
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.write(text_to_display)
            with col2:
                with st.popover("✏️ Edit GM", use_container_width=True):
                    st.markdown("**Edit GM Response**")
                    edited_gm_text = st.text_area("Modify AI narrative:", value=text_to_display, height=150, key=f"edit_gm_{idx}")
                    if st.button("Save Edit", key=f"btn_gm_{idx}", use_container_width=True):
                        # Parse and update character state if tags are present
                        if "<CHARACTER_STATE>" in edited_gm_text.upper() and "</CHARACTER_STATE>" in edited_gm_text.upper():
                            try:
                                lower_txt = edited_gm_text.lower()
                                s_idx = lower_txt.find("<character_state>") + len("<character_state>")
                                e_idx = lower_txt.find("</character_state>")
                                char_json_str = edited_gm_text[s_idx:e_idx].strip()
                                campaign_data["campaign_state"]["player"] = json.loads(char_json_str)
                                edited_gm_text = edited_gm_text[e_idx + len("</character_state>"):].strip()
                            except Exception as e:
                                st.error(f"Failed to parse character JSON in edit: {e}")

                        campaign_data["messages"][idx]["content"] = edited_gm_text
                        campaign_data["messages"][idx]["text"] = edited_gm_text
                        save_db_campaign(campaign_data)
                        st.rerun()

# --- ACTION INPUT PROCESSING (HEIGHT & CAPTION ADJUSTED) ---

st.markdown("""
    <style>
    /* Scope column styling strictly to the form inside the main app body */
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: flex-end !important;
        gap: 8px !important;
    }

    /* Column 1 (Text Area) inside Form */
    div[data-testid="stForm"] div[data-testid="column"]:nth-of-type(1) {
        flex: 1 1 auto !important;
        width: 85% !important;
        min-width: 0 !important;
    }

    /* Column 2 (Submit Button) inside Form */
    div[data-testid="stForm"] div[data-testid="column"]:nth-of-type(2) {
        flex: 0 0 48px !important;
        width: 48px !important;
        min-width: 48px !important;
    }

    /* 1. INCREASE TEXT AREA HEIGHT */
    div[data-testid="stForm"] div[data-testid="stTextArea"] textarea {
        border-radius: 10px !important;
        min-height: 90px !important; /* Adjust height here (e.g., 90px - 120px) */
        resize: vertical !important;  /* Allows manual dragging if desired */
    }

    /* 2. REMOVE "Press Ctrl+Enter to submit form" CAPTION */
    div[data-testid="stForm"] div[data-testid="stTextArea"] [data-testid="InputInstructions"] {
        display: none !important;
    }

    /* Green arrow submit button styling */
    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] > button {
        width: 48px !important;
        height: 48px !important;
        min-height: 48px !important;
        border-radius: 10px !important;
        padding: 0 !important;
        margin: 0 !important;
        background-color: transparent !important;
        border: 1px solid #00c853 !important;
        color: #00c853 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 18px !important;
    }

    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #00c853 !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)
with st.form(key="chat_form", clear_on_submit=True):
    col_text, col_btn = st.columns([0.88, 0.12])
    
    with col_text:
        user_input = st.text_area(
            "What do you do?", 
            height=90, 
            key="user_action_input", 
            placeholder="Send a message...",
            label_visibility="collapsed"
        )
    
    with col_btn:
        submit_action = st.form_submit_button("➔")

if submit_action and user_input.strip():
    clean_user_input = str(user_input).strip()
    
    with st.chat_message("user"):
        st.write(clean_user_input)
    
    campaign_data["messages"].append({"role": "user", "content": clean_user_input, "text": clean_user_input})

    with st.chat_message("assistant"):
        with st.spinner("The Game Master is thinking..."):
            recent_history = campaign_data["messages"][-12:]
            api_messages = [{"role": "system", "content": system_instruction}] + [
                {
                    "role": "assistant" if m.get("role") in ["assistant", "model"] else "user", 
                    "content": m.get("content") or m.get("text", "")
                } 
                for m in recent_history if isinstance(m, dict) and m.get("role") != "system"
            ]
            
            try:
                response = call_openrouter(api_messages, st.session_state.get("current_model_slug"))
                reply = response.choices[0].message.content
            except Exception as e:
                st.error(f"Failed to generate response: {e}")
                reply = None

    if reply:
        # Parse World Codex Tag
        if "<WORLD_CODEX>" in reply.upper() and "</WORLD_CODEX>" in reply.upper():
            lower_reply = reply.lower()
            s_idx = lower_reply.find("<world_codex>") + len("<world_codex>")
            e_idx = lower_reply.find("</world_codex>")
            campaign_data["world_codex"] = reply[s_idx:e_idx].strip()
            reply = reply[e_idx + len("</world_codex>"):].strip()

        # Parse Character State Tag
        if "<CHARACTER_STATE>" in reply.upper() and "</CHARACTER_STATE>" in reply.upper():
            try:
                lower_reply = reply.lower()
                s_idx = lower_reply.find("<character_state>") + len("<character_state>")
                e_idx = lower_reply.find("</character_state>")
                char_json_str = reply[s_idx:e_idx].strip()
                
                # Strip markdown code block formatting if present
                if char_json_str.startswith("```"):
                    char_json_str = char_json_str.split("```")[1]
                    if char_json_str.startswith("json"):
                        char_json_str = char_json_str[4:]
                
                campaign_data["campaign_state"]["player"] = json.loads(char_json_str.strip())
            except Exception as e:
                st.error(f"Failed to parse character state JSON: {e}")
            reply = reply[e_idx + len("</character_state>"):].strip()

        campaign_data["messages"].append({"role": "assistant", "content": reply, "text": reply})
        
        # Turn Counter & Auto-Summarize Every 10 Turns
        if "turn_counter" not in st.session_state:
            st.session_state.turn_counter = 0

        st.session_state.turn_counter += 1

        if st.session_state.turn_counter % 10 == 0:
            with st.spinner("Updating campaign memory summary..."):
                update_campaign_summary()

        save_db_campaign(campaign_data)
        st.rerun()