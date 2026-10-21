# auth.py
# User authentication, secure password hashing, and user management for D&D AI GM.

from datetime import datetime, timezone
import hashlib
import hmac
import re
import secrets

from config import SESSION_GRACE_PERIOD_SECONDS
from database import (
    get_user_record,
    save_user_record,
    list_user_records,
    delete_user_record,
    save_session_record,
    get_session_record,
    touch_session_record,
    delete_session_record,
    delete_user_sessions,
)


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hashes a password with PBKDF2-HMAC-SHA256 and a 16-byte random salt.

    Returns (hex_hash, salt).
    """
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return key.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies a password against a stored PBKDF2 hash in constant time."""
    candidate_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(candidate_hash, stored_hash)


PASSWORD_REQUIREMENTS_TEXT = (
    "Passphrase must be more than 5 characters long and include at least "
    "one uppercase letter, one number, and one special symbol (e.g. #%@&!)."
)

_SPECIAL_CHARS_PATTERN = r"[#%@&!$*^_\-+=?/\\|~.,:;()\[\]{}<>\"']"


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Checks a candidate password against the realm's passphrase requirements.

    Requires: more than 5 characters, at least one uppercase letter,
    at least one digit, and at least one special symbol.
    Returns (is_valid, message).
    """
    if len(password) <= 5:
        return False, "Passphrase must be longer than 5 characters."

    if not re.search(r"[A-Z]", password):
        return False, "Passphrase must include at least one capital letter."

    if not re.search(r"[0-9]", password):
        return False, "Passphrase must include at least one number."

    if not re.search(_SPECIAL_CHARS_PATTERN, password):
        return False, "Passphrase must include at least one special symbol (e.g. #%@&!)."

    return True, "Passphrase meets the realm's requirements."


def get_user(supabase, username: str) -> dict | None:
    """Retrieves a user by username from the database."""
    if not username:
        return None
    return get_user_record(supabase, username.strip())


def register_user(
    supabase,
    username: str,
    password: str,
    role: str = "player",
) -> tuple[bool, str, dict | None]:
    """Registers a new user in the database.

    Validates username format, checks for duplicates, and hashes the password.
    Returns (success_bool, message, user_data_dict or None).
    """
    cleaned_user = username.strip()

    if not cleaned_user:
        return False, "Username cannot be empty.", None

    if len(cleaned_user) < 3 or len(cleaned_user) > 30:
        return False, "Username must be between 3 and 30 characters.", None

    if not re.match(r"^[a-zA-Z0-9_]+$", cleaned_user):
        return False, "Username can only contain letters, numbers, and underscores.", None

    is_strong, strength_msg = validate_password_strength(password)
    if not is_strong:
        return False, strength_msg, None

    # Check if user already exists
    existing = get_user(supabase, cleaned_user)
    if existing:
        return False, f"An adventurer with the name '{cleaned_user}' already exists in the realm.", None

    # Hash and save
    pwd_hash, salt = hash_password(password)
    user_data = {
        "username": cleaned_user,
        "password_hash": pwd_hash,
        "salt": salt,
        "role": role,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if save_user_record(supabase, user_data):
        return True, f"Welcome to the realm, {cleaned_user}! Account created successfully.", user_data
    else:
        return False, "Failed to register account with the database. Please try again.", None


def authenticate_user(supabase, username: str, password: str) -> tuple[dict | None, str]:
    """Authenticates a user by username and password.

    Returns (user_dict or None, message).
    """
    cleaned_user = username.strip()
    if not cleaned_user or not password:
        return None, "Please enter both username and password."

    user = get_user(supabase, cleaned_user)
    if not user:
        return None, "Invalid username or password."

    stored_hash = user.get("password_hash", "")
    salt = user.get("salt", "")

    if not stored_hash or not salt:
        return None, "Account configuration error. Please contact the administrator."

    if verify_password(password, stored_hash, salt):
        return user, f"Welcome back, {user.get('username', cleaned_user)}!"

    return None, "Invalid username or password."


def init_admin_account(supabase, default_password: str = "Admin#123") -> None:
    """Ensures the admin account exists in Supabase.

    If 'admin' does not exist, registers it with role='admin' and default_password.
    """
    admin_user = get_user(supabase, "admin")
    if not admin_user:
        register_user(
            supabase=supabase,
            username="admin",
            password=default_password,
            role="admin",
        )


def list_all_users(supabase) -> list[dict]:
    """Retrieves all registered users for admin oversight."""
    return list_user_records(supabase)


def delete_user(supabase, username: str, requesting_user: dict | None = None) -> tuple[bool, str]:
    """Deletes an adventurer account and their campaign vault.

    Enforces that only admin can delete accounts and the admin account cannot be deleted.
    Returns (success_bool, message).
    """
    if requesting_user and requesting_user.get("role") != "admin":
        return False, "Permission denied: Only Realm Administrators may banish accounts."

    cleaned_user = username.strip()
    if cleaned_user.lower() == "admin":
        return False, "The master Realm Administrator account cannot be banished."

    target_user = get_user(supabase, cleaned_user)
    if not target_user:
        return False, f"Adventurer '{cleaned_user}' does not exist in the realm."

    if delete_user_record(supabase, cleaned_user):
        delete_user_sessions(supabase, cleaned_user)
        return True, f"Adventurer '{cleaned_user}' and their campaign vault have been banished from the realm."
    else:
        return False, f"Failed to delete adventurer '{cleaned_user}'. Please try again."


# =============================================================================
# SESSION LIFECYCLE & INACTIVITY GRACE PERIOD
# =============================================================================

def create_user_session(supabase, username: str) -> str:
    """Generates a secure cryptographically random session token and persists it in Supabase."""
    token = secrets.token_urlsafe(32)
    save_session_record(supabase, token, username)
    return token


def validate_session(
    supabase,
    token: str,
    grace_period_seconds: int = SESSION_GRACE_PERIOD_SECONDS,
) -> tuple[dict | None, str]:
    """Validates an adventurer's session token and inactivity grace period.

    Checks:
    1. Does the session record exist in Supabase?
    2. Has the user been inactive for longer than grace_period_seconds?
       - If yes: purges the session from Supabase and returns (None, "Session expired due to inactivity").
    3. Does the user record still exist in the realm?
       - If not: purges the orphaned session and returns (None, "Account no longer exists").
    4. If valid: returns (user_data, "Session valid").
    """
    if not token or not token.strip():
        return None, "No session token provided."

    session_record = get_session_record(supabase, token.strip())
    if not session_record:
        return None, "Session record not found."

    last_active_str = session_record.get("last_active")
    if not last_active_str:
        delete_session_record(supabase, token.strip())
        return None, "Invalid session record format."

    try:
        last_active = datetime.fromisoformat(last_active_str)
        if last_active.tzinfo is None:
            last_active = last_active.replace(tzinfo=timezone.utc)
    except Exception:
        delete_session_record(supabase, token.strip())
        return None, "Corrupted session timestamp."

    now = datetime.now(timezone.utc)
    inactivity_seconds = (now - last_active).total_seconds()

    if inactivity_seconds > grace_period_seconds:
        # Grace period has lapsed - session is closed
        delete_session_record(supabase, token.strip())
        return None, "Session expired due to inactivity."

    username = session_record.get("username", "")
    user = get_user(supabase, username)
    if not user:
        delete_session_record(supabase, token.strip())
        return None, "Adventurer account no longer exists."

    return user, "Session valid."


def touch_session(supabase, token: str) -> bool:
    """Updates the session's activity timestamp in Supabase to keep the grace period active."""
    if not token:
        return False
    return touch_session_record(supabase, token.strip())


def terminate_session(supabase, token: str) -> bool:
    """Explicitly ends a session (e.g. upon user logout)."""
    if not token:
        return False
    return delete_session_record(supabase, token.strip())

