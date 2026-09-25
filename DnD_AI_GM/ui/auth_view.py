# ui/auth_view.py
# Renders the Dark Fantasy login and registration gateway.

import streamlit as st
from auth import authenticate_user, register_user, get_user, PASSWORD_REQUIREMENTS_TEXT


def render_auth_page(supabase):
    """Renders the authentication portal gating access to the chat.

    Mutates st.session_state when login or registration is successful.
    """
    col_main = st.container()

    with col_main:
        st.markdown(
            """
            <div class="auth-portal-card">
                <div class="auth-portal-header">
                    <div class="auth-portal-emblem">🎲</div>
                    <p class="auth-portal-kicker">YOUR NEXT CHRONICLE BEGINS HERE</p>
                    <h1 class="auth-portal-title">CHRONICLES OF THE REALM</h1>
                    <p class="auth-portal-subtitle">Identify yourself, traveller, before consulting the Game Master.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["⚔️ Enter Realm (Log In)", "📜 Register Adventurer (Sign Up)"])

        # =========================================================================
        # TAB 1: LOGIN
        # =========================================================================
        with tab_login:
            st.markdown("<p style='color: #cbd5e1; font-size: 0.9rem; margin-top: 6px;'>Resume your chronicle with your credentials.</p>", unsafe_allow_html=True)
            with st.form(key="login_form", clear_on_submit=False):
                username_input = st.text_input(
                    "Adventurer Name",
                    placeholder="e.g. admin or Valen",
                    key="login_user_input",
                )
                password_input = st.text_input(
                    "Secret Passphrase",
                    type="password",
                    placeholder="Enter your passphrase",
                    key="login_pass_input",
                )
                submit_login = st.form_submit_button("⚔️ Enter the Realm", use_container_width=True)

            if submit_login:
                user, msg = authenticate_user(supabase, username_input, password_input)
                if user:
                    st.session_state.current_user = user
                    # Admin inherits default_campaign; other users get their isolated campaign key
                    if user.get("role") == "admin":
                        st.session_state.campaign_id = "default_campaign"
                    else:
                        st.session_state.campaign_id = f"campaign_{user['username'].lower()}"

                    # Clear existing cached campaign_data to guarantee clean reload for this user
                    if "campaign_data" in st.session_state:
                        del st.session_state.campaign_data
                    if "turn_counter" in st.session_state:
                        del st.session_state.turn_counter

                    st.success(f"Access granted! Welcome, {user['username']}.")
                    st.rerun()
                else:
                    st.error(f"⛔ {msg}")

        # =========================================================================
        # TAB 2: REGISTER
        # =========================================================================
        with tab_register:
            st.markdown("<p style='color: #cbd5e1; font-size: 0.9rem; margin-top: 6px;'>Inscribe your name into the realm's sacred registry to begin your journey.</p>", unsafe_allow_html=True)
            with st.form(key="register_form", clear_on_submit=False):
                reg_user = st.text_input(
                    "Desired Adventurer Name",
                    placeholder="e.g. Morvath (letters, numbers, underscores)",
                    key="reg_user_input",
                )
                reg_pass = st.text_input(
                    "Choose Passphrase",
                    type="password",
                    placeholder="6+ chars, 1 capital, 1 number, 1 symbol",
                    key="reg_pass_input",
                )
                st.markdown(
                    f"<p style='color: #94a3b8; font-size: 0.75rem; margin-top: -8px; margin-bottom: 10px;'>🔒 {PASSWORD_REQUIREMENTS_TEXT}</p>",
                    unsafe_allow_html=True,
                )
                reg_confirm = st.text_input(
                    "Confirm Passphrase",
                    type="password",
                    placeholder="Repeat your passphrase",
                    key="reg_confirm_input",
                )
                submit_register = st.form_submit_button("📜 Swear Oath & Register", use_container_width=True)

            if submit_register:
                if reg_pass != reg_confirm:
                    st.error("⛔ Passphrases do not match. Please verify your entry.")
                else:
                    success, msg, new_user = register_user(
                        supabase=supabase,
                        username=reg_user,
                        password=reg_pass,
                        role="player",
                    )
                    if success and new_user:
                        st.session_state.current_user = new_user
                        st.session_state.campaign_id = f"campaign_{new_user['username'].lower()}"
                        if "campaign_data" in st.session_state:
                            del st.session_state.campaign_data
                        if "turn_counter" in st.session_state:
                            del st.session_state.turn_counter
                        st.rerun()
                    else:
                        st.error(f"⛔ {msg}")

        st.markdown(
            """
            <div style="text-align: center; margin-top: 24px; color: #64748b; font-size: 0.78rem;">
                🛡️ <em>Every adventurer's tale, lore, and inventory are held in their own isolated vault.</em>
            </div>
            """,
            unsafe_allow_html=True,
        )
