# src/auth.py
import streamlit as st
from src.supabase_client import supabase

def _get_user():
    try:
        resp = supabase.auth.get_user()
        return getattr(resp, "user", None)
    except Exception:
        return None

def login_widget(title: str = "Acesso"):
    st.subheader(title)

    user = _get_user()
    if user:
        cols = st.columns([3, 1])
        cols[0].success(f"Conectado: {user.email}")
        if cols[1].button("Sair"):
            try:
                supabase.auth.sign_out()
            finally:
                pass
        return True

    with st.form("form_login"):
        email = st.text_input("E-mail", autocomplete="username")
        password = st.text_input("Senha", type="password", autocomplete="current-password")
        entrar = st.form_submit_button("Entrar", type="primary")

    if entrar:
        if not email or not password:
            st.error("Informe e-mail e senha.")
        else:
            try:
                supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.success("Autenticado.")
                return True
            except Exception as e:
                st.error("Falha ao autenticar.")
                st.exception(e)
    return False
