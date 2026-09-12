# styles.py
# Dark Fantasy CSS theme for the AI D&D Game Master app.
# Call inject_styles() once at the top of gui_app.py.

import streamlit as st

DARK_FANTASY_CSS = """
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
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 8px;
}

.char-name-text {
    font-family: 'Cinzel', serif;
    font-size: 1.25rem;
    font-weight: 800;
    color: #fce38a;
    line-height: 1.2;
    text-shadow: 0 2px 8px rgba(212, 175, 55, 0.3);
}

.char-level-badge {
    width: 44px;
    height: 44px;
    min-width: 44px;
    min-height: 44px;
    border-radius: 50%;
    border: 2px solid #d4af37;
    background: radial-gradient(circle at center, rgba(212, 175, 55, 0.28) 0%, #0e1524 85%);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    box-shadow: 0 0 10px rgba(212, 175, 55, 0.35);
    flex-shrink: 0;
    box-sizing: border-box;
    padding: 0;
    margin: 0;
}

.char-level-label {
    font-size: 0.6rem;
    font-weight: 700;
    color: #f7d774;
    text-transform: uppercase;
    line-height: 1;
    margin: 0;
    padding: 0;
    display: block;
    text-align: center;
}

.char-level-num {
    font-family: 'Cinzel', serif;
    font-size: 1.15rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1;
    margin: 2px 0 0 0;
    padding: 0;
    display: block;
    text-align: center;
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

/* Vertical Inventory & Spell Lists */
.inv-vertical-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    width: 100%;
    margin-top: 4px;
}

.inv-item-row {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(212, 175, 55, 0.2);
    border-left: 3px solid #d4af37;
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 0.85rem;
    color: #f1f5f9;
    box-sizing: border-box;
    width: 100%;
}

.inv-item-bullet {
    font-size: 0.95rem;
    flex-shrink: 0;
}

.inv-item-name {
    flex: 1;
    font-weight: 500;
    word-break: break-word;
}

.spell-item-row {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-left: 3px solid #8b5cf6;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 0.83rem;
    color: #e2e8f0;
    box-sizing: border-box;
    width: 100%;
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
"""


def inject_styles():
    """Injects the Dark Fantasy CSS theme into the Streamlit app.

    Call once near the top of gui_app.py, after st.set_page_config().
    """
    st.markdown(DARK_FANTASY_CSS, unsafe_allow_html=True)
