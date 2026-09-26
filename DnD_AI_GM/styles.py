import streamlit as st


def inject_styles():
    """Apply the shared fantasy theme and responsive auth layout."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap');

        :root {
            --realm-ink: #0c0e13;
            --realm-panel: #141821;
            --realm-panel-raised: #1b202a;
            --realm-gold: #d4af37;
            --realm-gold-pale: #fce38a;
            --realm-muted: #a7a9b1;
        }

        [data-testid="stSidebar"] .character-sheet-card {
            box-sizing: border-box;
            margin: 0.4rem 0 0.75rem;
            padding: 0.75rem;
            border: 1px solid rgba(212, 175, 55, 0.25);
            border-radius: 7px;
            background: linear-gradient(145deg, rgba(27, 32, 42, 0.95), rgba(20, 24, 33, 0.95));
        }

        [data-testid="stSidebar"] .char-name-badge,
        [data-testid="stSidebar"] .char-tags,
        [data-testid="stSidebar"] .hp-meta {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.4rem;
        }

        [data-testid="stSidebar"] .char-name-text {
            min-width: 0;
            color: #f4efe2;
            font-family: 'Cinzel', Georgia, serif;
            font-size: 1rem;
            font-weight: 600;
            overflow-wrap: anywhere;
        }

        [data-testid="stSidebar"] .char-level-badge {
            display: flex;
            flex: 0 0 auto;
            align-items: baseline;
            gap: 0.25rem;
            color: var(--realm-gold-pale);
            font-size: 0.78rem;
        }

        [data-testid="stSidebar"] .char-tags {
            justify-content: flex-start;
            flex-wrap: wrap;
            margin: 0.45rem 0 0.6rem;
        }

        [data-testid="stSidebar"] .tag-pill {
            padding: 0.15rem 0.4rem;
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 4px;
            color: #e5dfd0;
            font-size: 0.7rem;
            overflow-wrap: anywhere;
        }

        [data-testid="stSidebar"] .vitals-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: center;
            gap: 0.5rem;
        }

        [data-testid="stSidebar"] .hp-meta {
            font-size: 0.72rem;
        }

        [data-testid="stSidebar"] .hp-bar-bg {
            height: 6px;
            margin-top: 0.3rem;
            overflow: hidden;
            border-radius: 4px;
            background: #303541;
        }

        [data-testid="stSidebar"] .hp-bar-fill {
            height: 100%;
            border-radius: inherit;
        }

        [data-testid="stSidebar"] .ac-shield-box {
            min-width: 2.2rem;
            padding: 0.2rem;
            border: 1px solid rgba(212, 175, 55, 0.3);
            border-radius: 5px;
            text-align: center;
        }

        [data-testid="stSidebar"] .ac-num {
            color: #f4efe2;
            font-size: 1rem;
            font-weight: 700;
        }

        [data-testid="stSidebar"] .ac-label {
            color: var(--realm-muted);
            font-size: 0.62rem;
        }

        [data-testid="stSidebar"] .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.35rem;
            margin-top: 0.65rem;
        }

        [data-testid="stSidebar"] .stat-box {
            min-width: 0;
            padding: 0.3rem 0.15rem;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 5px;
            background: rgba(255, 255, 255, 0.035);
            text-align: center;
        }

        [data-testid="stSidebar"] .s-name {
            color: var(--realm-muted);
            font-size: 0.65rem;
            font-weight: 600;
        }

        [data-testid="stSidebar"] .s-val {
            color: #f4efe2;
            font-size: 0.95rem;
            font-weight: 700;
            line-height: 1.15;
        }

        [data-testid="stSidebar"] .s-mod {
            color: var(--realm-gold-pale);
            font-size: 0.68rem;
        }

        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Source Sans 3', sans-serif;
        }

        section[data-testid="stMain"] .block-container {
            width: 100%;
            max-width: 100%;
            padding-left: clamp(0.75rem, 3vw, 2rem);
            padding-right: clamp(0.75rem, 3vw, 2rem);
        }

        section[data-testid="stMain"]:has(.auth-portal-card) {
            background-color: var(--realm-ink);
            background-image:
                linear-gradient(135deg, rgba(212, 175, 55, 0.025) 25%, transparent 25%, transparent 75%, rgba(212, 175, 55, 0.025) 75%),
                linear-gradient(180deg, #171a22 0%, var(--realm-ink) 72%);
            background-size: 42px 42px, 100% 100%;
        }

        section[data-testid="stMain"]:has(.auth-portal-card) .block-container {
            width: min(100%, 740px);
            max-width: 740px;
            margin-inline: auto;
            padding-top: clamp(2rem, 8vh, 5rem);
            padding-bottom: 3rem;
        }

        .auth-portal-card {
            box-sizing: border-box;
            width: 100%;
            margin-bottom: 1rem;
            padding: 2rem 2rem 1.5rem;
            border: 1px solid rgba(212, 175, 55, 0.3);
            border-top: 2px solid var(--realm-gold);
            border-radius: 8px;
            background: linear-gradient(150deg, rgba(27, 32, 42, 0.98), rgba(15, 18, 25, 0.98));
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.28);
        }

        .auth-portal-header {
            text-align: center;
        }

        .auth-portal-emblem {
            display: grid;
            place-items: center;
            width: 3rem;
            aspect-ratio: 1;
            margin: 0 auto 0.8rem;
            border: 1px solid rgba(212, 175, 55, 0.55);
            border-radius: 50%;
            background: rgba(212, 175, 55, 0.08);
            font-size: 1.35rem;
        }

        .auth-portal-kicker {
            margin: 0 0 0.45rem;
            color: var(--realm-gold-pale);
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        h1.auth-portal-title {
            margin: 0;
            color: #f4efe2;
            font-family: 'Cinzel', Georgia, serif;
            font-size: clamp(1.6rem, 4vw, 2.35rem);
            font-weight: 600;
            line-height: 1.2;
            overflow-wrap: normal;
            text-wrap: balance;
        }

        .auth-portal-subtitle {
            margin: 0.7rem 0 0;
            color: var(--realm-muted);
            font-size: 0.98rem;
        }

        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.5rem;
            border-bottom: 1px solid rgba(212, 175, 55, 0.22);
        }

        div[data-testid="stTabs"] button[role="tab"] {
            min-height: 2.8rem;
            color: var(--realm-muted);
            font-weight: 600;
        }

        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: var(--realm-gold-pale);
        }

        div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            background-color: var(--realm-gold);
        }

        div[data-testid="stForm"] {
            padding: 1rem 1.1rem 0.8rem;
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 8px;
            background: rgba(20, 24, 33, 0.82);
        }

        div[data-testid="stTextInput"] input {
            border-color: #3b414d;
            background: var(--realm-panel-raised);
        }

        div[data-testid="stTextInput"] input:focus {
            border-color: var(--realm-gold);
            box-shadow: 0 0 0 1px var(--realm-gold);
        }

        div[data-testid="stFormSubmitButton"] button {
            border: 1px solid var(--realm-gold);
            background: linear-gradient(180deg, #e4c45b, #c49b25);
            color: #17150f;
            font-weight: 700;
        }

        div[data-testid="stFormSubmitButton"] button:hover {
            border-color: var(--realm-gold-pale);
            background: var(--realm-gold-pale);
            color: #17150f;
        }

        @media (max-width: 640px) {
            section[data-testid="stMain"] .block-container {
                padding: 0.75rem 0.5rem 2rem;
            }

            section[data-testid="stMain"]:has(.auth-portal-card) .block-container {
                width: 100%;
                max-width: 100%;
                padding: 4rem 0.5rem 2rem;
            }

            .auth-portal-card {
                padding: 1.5rem 1rem 1.25rem;
            }

            h1.auth-portal-title {
                font-size: clamp(1.5rem, 7vw, 2rem);
            }

            div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
                min-width: 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
