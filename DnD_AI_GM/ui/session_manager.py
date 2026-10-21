# ui/session_manager.py
# Client-side session cookie management and synchronization across page reloads & browser restarts.

import streamlit as st
import streamlit.components.v1 as components
from config import SESSION_COOKIE_NAME, SESSION_GRACE_PERIOD_SECONDS


def set_client_session(token: str, max_age: int = SESSION_GRACE_PERIOD_SECONDS) -> None:
    """Injects JavaScript to persist the session token in cookies and localStorage."""
    if not token:
        return

    # Injects both directly and into parent frame for complete browser compatibility
    js_payload = f"""
    <script>
    (function() {{
        const token = "{token}";
        const maxAge = {max_age};
        const cookieName = "{SESSION_COOKIE_NAME}";
        const cookieStr = cookieName + "=" + encodeURIComponent(token) + "; path=/; max-age=" + maxAge + "; SameSite=Lax";

        document.cookie = cookieStr;
        try {{
            if (window.parent && window.parent.document) {{
                window.parent.document.cookie = cookieStr;
                window.parent.localStorage.setItem(cookieName, token);
                window.parent.sessionStorage.removeItem(cookieName + "_expired");
            }}
        }} catch(e) {{}}

        try {{
            localStorage.setItem(cookieName, token);
            sessionStorage.removeItem(cookieName + "_expired");
        }} catch(e) {{}}
    }})();
    </script>
    """
    components.html(js_payload, height=0, width=0)


def clear_client_session() -> None:
    """Injects JavaScript to purge the session token from cookies and localStorage."""
    js_payload = f"""
    <script>
    (function() {{
        const cookieName = "{SESSION_COOKIE_NAME}";
        const cookieStr = cookieName + "=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";

        document.cookie = cookieStr;
        try {{
            if (window.parent && window.parent.document) {{
                window.parent.document.cookie = cookieStr;
                window.parent.localStorage.removeItem(cookieName);
                window.parent.sessionStorage.setItem(cookieName + "_expired", "true");
            }}
        }} catch(e) {{}}

        try {{
            localStorage.removeItem(cookieName);
            sessionStorage.setItem(cookieName + "_expired", "true");
        }} catch(e) {{}}
    }})();
    </script>
    """
    components.html(js_payload, height=0, width=0)


def render_session_recovery_bridge() -> None:
    """Runs on the auth gateway: if localStorage has an unexpired token, syncs to cookie and reloads."""
    js_payload = f"""
    <script>
    (function() {{
        try {{
            const cookieName = "{SESSION_COOKIE_NAME}";
            const isMarkedExpired = sessionStorage.getItem(cookieName + "_expired");
            if (isMarkedExpired) {{
                return;
            }}

            const localToken = localStorage.getItem(cookieName);
            const cookies = document.cookie || "";
            const hasCookie = cookies.indexOf(cookieName + "=") !== -1;

            if (localToken && !hasCookie) {{
                document.cookie = cookieName + "=" + encodeURIComponent(localToken) + "; path=/; max-age={SESSION_GRACE_PERIOD_SECONDS}; SameSite=Lax";
                if (window.parent && window.parent.document) {{
                    window.parent.document.cookie = cookieName + "=" + encodeURIComponent(localToken) + "; path=/; max-age={SESSION_GRACE_PERIOD_SECONDS}; SameSite=Lax";
                }}
                window.location.reload();
            }}
        }} catch(e) {{}}
    }})();
    </script>
    """
    components.html(js_payload, height=0, width=0)
