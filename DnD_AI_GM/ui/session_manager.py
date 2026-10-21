# ui/session_manager.py
# Client-side session storage management and synchronization across page reloads & browser restarts.

import streamlit as st
import streamlit.components.v1 as components
from config import SESSION_COOKIE_NAME, SESSION_GRACE_PERIOD_SECONDS


def set_client_session(token: str, max_age: int = SESSION_GRACE_PERIOD_SECONDS) -> None:
    """Persists the session token across browser sessions via localStorage and cookies."""
    if not token:
        return

    # Use st.html (non-iframed top-level execution) + components.html fallback
    js_code = f"""
    <script>
    (function() {{
        try {{
            const token = "{token}";
            const maxAge = {max_age};
            const cookieName = "{SESSION_COOKIE_NAME}";
            const isHttps = window.location.protocol === 'https:';
            const secureFlag = isHttps ? '; Secure' : '';
            const cookieStr = cookieName + "=" + encodeURIComponent(token) + "; path=/; max-age=" + maxAge + secureFlag + "; SameSite=Lax";

            document.cookie = cookieStr;
            localStorage.setItem(cookieName, token);
            sessionStorage.removeItem("dnd_logged_out");

            if (window.parent && window.parent !== window) {{
                try {{
                    window.parent.document.cookie = cookieStr;
                    window.parent.localStorage.setItem(cookieName, token);
                    window.parent.sessionStorage.removeItem("dnd_logged_out");
                }} catch(e) {{}}
            }}
        }} catch(e) {{}}
    }})();
    </script>
    """
    try:
        st.html(js_code, unsafe_allow_javascript=True)
    except Exception:
        components.html(js_code, height=0, width=0)


def clear_client_session() -> None:
    """Purges the session token from client cookies and localStorage."""
    js_code = f"""
    <script>
    (function() {{
        try {{
            const cookieName = "{SESSION_COOKIE_NAME}";
            const isHttps = window.location.protocol === 'https:';
            const secureFlag = isHttps ? '; Secure' : '';
            const cookieStr = cookieName + "=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT" + secureFlag + "; SameSite=Lax";

            document.cookie = cookieStr;
            localStorage.removeItem(cookieName);
            sessionStorage.setItem("dnd_logged_out", "true");

            if (window.parent && window.parent !== window) {{
                try {{
                    window.parent.document.cookie = cookieStr;
                    window.parent.localStorage.removeItem(cookieName);
                    window.parent.sessionStorage.setItem("dnd_logged_out", "true");
                }} catch(e) {{}}
            }}
        }} catch(e) {{}}
    }})();
    </script>
    """
    try:
        st.html(js_code, unsafe_allow_javascript=True)
    except Exception:
        components.html(js_code, height=0, width=0)


def render_session_recovery_bridge() -> None:
    """On the auth gateway: checks if localStorage holds a saved token and attaches it to query_params."""
    js_code = f"""
    <script>
    (function() {{
        try {{
            const cookieName = "{SESSION_COOKIE_NAME}";
            const isLoggedOut = sessionStorage.getItem("dnd_logged_out");
            if (isLoggedOut) {{
                return;
            }}

            const localToken = localStorage.getItem(cookieName);
            const currentUrl = new URL(window.location.href);

            if (localToken && !currentUrl.searchParams.has("session")) {{
                currentUrl.searchParams.set("session", localToken);
                window.location.replace(currentUrl.href);
            }}
        }} catch(e) {{}}
    }})();
    </script>
    """
    try:
        st.html(js_code, unsafe_allow_javascript=True)
    except Exception:
        components.html(js_code, height=0, width=0)
