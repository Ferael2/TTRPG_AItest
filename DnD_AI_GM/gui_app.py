import os
import json
import streamlit as st
from openai import OpenAI

SAVE_FILE = "campaign_save.json"
CODEX_FILE = "world_codex.txt"

st.set_page_config(page_title="AI D&D Game Master", page_icon="🎲", layout="wide")
st.title("🎲 AI Game Master Campaign (With Edit & Rewind)")

# --- HELPER FUNCTIONS ---

def load_campaign():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_state():
    if os.path.exists("campaign_state.json"):
        with open("campaign_state.json", "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                pass
    # STEP 1: Expanded default dictionary for D&D character attributes
    return {
        "player": {
            "name": "Hero",
            "species": "Unknown",
            "class": "Unknown",
            "level": 1,
            "hp": 10,
            "max_hp": 10,
            "stats": {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
            "proficiencies": [],
            "backstory": "",
            "inventory": []
        },
        "current_location": "Starting Location",
        "key_npcs": [],
        "active_quests": [],
        "summary": "The campaign has just begun."
    }

def save_campaign():
    if "messages" in st.session_state:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, indent=2)

# OpenRouter API Setup & Helper Function
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")

if not OPENROUTER_API_KEY:
    st.error("🔑 OpenRouter API Key missing! Please set OPENROUTER_API_KEY in Streamlit Cloud Secrets.")
    st.stop()

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
    current_state = load_state()
    existing_summary = current_state.get("summary", "The campaign has just begun.")
    
    messages_to_use = st.session_state.messages if "messages" in st.session_state and st.session_state.messages else load_campaign()

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

RECENT EVENTS TO INTEGRATE:
{formatted_recent}

INSTRUCTIONS:
Create an updated, concise summary of the campaign so far.
Keep the output under 250 words. Output ONLY the updated summary text.
"""}
    ]

    try:
        response = call_openrouter(summary_prompt, st.session_state.get("current_model_slug"))
        new_summary = response.choices[0].message.content.strip()
        
        current_state["summary"] = new_summary
        with open("campaign_state.json", "w", encoding="utf-8") as f:
            json.dump(current_state, f, indent=2)
            
        return new_summary
            
    except Exception as e:
        st.error(f"API Error during summary: {e}")
        return existing_summary

# Execute state load after functions are defined
game_state = load_state()

# --- STEP 2: DYNAMIC 3-PHASE SYSTEM PROMPTS ---

world_exists = os.path.exists(CODEX_FILE)
world_info = ""
if world_exists:
    with open(CODEX_FILE, "r", encoding="utf-8") as file:
        world_info = file.read()

character_created = game_state.get("player", {}).get("species") != "Unknown"

if not world_exists:
    # Phase 1: World Architect
    system_instruction = """
You are an expert TTRPG World Architect.
The player is starting a new campaign, but no world codex exists yet.

INSTRUCTIONS:
1. Ask the player 3-4 concise questions about Genre/Setting, Tone, Magic/Tech level, and Key Factions.
2. When the player answers, synthesize their choices inside <WORLD_CODEX>...</WORLD_CODEX>.
3. Right after closing </WORLD_CODEX>, welcome them to the setting and ask the Character Creation questions: Name, Species, Class, Stat Preferences, Proficiencies, Equipment, and Backstory hooks.
"""

elif not character_created:
    # Phase 2: Character Creator
    system_instruction = f"""
You are an expert D&D Character Creator.

WORLD SETTING:
{world_info}

CRITICAL INSTRUCTION:
Once the player provides their character details (Name, Species, Class, Stats, Backstory, Proficiencies, Inventory), you MUST generate a valid JSON block inside <CHARACTER_STATE>...</CHARACTER_STATE> tags as part of your response.

Required Format:
<CHARACTER_STATE>
{{
    "name": "Felix Lloyd",
    "species": "Vampire",
    "class": "Sorcerer",
    "level": 1,
    "hp": 8,
    "max_hp": 8,
    "stats": {{"STR": 8, "DEX": 14, "CON": 12, "INT": 12, "WIS": 10, "CHA": 16}},
    "proficiencies": ["Arcana", "Deception"],
    "backstory": "Character backstory summary...",
    "inventory": ["Staff", "Pouch"]
}}
</CHARACTER_STATE>

Do not skip this tag. Right below </CHARACTER_STATE>, begin the campaign's opening scene and present 2-3 logical options or ask "What do you do?".
"""

else:
    # Phase 3: Active Game Master
    campaign_summary = game_state.get("summary", "The campaign has just begun.")
    system_instruction = f"""
You are an expert TTRPG Game Master running a solo campaign for the player.

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
4. When the player attempts something risky or challenging, ask for D&D skill checks based on their stats and proficiencies.
5. LEVEL-UP & MILESTONE HANDLING:
   - When the player requests a level-up or reaches a milestone level (e.g., subclass choice at level 3, Feat/ASI at levels 4, 8, 12), ASK the player to make those specific choices BEFORE finalizing the level-up.
   - Once all choices (subclass, feat, spells, stat increases) are made by the player, output the complete updated <CHARACTER_STATE>...</CHARACTER_STATE> JSON block.
6. The player is allowed to romance NPCs.
7. Scenes with NSFW content are allowed.
8. Create believable scenarios for the characters to interact in.
9. End EVERY response with 2–3 logical options or ask "What do you do?".
"""

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("📊 Campaign State")
    st.subheader(f"📍 Location: {game_state.get('current_location', 'Unknown')}")
    
    # STEP 4: Enhanced Stats Grid in Sidebar
    with st.expander("🎒 Character & Stats", expanded=True):
        player_info = game_state.get("player", {})
        st.write(f"**Name:** {player_info.get('name', 'Hero')}")
        st.write(f"**Race/Class:** {player_info.get('species', 'Unknown')} {player_info.get('class', '')}")
        st.write(f"**HP:** {player_info.get('hp', 10)}/{player_info.get('max_hp', 10)}")
        
        stats = player_info.get("stats", {})
        if stats:
            cols = st.columns(3)
            stat_items = list(stats.items())
            for idx, (k, v) in enumerate(stat_items):
                cols[idx % 3].metric(label=k, value=v)
                
        st.write("**Inventory:**")
        for item in player_info.get("inventory", []):
            st.write(f"• {item}")

    st.markdown("---")
    st.header("🤖 AI Model Selection")
    
    selected_label = st.selectbox(
        "Choose Game Master AI Model:",
        options=list(MODEL_OPTIONS.keys()),
        index=0,
        help="Select your preferred AI model for narrative generation."
    )
    st.session_state.current_model_slug = MODEL_OPTIONS[selected_label]

    st.markdown("---")
    chat_exists = os.path.exists(SAVE_FILE)
    state_exists = os.path.exists("campaign_state.json")

    st.header("💾 Campaign File Status")
    if chat_exists and state_exists and world_exists and character_created:
        st.success("✅ World, Character & Saves active")
    elif not world_exists:
        st.info("🌐 Phase 1: World Creation Active")
    elif not character_created:
        st.info("🧙‍♂️ Phase 2: Character Creation Active")
    else:
        st.warning("⚠️ Save files incomplete")

    # Emergency Retry Button
    if "messages" in st.session_state and st.session_state.messages and st.session_state.messages[-1].get("role") == "user":
        st.warning("⚠️ The GM hasn't responded to your last action yet.")
        if st.button("🎲 Retry GM Response", use_container_width=True):
            with st.spinner("Retrying GM response..."):
                MAX_HISTORY_TURNS = 12
                recent_history = st.session_state.messages[-MAX_HISTORY_TURNS:]
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
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": reply,
                        "text": reply
                    })
                    save_campaign()
                    st.rerun()
                except Exception as e:
                    st.error(f"Retry failed: {e}")

    with st.expander("⚙️ Manage Saves (Upload / Download)", expanded=not (chat_exists and state_exists and world_exists)):
        st.subheader("📥 Downloads")
        if chat_exists:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                st.download_button(
                    label="Download Chat Log",
                    data=f.read(),
                    file_name="campaign_save.json",
                    mime="application/json",
                    use_container_width=True
                )

        if state_exists:
            with open("campaign_state.json", "r", encoding="utf-8") as f:
                st.download_button(
                    label="Download State File",
                    data=f.read(),
                    file_name="campaign_state.json",
                    mime="application/json",
                    use_container_width=True
                )

        if world_exists:
            with open(CODEX_FILE, "r", encoding="utf-8") as f:
                st.download_button(
                    label="Download World Codex",
                    data=f.read(),
                    file_name="world_codex.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        st.markdown("---")
        st.subheader("📤 Upload / Replace Saves")
        
        uploaded_history = st.file_uploader("Upload Chat Save", type=["json"], key="upload_hist")
        if uploaded_history is not None:
            with open(SAVE_FILE, "wb") as f:
                f.write(uploaded_history.getbuffer())
            st.session_state.messages = load_campaign()
            st.success("Chat history updated and loaded!")
            st.rerun()

        uploaded_state = st.file_uploader("Upload State Save", type=["json"], key="upload_state")
        if uploaded_state is not None:
            with open("campaign_state.json", "wb") as f:
                f.write(uploaded_state.getbuffer())
            st.success("Campaign state updated!")
            st.rerun()

        uploaded_codex = st.file_uploader("Upload World Codex", type=["txt"], key="upload_codex")
        if uploaded_codex is not None:
            with open(CODEX_FILE, "wb") as f:
                f.write(uploaded_codex.getbuffer())
            st.success("World Codex updated!")
            st.rerun()

        st.markdown("---")
        if st.button("🔄 Catch Up Summary", use_container_width=True):
            with st.spinner("Summarizing campaign history..."):
                result = update_campaign_summary()
                if result:
                    st.session_state["dev_summary_preview"] = result
                    st.success("Summary generated successfully!")
                else:
                    st.warning("Summary generation returned no result.")

    if "dev_summary_preview" in st.session_state:
        with st.expander("🔍 DEV PREVIEW: Summary Output", expanded=True):
            st.write(st.session_state["dev_summary_preview"])
            if st.button("❌ Clear Preview", use_container_width=True):
                del st.session_state["dev_summary_preview"]
                st.rerun()
        
    st.markdown("---")
    if st.button("🗑️ Restart campaign", use_container_width=True):
        for f in [SAVE_FILE, "campaign_state.json", CODEX_FILE]:
            if os.path.exists(f):
                os.remove(f)
        st.session_state.messages = []
        st.rerun()

# 4. Load Conversation Memory
if "messages" not in st.session_state:
    saved_history = load_campaign()
    if saved_history:
        st.session_state.messages = saved_history
    else:
        st.session_state.messages = []
        opening_prompt = "Hello! Let's start a new campaign. Please ask me the world-building questions to design our setting!" if not world_exists else "Start character creation!"
        
        opening_context = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": opening_prompt}
        ]
        
        response = call_openrouter(opening_context, st.session_state.get("current_model_slug"))
        opening_reply = response.choices[0].message.content
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": opening_reply, 
            "text": opening_reply
        })
        save_campaign()

# 5. Render History with Edit Capability
DISPLAY_LIMIT = 15
total_messages = len(st.session_state.messages)
show_all = st.checkbox("📜 Show Full Campaign History", value=False)
start_idx = 0 if show_all else max(0, total_messages - DISPLAY_LIMIT)

if not show_all and total_messages > DISPLAY_LIMIT:
    st.info(f"Showing last {DISPLAY_LIMIT} messages. Check 'Show Full Campaign History' above to view all {total_messages} turns.")

for idx in range(start_idx, total_messages):
    msg = st.session_state.messages[idx]
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
                        st.session_state.messages[idx]["content"] = new_text
                        st.session_state.messages[idx]["text"] = new_text
                        st.session_state.messages = st.session_state.messages[:idx + 1]
                        
                        api_messages = [{"role": "system", "content": system_instruction}] + [
                            {
                                "role": "assistant" if m.get("role") in ["assistant", "model"] else "user", 
                                "content": m.get("content") or m.get("text", "")
                            } 
                            for m in st.session_state.messages if isinstance(m, dict) and m.get("role") != "system"
                        ]
                        
                        try:
                            response = call_openrouter(api_messages, st.session_state.get("current_model_slug"))
                            reply = response.choices[0].message.content
                            st.session_state.messages.append({"role": "assistant", "content": reply, "text": reply})
                            save_campaign()
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
                        st.session_state.messages[idx]["content"] = edited_gm_text
                        st.session_state.messages[idx]["text"] = edited_gm_text
                        save_campaign()
                        st.rerun()

# --- STEP 3: USER INPUT PROCESSING WITH TAG PARSING ---

if user_input := st.chat_input("What do you do?"):
    with st.chat_message("user"):
        st.write(user_input)
    
    st.session_state.messages.append({
        "role": "user", 
        "content": user_input,
        "text": user_input
    })

    with st.chat_message("assistant"):
        with st.spinner("The Game Master is thinking..."):
            MAX_HISTORY_TURNS = 12
            recent_history = st.session_state.messages[-MAX_HISTORY_TURNS:]

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
        # STEP 3A: Parse World Codex Tag if present
        if "<WORLD_CODEX>" in reply and "</WORLD_CODEX>" in reply:
            codex_content = reply.split("<WORLD_CODEX>")[1].split("</WORLD_CODEX>")[0].strip()
            with open(CODEX_FILE, "w", encoding="utf-8") as f:
                f.write(codex_content)
            reply = reply.split("</WORLD_CODEX>")[1].strip()

        # STEP 3B: Parse Character State Tag if present
        if "<CHARACTER_STATE>" in reply.upper() and "</CHARACTER_STATE>" in reply.upper():
            try:
                # Extract content between tags regardless of letter casing
                lower_reply = reply.lower()
                start_idx = lower_reply.find("<character_state>") + len("<character_state>")
                end_idx = lower_reply.find("</character_state>")
                char_json_str = reply[start_idx:end_idx].strip()

                parsed_char = json.loads(char_json_str)
                current_state = load_state()
                current_state["player"] = parsed_char
                
                with open("campaign_state.json", "w", encoding="utf-8") as f:
                    json.dump(current_state, f, indent=2)
                    
            except Exception as e:
                st.error(f"Failed to parse character state JSON: {e}")
            
            # Clean reply text for chat display
            reply = reply[end_idx + len("</character_state>"):].strip()

        st.session_state.messages.append({
            "role": "assistant", 
            "content": reply,
            "text": reply
        })

        if "turn_counter" not in st.session_state:
            st.session_state.turn_counter = 0

        st.session_state.turn_counter += 1

        if st.session_state.turn_counter % 10 == 0:
            with st.spinner("Updating campaign memory summary..."):
                update_campaign_summary()

        save_campaign()
        st.rerun()