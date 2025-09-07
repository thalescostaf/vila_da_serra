# pages/00_Home.py
import streamlit as st
from src.ui import require_auth
from src.supabase_client import supabase

st.set_page_config(page_title="Vila da Serra — Home", page_icon="🏠", layout="wide")

user = require_auth()  # garante sessão válida

st.title("🏠 Vila da Serra — Home")

col_user, col_logout = st.columns([3, 1])
col_user.success(f"Conectado: {user.email}")

if col_logout.button("Sair"):
    try:
        supabase.auth.sign_out()
        try:
            supabase.postgrest.auth(None)
        except Exception:
            pass
        st.query_params.clear()
        st.rerun()  # volta ao main.py, que mostrará a página de Login
    finally:
        pass
    st.stop()

st.write("Selecione um módulo para continuar.")

def go(label: str, page_path: str):
    if st.button(label, use_container_width=True, type="primary"):
        st.switch_page(page_path)

go("📈 Métricas", "pages/1_Metricas.py")
go("📝 Ocorrências", "pages/2_Ocorrencias.py")
go("💰 Fluxo de Caixa", "pages/3_Fluxo_de_Caixa.py")
go("🗓️ Agenda", "pages/4_Agenda.py")
go("👥 Moradores", "pages/5_Moradores.py")
