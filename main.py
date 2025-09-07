# main.py
import streamlit as st
from src.supabase_client import supabase, ensure_postgrest_auth

st.set_page_config(page_title="Vila da Serra", page_icon="🏢", layout="wide")

ensure_postgrest_auth()

def get_user():
    try:
        res = supabase.auth.get_user()
        return getattr(res, "user", None)
    except Exception:
        return None

user = get_user()

Login       = st.Page("pages/0_Login.py",         title="Login",        icon="🔐")
Home        = st.Page("pages/00_Home.py",         title="Home",         icon="🏠")
Metricas    = st.Page("pages/1_Metricas.py",      title="Métricas",     icon="📈")
Ocorrencias = st.Page("pages/2_Ocorrencias.py",   title="Ocorrências",  icon="📝")
Fluxo       = st.Page("pages/3_Fluxo_de_Caixa.py",title="Fluxo de Caixa", icon="💰")
Agenda      = st.Page("pages/4_Agenda.py",        title="Agenda",       icon="🗓️")
Moradores   = st.Page("pages/5_Moradores.py",     title="Moradores",    icon="👥")

if user:
    nav = st.navigation(
        {
            "Início": [Home],
            "Módulos": [Metricas, Ocorrencias, Fluxo, Agenda, Moradores],
        }
    )
else:
    nav = st.navigation({"": [Login]})

nav.run()
