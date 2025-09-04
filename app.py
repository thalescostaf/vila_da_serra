import streamlit as st
from src.supabase_client import supabase

# Configuração da página
st.set_page_config(page_title="Vila da Serra — Home", page_icon="🏠", layout="wide")

# Título
st.title("🏠 Vila da Serra — Home")

# ---------- Autenticação global ----------
def get_current_user():
    try:
        resp = supabase.auth.get_user()
        return getattr(resp, "user", None)
    except Exception:
        return None

user = get_current_user()

if not user:
    st.subheader("Acesso")
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
                user = get_current_user()
                if user:
                    st.success("Autenticado.")
                else:
                    st.warning("Autenticado, recarregue a página se os módulos não aparecerem.")
            except Exception as e:
                st.error("Falha ao autenticar.")
                st.exception(e)

    if not user:
        st.stop()

# Barra de usuário/logoff
col_user, col_logout = st.columns([3, 1])
col_user.success(f"Conectado: {user.email}")
if col_logout.button("Sair"):
    try:
        supabase.auth.sign_out()
    finally:
        st.experimental_set_query_params()
    st.stop()

# ---------- Navegação ----------
def go(label: str, page_path: str):
    if st.button(label, use_container_width=True, type="primary"):
        st.switch_page(page_path)

st.write("Selecione um módulo para continuar.")
go("📈 Métricas", "pages/1_Metricas.py")
go("📝 Ocorrências", "pages/2_Ocorrencias.py")
go("💰 Fluxo de Caixa", "pages/3_Fluxo_de_Caixa.py")
go("🗓️ Agenda", "pages/4_Agenda.py")
go("👥 Moradores", "pages/5_Moradores.py")
