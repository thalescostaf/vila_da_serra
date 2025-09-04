import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from src.supabase_client import table
from src.ui import back_home, require_auth

st.set_page_config(page_title="Fluxo de Caixa", page_icon="💰", layout="wide")

# exige login e aplica token
require_auth()

# botão voltar
back_home()

st.title("💰 Fluxo de Caixa")

TIPOS = ["entrada", "saida"]

# -------- utilitários --------
def fmt_data_ddmmaaaa(v):
    if not v:
        return ""
    try:
        if isinstance(v, (datetime, date)):
            d = v if isinstance(v, date) else v.date()
        else:
            s = str(v).split("T")[0]  # "YYYY-MM-DD"
            d = datetime.strptime(s, "%Y-%m-%d").date()
        return d.strftime("%d/%m/%Y")
    except Exception:
        return str(v)

# -------- filtros --------
hoje = date.today()
default_ini = hoje - timedelta(days=30)
col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
with col_f1:
    data_ini = st.date_input("Data inicial", value=default_ini)
with col_f2:
    data_fim = st.date_input("Data final", value=hoje)
with col_f3:
    tipo_sel = st.selectbox("Tipo", ["Todos"] + TIPOS, index=0)

# -------- carregar dados (server-side) --------
def carregar_transacoes(dt_ini: date | None, dt_fim: date | None, tipo: str | None):
    q = table("transacoes").select("id,data,descricao,valor,tipo,created_at")
    if dt_ini:
        q = q.gte("data", dt_ini.isoformat())
    if dt_fim:
        q = q.lte("data", dt_fim.isoformat())
    if tipo and tipo in TIPOS:
        q = q.eq("tipo", tipo)
    q = q.order("data", desc=True).order("created_at", desc=True).limit(500)
    res = q.execute()
    return pd.DataFrame(res.data or [])

df = carregar_transacoes(data_ini, data_fim, tipo_sel if tipo_sel != "Todos" else None)

# -------- listagem --------
st.subheader("Transações")

if df.empty:
    st.info("Nenhuma transação encontrada no período.")
else:
    df_view = df.copy()
    df_view["data_fmt"] = df_view["data"].apply(fmt_data_ddmmaaaa)
    df_view = df_view.sort_values(["data", "created_at"], ascending=[False, False])

    cols_order = ["data_fmt", "descricao", "valor", "tipo"]
    col_cfg = {
        "data_fmt": st.column_config.TextColumn("Data"),
        "descricao": st.column_config.TextColumn("Transação"),
        "tipo": st.column_config.TextColumn("Tipo"),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
    }
    st.dataframe(
        df_view[cols_order],
        hide_index=True,
        use_container_width=True,
        column_config=col_cfg,
    )

st.divider()

# -------- expander com abas: Criar / Editar-Excluir --------
with st.expander("Gerenciar transações", expanded=False):
    tab_criar, tab_editar = st.tabs(["➕ Criar", "✏️ Editar/Excluir"])

    # --- Aba Criar ---
    with tab_criar:
        with st.form("form_nova_tx"):
            descricao = st.text_input("Descrição", max_chars=200)
            tipo = st.selectbox("Tipo", TIPOS, index=0)
            valor = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
            data_tx = st.date_input("Data", value=hoje)
            salvar = st.form_submit_button("Salvar", type="primary")

        if salvar:
            if not descricao.strip():
                st.error("Informe a descrição.")
            else:
                payload = {
                    "descricao": descricao.strip(),
                    "tipo": tipo,
                    "valor": float(valor),
                    "data": data_tx.isoformat(),
                }
                try:
                    table("transacoes").insert(payload).execute()
                    st.success("Transação criada.")
                except Exception as e:
                    st.error("Não foi possível criar a transação.")
                    st.exception(e)

    # --- Aba Editar/Excluir ---
    with tab_editar:
        if df.empty:
            st.info("Não há transações para editar.")
        else:
            opcoes = []
            for _, r in df.iterrows():
                rotulo = (
                    f"{fmt_data_ddmmaaaa(r.get('data'))} — {r.get('tipo','')} — "
                    f"{r.get('descricao','')} — R$ {float(r.get('valor',0)):,.2f} — "
                    f"#{str(r.get('id',''))[:8].upper()}"
                )
                opcoes.append((rotulo, r.get("id")))
            labels, ids = zip(*opcoes)
            escolha = st.selectbox("Selecione a transação", labels, index=0)
            tx_id = ids[labels.index(escolha)]
            atual = df[df["id"] == tx_id].iloc[0].to_dict()

            try:
                y, m, d = map(int, str(atual.get("data")).split("-"))
                data_default = date(y, m, d)
            except Exception:
                data_default = hoje

            tipo_idx = TIPOS.index(atual.get("tipo", "entrada")) if atual.get("tipo") in TIPOS else 0

            with st.form("form_edit_tx"):
                descricao = st.text_input("Descrição", value=str(atual.get("descricao","")), max_chars=200)
                tipo = st.selectbox("Tipo", TIPOS, index=tipo_idx)
                valor = st.number_input(
                    "Valor",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    value=float(atual.get("valor", 0.0)),
                )
                data_tx = st.date_input("Data", value=data_default)

                col1, col2 = st.columns([1, 1])
                with col1:
                    salvar = st.form_submit_button("Salvar alterações", type="primary")
                with col2:
                    excluir = st.form_submit_button("Excluir", type="secondary")

            if salvar:
                if not descricao.strip():
                    st.error("Informe a descrição.")
                else:
                    payload = {
                        "descricao": descricao.strip(),
                        "tipo": tipo,
                        "valor": float(valor),
                        "data": data_tx.isoformat(),
                    }
                    try:
                        table("transacoes").update(payload).eq("id", tx_id).execute()
                        st.success("Transação atualizada.")
                    except Exception as e:
                        st.error("Não foi possível atualizar a transação.")
                        st.exception(e)

            if excluir:
                try:
                    table("transacoes").delete().eq("id", tx_id).execute()
                    st.success("Transação excluída.")
                except Exception as e:
                    st.error("Não foi possível excluir a transação.")
                    st.exception(e)
