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

/* Responsive base: prevent text from clipping/overflowing on narrow screens */
*, *::before, *::after {
    box-sizing: border-box;
}

body, p, span, div, h1, h2, h3, h4, h5, h6, label,
.char-name-text, .hero-banner-title, .hero-banner-subtitle,
.auth-portal-title, .auth-portal-subtitle, .user-profile-name,
.inv-item-name, .spell-item-row, .tag-pill, .hp-meta, .s-name, .s-val {
    overflow-wrap: break-word !important;
    word-wrap: break-word !important;
    word-break: break-word !important;
    min-width: 0 !important;
}

/* Flex/grid children collapse to their content's intrinsic width by default,
   which silently clips or overflows sibling text on phones/small laptops.
   Forcing min-width: 0 lets them shrink and wrap normally instead. */
.char-name-badge, .char-name-badge > *,
.vitals-row, .vitals-row > *,
.hp-meta, .hp-meta > *,
.hero-campaign-banner, .hero-campaign-banner > *,
.hero-banner-badges, .hero-banner-badges > *,
.inv-item-row, .inv-item-row > *,
.spell-item-row, .spell-item-row > *,
.user-profile-card, .user-profile-card > *,
.user-profile-info, .user-profile-info > *,
.quick-action-bar, .quick-action-bar > * {
    min-width: 0;
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

/* --- AUTHENTICATION PORTAL & USER BADGES --- */
.auth-portal-container {
    max-width: 480px;
    margin: 2rem auto;
    padding: 0 1rem;
}

.auth-portal-card {
    background: linear-gradient(160deg, #131b2e 0%, #0c101a 100%);
    border: 1px solid rgba(212, 175, 55, 0.4);
    border-radius: 16px;
    padding: 28px 24px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.7), 0 0 25px rgba(212, 175, 55, 0.12);
    position: relative;
    overflow: hidden;
}

.auth-portal-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, #d4af37, #fce38a, #d4af37, transparent);
}

.auth-portal-header {
    text-align: center;
    margin-bottom: 24px;
}

.auth-portal-emblem {
    font-size: 3rem;
    margin-bottom: 8px;
    filter: drop-shadow(0 0 12px rgba(212, 175, 55, 0.4));
    display: inline-block;
}

.auth-portal-title {
    font-family: 'Cinzel', serif;
    font-size: 1.7rem;
    font-weight: 800;
    color: #fce38a;
    letter-spacing: 0.08em;
    margin: 0;
    text-shadow: 0 2px 10px rgba(212, 175, 55, 0.35);
}

.auth-portal-subtitle {
    font-size: 0.88rem;
    color: #94a3b8;
    margin-top: 6px;
    font-style: italic;
}

.user-profile-card {
    background: linear-gradient(135deg, #141c2e, #0e1422);
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.user-profile-info {
    display: flex;
    flex-direction: column;
}

.user-profile-name {
    font-family: 'Cinzel', serif;
    font-weight: 700;
    font-size: 1rem;
    color: #fce38a;
}

.user-profile-role {
    font-size: 0.72rem;
    color: #cbd5e1;
    font-weight: 500;
}

.admin-badge {
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    color: #f8fafc;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border: 1px solid rgba(167, 139, 250, 0.4);
}

.player-badge {
    background: linear-gradient(135deg, #059669, #047857);
    color: #f8fafc;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border: 1px solid rgba(52, 211, 153, 0.4);
}

/* --- RESPONSIVE ADJUSTMENTS --- */
/* Narrow laptop / tablet windows: tighten spacing, keep everything on-screen */
@media (max-width: 900px) {
    .main .block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .hero-banner-title {
        font-size: 1.3rem;
    }

    .auth-portal-title {
        font-size: 1.4rem;
        letter-spacing: 0.05em;
    }
}

/* Phone-width screens: shrink headers/badges and stack flex rows so labels
   have room to wrap instead of being cut off */
@media (max-width: 600px) {
    .main .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        padding-top: 1rem !important;
    }

    .hero-campaign-banner {
        flex-direction: column;
        align-items: flex-start;
        padding: 12px 14px;
    }

    .hero-banner-title {
        font-size: 1.15rem;
        letter-spacing: 0.02em;
    }

    .hero-banner-subtitle {
        font-size: 0.78rem;
    }

    .auth-portal-card {
        padding: 20px 16px;
        overflow: visible;
    }

    .auth-portal-title {
        font-size: 1.2rem;
        letter-spacing: 0.03em;
    }

    .auth-portal-subtitle {
        font-size: 0.8rem;
    }

    .char-name-badge {
        flex-wrap: wrap;
    }

    .char-name-text {
        font-size: 1.05rem;
    }

    .vitals-row {
        flex-wrap: wrap;
    }

    .stats-grid {
        grid-template-columns: repeat(3, 1fr);
        gap: 6px;
    }

    .stat-box {
        padding: 5px 2px;
    }

    .stat-box .s-name {
        font-size: 0.58rem;
    }

    .user-profile-card {
        flex-wrap: wrap;
    }

    .quick-action-bar {
        padding: 6px 8px;
        gap: 6px;
    }
}

/* --- RESPONSIVE HERO OVERRIDES (mobile-friendly) --- */

/* Centered wrapper with a sane max width so large headings don't become very tall narrow columns */
.responsive-wrapper {
  margin: 0 auto;
  padding: 0 1rem;
  max-width: 920px; /* desktop cap; reduces extremely long narrow columns on mobile */
  box-sizing: border-box;
}

/* Cap the hero banner width so it never becomes a skinny column */
.hero-campaign-banner {
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
  box-sizing: border-box;
}

/* Use responsive font sizing so the title scales but never explodes on phones. Also avoid forced word-breaks. */
.hero-banner-title {
  font-family: 'Cinzel', serif;
  font-weight: 800;
  color: #f7d774;
  margin: 0;
  line-height: 1.02;
  letter-spacing: 0.03em;
  text-shadow: 0 2px 10px rgba(212, 175, 55, 0.25);
  font-size: clamp(20px, 6.6vw, 40px); /* min 20px, scales with viewport, max 40px */
  word-break: normal !important;
  white-space: pre-wrap !important; /* keep intended line breaks but allow wrapping */
}

/* Slightly larger subtitle on phones but constrained */
.hero-banner-subtitle {
  font-size: clamp(12px, 2.6vw, 16px);
  margin-top: 6px;
  color: #94a3b8;
}

/* Ensure badges stay to the right on wide screens but wrap cleanly on narrow screens */
.hero-banner-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* Mobile-specific tweak: stack banner content vertically and align center for small widths */
@media (max-width: 600px) {
  .hero-campaign-banner {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 12px 10px;
  }

  .hero-banner-title {
    text-align: center;
    font-size: clamp(18px, 9vw, 32px);
  }

  .hero-banner-subtitle {
    text-align: center;
    font-size: 13px;
  }

  .main .block-container {
    padding-left: 0.6rem !important;
    padding-right: 0.6rem !important;
  }
}
</style>
"""


def inject_styles():
    """Injects the Dark Fantasy CSS theme into the Streamlit app.

    Call once near the top of gui_app.py, after st.set_page_config().
    """
    st.markdown(DARK_FANTASY_CSS, unsafe_allow_html=True)

