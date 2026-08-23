import os
try:
    import streamlit as st
    ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
    WEAVIATE_URL      = st.secrets["WEAVIATE_URL"]
    WEAVIATE_API_KEY  = st.secrets["WEAVIATE_API_KEY"]
    SUPABASE_URL      = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY      = st.secrets["SUPABASE_KEY"]

except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    WEAVIATE_URL      = os.getenv("WEAVIATE_URL")
    WEAVIATE_API_KEY  = os.getenv("WEAVIATE_API_KEY")
    SUPABASE_URL      = os.getenv("SUPABASE_URL")
    SUPABASE_KEY      = os.getenv("SUPABASE_KEY")