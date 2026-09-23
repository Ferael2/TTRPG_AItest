# auth.py
# User authentication, secure password hashing, and user management for D&D AI GM.

from datetime import datetime, timezone
import hashlib
import hmac
import re
import secrets

from database import get_user_record, save_user_record, list_user_records


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

    if len(password) < 4:
        return False, "Password must be at least 4 characters long.", None

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


def init_admin_account(supabase, default_password: str = "admin123") -> None:
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
