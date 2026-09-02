import os
import json
import streamlit as st
from openai import OpenAI

SAVE_FILE = "campaign_save.json"

st.set_page_config(page_title="AI D&D Game Master", page_icon="🎲", layout="wide")
st.title("🎲 AI Game Master Campaign (With Edit & Rewind)")

# 1. Read World Codex
world_info = ""
if os.path.exists("world_codex.txt"):
    with open("world_codex.txt", "r", encoding="utf-8") as file:
        world_info = file.read()

# --- HELPER FUNCTIONS (ORDER MATTERS) ---

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
    # Fallback default dictionary so .get() never crashes
    return {
        "player": {"name": "Hero", "hp": 10, "max_hp": 10, "inventory": []},
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
    """
    Tries the user-selected model first. 
    If it fails, automatically falls back through remaining free models.
    """
    # Build fallback queue starting with user's preferred model
    fallback_queue = []
    if selected_model_slug:
        fallback_queue.append(selected_model_slug)
    
    # Add remaining models to fallback queue
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
    """Summarizes recent context and updates campaign_state.json automatically."""
    current_state = load_state()
    existing_summary = current_state.get("summary", "The campaign has just begun.")
    
    # Grab messages from session state, or load directly from file if empty
    messages_to_use = []
    if "messages" in st.session_state and st.session_state.messages:
        messages_to_use = st.session_state.messages
    else:
        messages_to_use = load_campaign()

    if not messages_to_use:
        st.error("⚠️ No chat history found in memory or campaign_save.json!")
        return None

    # Grab the last 15 messages (or full history if shorter)
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
Focus strictly on:
1. Major story beats and plot developments.
2. Current status/condition of key NPCs (e.g., whether someone is injured, unconscious, or friendly).
3. Active objectives and key locations.

Keep the output under 250 words. Output ONLY the updated summary text.
"""}
    ]

    try:
        response = call_openrouter(summary_prompt, st.session_state.get("current_model_slug"))
        new_summary = response.choices[0].message.content.strip()
        
        # Save back to campaign_state.json
        current_state["summary"] = new_summary
        with open("campaign_state.json", "w", encoding="utf-8") as f:
            json.dump(current_state, f, indent=2)
            
        return new_summary
            
    except Exception as e:
        st.error(f"API Error during summary: {e}")
        return existing_summary  # Return existing summary instead of None on error

# Execute state load after functions are defined
game_state = load_state()

# --- SYSTEM INSTRUCTION (LOADED BEFORE SIDEBAR SO SIDEBAR BUTTONS CAN READ IT) ---
campaign_summary = game_state.get("summary", "The campaign has just begun.")

system_instruction = f"""
You are an expert TTRPG Game Master running a solo campaign for the player.

WORLD SETTING & LORE:
{world_info}

CAMPAIGN SUMMARY & RECENT EVENTS:
{campaign_summary}

CURRENT GAME STATE (PERSISTENT FACTS):
{json.dumps(game_state, indent=2)}

GAME RULES:
1. Speak in the 2nd person ("You enter...", "You see...").
2. Describe scenes with rich sensory details.
3. Refer strictly to CAMPAIGN SUMMARY for NPC statuses (e.g., check if an NPC is unconscious/hospitalized before having others talk about them).
4. Do not make major decisions or force actions for the player's character.
5. When the player attempts something difficult or risky, ask for a D&D skill check (e.g., [Roll Perception] or [Roll Stealth]).
6. Focus on character development over action and fighting (But fights and action can still happen but rarely).
7. The player is allowed to romance NPCs.
8. Scenes with NSFW content are allowed.
9. Create interesting and believable scenarios for the characters to interact in.
10. End EVERY response with 2–3 logical options or ask "What do you do?".
"""

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("📊 Campaign State")
    st.subheader(f"📍 Location: {game_state.get('current_location', 'Unknown')}")
    
    with st.expander("🎒 Inventory & Stats", expanded=True):
        player_info = game_state.get("player", {})
        st.write(f"**Name:** {player_info.get('name')}")
        st.write(f"**HP:** {player_info.get('hp')}/{player_info.get('max_hp')}")
        st.write("**Items:**")
        for item in player_info.get("inventory", []):
            st.write(f"• {item}")
            
    with st.expander("👥 Key NPCs"):
        for npc in game_state.get("key_npcs", []):
            st.write(f"• **{npc.get('name')}**: {npc.get('role')}")

    st.markdown("---")
    st.header("🤖 AI Model Selection")
    
    selected_label = st.selectbox(
        "Choose Game Master AI Model:",
        options=list(MODEL_OPTIONS.keys()),
        index=0,
        help="Select your preferred AI model for narrative generation. If your choice is offline, the app automatically fails over to the next available free model."
    )
    
    # Store the chosen OpenRouter slug in session state
    st.session_state.current_model_slug = MODEL_OPTIONS[selected_label]

    st.markdown("---")
    chat_exists = os.path.exists(SAVE_FILE)
    state_exists = os.path.exists("campaign_state.json")

    st.header("💾 Campaign File Status")
    if chat_exists and state_exists:
        st.success("✅ Campaign & State files active")
    elif chat_exists:
        st.info("ℹ️ Chat history active (Default state used)")
    else:
        st.warning("⚠️ No save files detected")

    # Emergency Retry Button if the AI fails to reply
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

    with st.expander("⚙️ Manage Saves (Upload / Download)", expanded=not (chat_exists and state_exists)):
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

        st.markdown("---")
        st.subheader("📤 Upload / Replace Saves")
        
        uploaded_history = st.file_uploader("Upload Chat Save", type=["json"], key="upload_hist")
        if uploaded_history is not None:
            with open(SAVE_FILE, "wb") as f:
                f.write(uploaded_history.getbuffer())
            st.success("Chat history updated!")
            st.rerun()

        uploaded_state = st.file_uploader("Upload State Save", type=["json"], key="upload_state")
        if uploaded_state is not None:
            with open("campaign_state.json", "wb") as f:
                f.write(uploaded_state.getbuffer())
            st.success("Campaign state updated!")
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

    # DEV PREVIEW (Inside sidebar, outside expander)
    if "dev_summary_preview" in st.session_state:
        with st.expander("🔍 DEV PREVIEW: Summary Output", expanded=True):
            st.write(st.session_state["dev_summary_preview"])
            if st.button("❌ Clear Preview", use_container_width=True):
                del st.session_state["dev_summary_preview"]
                st.rerun()
        
    st.markdown("---")
    if st.button("🗑️ Restart campaign"):
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
        if os.path.exists("campaign_state.json"):
            os.remove("campaign_state.json")
        st.session_state.messages = []
        st.rerun()

# 4. Load Conversation Memory
if "messages" not in st.session_state:
    saved_history = load_campaign()
    if saved_history:
        st.session_state.messages = saved_history
    else:
        st.session_state.messages = []
        
        opening_context = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": "Start the campaign! Ask me to introduce my character (Name, Class, Stats/Equipment) or jump straight into the opening scene."}
        ]
        
        response = call_openrouter(opening_context)
        opening_reply = response.choices[0].message.content
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": opening_reply, 
            "text": opening_reply
        })
        save_campaign()

# 5. Render History with Edit Capability (Optimized Display)
DISPLAY_LIMIT = 15  # Only render the last 15 messages by default

total_messages = len(st.session_state.messages)
show_all = st.checkbox("📜 Show Full Campaign History", value=False)

# Determine starting index for rendering
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
                    new_text = st.text_area(
                        "Rewrite action:", 
                        value=text_to_display, 
                        height=150, 
                        key=f"edit_{idx}"
                    )
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
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": reply,
                                "text": reply
                            })
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
                    edited_gm_text = st.text_area(
                        "Modify AI narrative:", 
                        value=text_to_display, 
                        height=150, 
                        key=f"edit_gm_{idx}"
                    )
                    if st.button("Save Edit", key=f"btn_gm_{idx}", use_container_width=True):
                        st.session_state.messages[idx]["content"] = edited_gm_text
                        st.session_state.messages[idx]["text"] = edited_gm_text
                        save_campaign()
                        st.rerun()

# 6. Normal Player Action Input
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

    # Only append if a valid reply was returned
    if reply:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": reply,
            "text": reply
        })

        # Track turn count and auto-summarize every 10 turns
        if "turn_counter" not in st.session_state:
            st.session_state.turn_counter = 0

        st.session_state.turn_counter += 1

        if st.session_state.turn_counter % 10 == 0:
            with st.spinner("Updating campaign memory summary..."):
                update_campaign_summary()

        save_campaign()
        st.rerun()