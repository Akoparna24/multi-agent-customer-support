import os


def get_secret(key: str) -> str:
    """Get secret from Streamlit Cloud or local .env"""
    # Try Streamlit secrets first
    try:
        import streamlit as st
        value = st.secrets.get(key)
        if value:
            return value
    except Exception:
        pass

    # Fall back to environment variables
    value = os.getenv(key)
    if value:
        return value

    raise ValueError(f"Secret '{key}' not found in Streamlit secrets or .env file")


ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
WEAVIATE_URL = get_secret("WEAVIATE_URL")
WEAVIATE_API_KEY = get_secret("WEAVIATE_API_KEY")
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")