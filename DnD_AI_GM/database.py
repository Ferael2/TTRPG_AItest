# database.py
# Supabase client setup, campaign persistence helpers, and user account storage.

import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def init_supabase(url: str, key: str) -> Client:
    """Initialises and caches the Supabase client for the lifetime of the app process."""
    return create_client(url, key)


def _resolve_campaign_id(campaign_id: str | None = None) -> str:
    """Resolves the active campaign ID from argument or session state."""
    if campaign_id:
        return campaign_id
    if hasattr(st, "session_state") and "campaign_id" in st.session_state:
        return st.session_state.campaign_id
    return "default_campaign"


def load_db_campaign(supabase: Client, campaign_id: str | None = None):
    """Loads the campaign record from the Supabase database.

    Returns the campaign data dict on success, or None if no record exists.
    """
    target_id = _resolve_campaign_id(campaign_id)
    try:
        response = supabase.table("campaigns").select("data").eq("id", target_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["data"]
    except Exception as e:
        st.error(f"Error loading campaign '{target_id}' from Supabase: {e}")
    return None


def save_db_campaign(supabase: Client, data: dict, campaign_id: str | None = None):
    """Saves (upserts) the full campaign record to the Supabase database."""
    target_id = _resolve_campaign_id(campaign_id)
    try:
        supabase.table("campaigns").upsert({"id": target_id, "data": data}).execute()
    except Exception as e:
        st.error(f"Error saving campaign '{target_id}' to Supabase: {e}")


def delete_db_campaign(supabase: Client, campaign_id: str | None = None):
    """Deletes the campaign record from the Supabase database, effectively resetting it."""
    target_id = _resolve_campaign_id(campaign_id)
    try:
        supabase.table("campaigns").delete().eq("id", target_id).execute()
    except Exception as e:
        st.error(f"Error resetting Supabase record '{target_id}': {e}")


# =============================================================================
# USER ACCOUNT PERSISTENCE
# =============================================================================

def get_user_record(supabase: Client, username: str) -> dict | None:
    """Fetches user credentials and profile by username from the campaigns table."""
    normalized_username = username.strip().lower()
    try:
        resp = (
            supabase.table("campaigns")
            .select("data")
            .eq("id", f"user_account:{normalized_username}")
            .execute()
        )
        if resp.data and len(resp.data) > 0:
            return resp.data[0]["data"]
    except Exception as e:
        st.error(f"Error fetching user record from Supabase: {e}")
    return None


def save_user_record(supabase: Client, user_data: dict) -> bool:
    """Persists a user record to the Supabase campaigns table."""
    normalized_username = user_data["username"].strip().lower()
    try:
        supabase.table("campaigns").upsert({
            "id": f"user_account:{normalized_username}",
            "data": user_data,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error saving user record to Supabase: {e}")
        return False


def list_user_records(supabase: Client) -> list[dict]:
    """Lists all registered user records for administrative oversight."""
    try:
        resp = (
            supabase.table("campaigns")
            .select("data")
            .like("id", "user_account:%")
            .execute()
        )
        if resp.data and len(resp.data) > 0:
            return [row["data"] for row in resp.data if "data" in row and isinstance(row["data"], dict)]
    except Exception:
        pass
    return []


def delete_user_record(supabase: Client, username: str) -> bool:
    """Deletes a user's account record and their isolated campaign vault from Supabase."""
    normalized_username = username.strip().lower()
    try:
        supabase.table("campaigns").delete().eq("id", f"user_account:{normalized_username}").execute()
        supabase.table("campaigns").delete().eq("id", f"campaign_{normalized_username}").execute()
        return True
    except Exception as e:
        st.error(f"Error deleting user record from Supabase: {e}")
        return False

