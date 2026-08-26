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

# Helper Functions
def save_campaign():
    if "messages" in st.session_state:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, indent=2)

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
        "active_quests": []
    }

game_state = load_state()

# Sidebar Controls
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
    st.header("💾 Save & Load Campaign")
    # 1. DOWNLOAD CURRENT SAVES
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Download Chat Save",
                data=f.read(),
                file_name="campaign_save.json",
                mime="application/json",
                use_container_width=True
            )

    if os.path.exists("campaign_state.json"):
        with open("campaign_state.json", "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Download State Save",
                data=f.read(),
                file_name="campaign_state.json",
                mime="application/json",
                use_container_width=True
            )

    # 2. UPLOAD SAVES FROM DEVICE
    uploaded_history = st.file_uploader("Upload Chat Save (campaign_save.json)", type=["json"], key="upload_hist")
    if uploaded_history is not None:
        with open(SAVE_FILE, "wb") as f:
            f.write(uploaded_history.getbuffer())
        st.success("Chat history loaded!")
        st.rerun()

    uploaded_state = st.file_uploader("Upload State Save (campaign_state.json)", type=["json"], key="upload_state")
    if uploaded_state is not None:
        with open("campaign_state.json", "wb") as f:
            f.write(uploaded_state.getbuffer())
        st.success("Campaign state loaded!")
        st.rerun()

    st.markdown("---")
    if st.button("🗑️ Delete Save & Restart"):
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
        st.session_state.messages = []
        st.rerun()

# 2. System Instructions

system_instruction = f"""
You are an expert TTRPG Game Master running a solo campaign for the player.

WORLD SETTING & LORE:
{world_info}

CURRENT GAME STATE (PERSISTENT FACTS):
{json.dumps(game_state, indent=2)}

GAME RULES:
1. Speak in the 2nd person ("You enter...", "You see...").
2. Describe scenes with rich sensory details.
3. Do not make major decisions or force actions for the player's character.
4. When the player attempts something difficult or risky, ask for a D&D skill check (e.g., [Roll Perception] or [Roll Stealth]).
5. Focus on character development over action and fighting (But fights and action can still happen but rarely).
6. The player is allowed to romance NPCs.
7. Create interesting and believable scenarios for the characters to interact in.
8. End EVERY response with 2–3 logical options or ask "What do you do?".
"""

# 3. Setup OpenRouter API Client
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]

if "client" not in st.session_state:
    st.session_state.client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

FREE_MODELS = [
    "openrouter/auto",
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-20b:free"
]

def call_openrouter(messages):
    """Loops through active OpenRouter models automatically to prevent errors."""
    last_error = None
    for model_name in FREE_MODELS:
        try:
            return st.session_state.client.chat.completions.create(
                model=model_name,
                messages=messages
            )
        except Exception as e:
            last_error = e
            continue
    raise last_error

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

# 5. Render History with Edit Capability
for idx, msg in enumerate(st.session_state.messages):
    if msg.get("role") == "system":
        continue
    
    raw_role = msg.get("role", "user")
    role = "assistant" if raw_role in ["assistant", "model"] else "user"
    text_to_display = msg.get("content") or msg.get("text", "")
    
    with st.chat_message(role):
        
        if role == "user":
            col1, col2 = st.columns([0.85, 0.15])  # Slightly wider action column for the button
            with col1:
                st.write(text_to_display)
            with col2:
                # use_container_width makes the popover expand cleanly
                with st.popover("✏️ Edit", use_container_width=True):
                    st.markdown("**Edit & Rewind Action**")
                    
                    # Using text_area makes the box wider and multi-line for long responses
                    new_text = st.text_area(
                        "Rewrite action:", 
                        value=text_to_display, 
                        height=150, 
                        key=f"edit_{idx}"
                    )
                    
                    if st.button("Save & Rewind", key=f"btn_{idx}", use_container_width=True):
                        # Update prompt & trim out future turns
                        st.session_state.messages[idx]["content"] = new_text
                        st.session_state.messages[idx]["text"] = new_text
                        st.session_state.messages = st.session_state.messages[:idx + 1]
                        
                        # Regenerate GM outcome for edited prompt
                        api_messages = [{"role": "system", "content": system_instruction}] + [
                            {
                                "role": "assistant" if m.get("role") in ["assistant", "model"] else "user", 
                                "content": m.get("content") or m.get("text", "")
                            } 
                            for m in st.session_state.messages if m.get("role") != "system"
                        ]
                        
                        response = call_openrouter(api_messages)
                        reply = response.choices[0].message.content
                        
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": reply,
                            "text": reply
                        })
                        
                        save_campaign()
                        st.rerun()
        else:
            st.write(text_to_display)

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
            # Limit API payload to System Prompt + Last 12 messages only
            MAX_HISTORY_TURNS = 12
            recent_history = st.session_state.messages[-MAX_HISTORY_TURNS:]

            api_messages = [{"role": "system", "content": system_instruction}] + [
                {
                    "role": "assistant" if m.get("role") in ["assistant", "model"] else "user", 
                    "content": m.get("content") or m.get("text", "")
                } 
                for m in recent_history if m.get("role") != "system"
            ]
            
            response = call_openrouter(api_messages)
            reply = response.choices[0].message.content
            st.write(reply)

    st.session_state.messages.append({
        "role": "assistant", 
        "content": reply,
        "text": reply
    })
    
    save_campaign()
    st.rerun()