# pages/0_Login.py
import streamlit as st
from src.supabase_client import supabase, ensure_postgrest_auth

st.set_page_config(page_title="Vila da Serra — Login", page_icon="🔐", layout="centered")

ensure_postgrest_auth()

st.title("🔐 Acesso")

def get_current_user():
    try:
        resp = supabase.auth.get_user()
        return getattr(resp, "user", None)
    except Exception:
        return None

user = get_current_user()

# Se já estiver logado e abrir /Login, apenas re-renderizamos para o main decidir (vai cair na Home)
if user:
    st.success(f"Você já está autenticado como {user.email}.")
    st.query_params.clear()
    st.rerun()  # main.py vai montar a nav autenticada (Home/Módulos)
    st.stop()

with st.form("form_login"):
    email = st.text_input("E-mail", autocomplete="username")
    password = st.text_input("Senha", type="password", autocomplete="current-password")
    entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

if entrar:
    if not email or not password:
        st.error("Informe e-mail e senha.")
    else:
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            # aplica o token ao PostgREST imediatamente
            try:
                if getattr(res, "session", None) and getattr(res.session, "access_token", None):
                    supabase.postgrest.auth(res.session.access_token)
            except Exception:
                pass

            ensure_postgrest_auth()
            user = get_current_user()

            if user:
                st.success("Autenticado com sucesso. Redirecionando…")
                st.query_params.clear()
                st.rerun()  # deixa o main.py redirecionar para a Home
            else:
                st.warning("Autenticado, mas não foi possível carregar o usuário. Tente novamente.")
        except Exception as e:
            st.error("Falha ao autenticar. Verifique suas credenciais.")
            st.exception(e)
