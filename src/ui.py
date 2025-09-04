# src/ui.py
import streamlit as st
from src.supabase_client import supabase, ensure_postgrest_auth

def back_home():
    # Botão simples para voltar à Home
    if st.button("← Voltar para Home"):
        st.switch_page("app.py")

def require_auth():
    """
    Garante que o usuário esteja autenticado e aplica o token no PostgREST.
    Use no topo de cada página (antes de qualquer operação no banco).
    """
    # Aplica (ou limpa) o token da sessão atual no PostgREST
    ensure_postgrest_auth()

    # Verifica se há usuário
    try:
        resp = supabase.auth.get_user()
        user = getattr(resp, "user", None)
    except Exception:
        user = None

    if not user:
        # Mensagem discreta e bloqueio da página
        st.warning("Acesse a Home para entrar.")
        st.stop()

    # Reforça o token após obter o usuário (cobre casos de renovação de sessão)
    ensure_postgrest_auth()
    return user
