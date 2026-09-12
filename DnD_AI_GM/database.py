# database.py
# Supabase client setup and all campaign persistence helpers.

import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def init_supabase(url: str, key: str) -> Client:
    """Initialises and caches the Supabase client for the lifetime of the app process."""
    return create_client(url, key)


def load_db_campaign(supabase: Client):
    """Loads the campaign record from the Supabase database.

    Returns the campaign data dict on success, or None if no record exists.
    """
    try:
        response = supabase.table("campaigns").select("data").eq("id", "default_campaign").execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["data"]
    except Exception as e:
        st.error(f"Error loading from Supabase: {e}")
    return None


def save_db_campaign(supabase: Client, data: dict):
    """Saves (upserts) the full campaign record to the Supabase database."""
    try:
        supabase.table("campaigns").upsert({"id": "default_campaign", "data": data}).execute()
    except Exception as e:
        st.error(f"Error saving to Supabase: {e}")


def delete_db_campaign(supabase: Client):
    """Deletes the campaign record from the Supabase database, effectively resetting it."""
    try:
        supabase.table("campaigns").delete().eq("id", "default_campaign").execute()
    except Exception as e:
        st.error(f"Error resetting Supabase record: {e}")
