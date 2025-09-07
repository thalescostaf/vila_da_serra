# src/ui.py
import streamlit as st
from src.supabase_client import supabase, ensure_postgrest_auth

def back_home():
    if st.button("← Voltar para Home"):
        st.switch_page("pages/00_Home.py")

def require_auth():
    ensure_postgrest_auth()
    try:
        resp = supabase.auth.get_user()
        user = getattr(resp, "user", None)
    except Exception:
        user = None
    if not user:
        st.switch_page("pages/0_Login.py")
    # reassert token
    ensure_postgrest_auth()
    return user
