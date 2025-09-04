# pages/1_Metricas.py
import streamlit as st
from src.supabase_client import table
from src.ui import back_home

st.set_page_config(page_title="Métricas", page_icon="📈", layout="wide")

# Botão voltar para Home
back_home()

# Título
st.title("📈 Métricas")

def count_table(table_name: str) -> int:
    # select com count='exact' retorna apenas a contagem
    res = table(table_name).select("id", count="exact").execute()
    return int(res.count or 0)

def count_table_eq(table_name: str, col: str, val: str) -> int:
    # filtros depois do select (importante para o client do Supabase)
    q = table(table_name).select("id", count="exact").eq(col, val)
    res = q.execute()
    return int(res.count or 0)

def count_table_neq(table_name: str, col: str, val: str) -> int:
    q = table(table_name).select("id", count="exact").neq(col, val)
    res = q.execute()
    return int(res.count or 0)

try:
    total_moradores = count_table("moradores")
    total_ocorrencias = count_table("ocorrencias")
    total_finalizadas = count_table_eq("ocorrencias", "status", "finalizada")
    total_em_aberto = count_table_neq("ocorrencias", "status", "finalizada")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Moradores", f"{total_moradores}")
    with c2:
        st.metric("Ocorrências", f"{total_ocorrencias}")
    with c3:
        st.metric("Finalizadas", f"{total_finalizadas}")
    with c4:
        st.metric("Em aberto", f"{total_em_aberto}")

except Exception as e:
    st.error("Não foi possível carregar as métricas. Verifique o .env e as policies no Supabase.")
    st.exception(e)
