# pages/5_Moradores.py
import streamlit as st
import pandas as pd
from src.supabase_client import table
from src.ui import back_home, require_auth

st.set_page_config(page_title="Moradores", page_icon="👥", layout="wide")

# exige login e aplica token
require_auth()

# voltar para Home
back_home()

st.title("👥 Moradores")

# --------- utils ---------
def carregar_moradores(nome: str | None = None, predio: str | None = None, apto: str | None = None) -> pd.DataFrame:
    # Carrega moradores aplicando filtros server-side quando possível
    q = table("moradores").select("id,nome,telefone,predio,apto,created_at").order("nome")
    if nome and nome.strip():
        q = q.ilike("nome", f"%{nome.strip()}%")
    if predio and predio.strip():
        q = q.ilike("predio", f"%{predio.strip()}%")
    if apto and apto.strip():
        q = q.ilike("apto", f"%{apto.strip()}%")
    res = q.limit(1000).execute()
    return pd.DataFrame(res.data or [])

def label_morador(row: dict) -> str:
    return f"{row.get('nome','(sem nome)')} — Prédio {row.get('predio','?')}, Apto {row.get('apto','?')} — #{str(row.get('id',''))[:8].upper()}"

# --------- filtros (topo da página) ---------
col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
with col_f1:
    f_nome = st.text_input("Nome")
with col_f2:
    f_predio = st.text_input("Prédio")
with col_f3:
    f_apto = st.text_input("Apto")

df = carregar_moradores(f_nome, f_predio, f_apto)

# --------- tabela sempre visível ---------
st.subheader("Lista de moradores")
if df.empty:
    st.info("Nenhum morador encontrado com os filtros atuais.")
else:
    df_view = df.rename(
        columns={
            "nome": "Nome",
            "telefone": "Telefone",
            "predio": "Prédio",
            "apto": "Apto",
        }
    )
    cols_order = ["Nome", "Telefone", "Prédio", "Apto"]
    st.dataframe(
        df_view[cols_order],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Nome": st.column_config.TextColumn("Nome"),
            "Telefone": st.column_config.TextColumn("Telefone"),
            "Prédio": st.column_config.TextColumn("Prédio"),
            "Apto": st.column_config.TextColumn("Apto"),
        },
    )

st.divider()

# --------- CRUD no expander ---------
with st.expander("Gerenciar moradores", expanded=False):
    tab_add, tab_edit = st.tabs(["➕ Adicionar", "✏️ Editar/Excluir"])

    # --- Adicionar ---
    with tab_add:
        with st.form("form_add_morador"):
            nome = st.text_input("Nome", max_chars=200)
            telefone = st.text_input("Telefone", max_chars=30, placeholder="(opcional)")
            predio = st.text_input("Prédio", max_chars=30)
            apto = st.text_input("Apto", max_chars=30)

            salvar = st.form_submit_button("Salvar morador", type="primary")

        if salvar:
            if not nome.strip():
                st.error("Informe o nome.")
            elif not predio.strip() or not apto.strip():
                st.error("Informe o prédio e o apartamento.")
            else:
                payload = {
                    "nome": nome.strip(),
                    "telefone": telefone.strip() if telefone else None,
                    "predio": predio.strip(),
                    "apto": apto.strip(),
                }
                try:
                    table("moradores").insert(payload).execute()
                    st.success("Morador adicionado.")
                except Exception as e:
                    st.error("Não foi possível adicionar o morador.")
                    st.exception(e)

    # --- Editar/Excluir ---
    with tab_edit:
        # Estado: nenhum morador selecionado por padrão
        if "edit_morador_id" not in st.session_state:
            st.session_state.edit_morador_id = None

        # Campo de busca (somente nome)
        termo = st.text_input("Buscar por nome (digite parte do nome)", key="busca_edit_nome")

        # Se ninguém selecionado, exibe resultados clicáveis
        if st.session_state.edit_morador_id is None:
            if termo and termo.strip():
                df_filtrado = df[df["nome"].str.contains(termo.strip(), case=False, na=False)]
            else:
                df_filtrado = df

            if df_filtrado.empty:
                st.info("Digite um nome para pesquisar e clique no morador para editar.")
            else:
                st.caption(f"{len(df_filtrado)} resultado(s) — clique no nome para editar (mostrando até 50).")
                for _, r in df_filtrado.head(50).iterrows():
                    label = label_morador(r.to_dict())
                    if st.button(label, key=f"pick_{r['id']}", use_container_width=True):
                        st.session_state.edit_morador_id = r["id"]
                        st.rerun()  # rerender com o formulário aberto
        else:
            # Busca o registro atual, mesmo que os filtros do topo o ocultem
            sel_id = st.session_state.edit_morador_id
            atual_df = df[df["id"] == sel_id]
            if atual_df.empty:
                try:
                    res = table("moradores").select("id,nome,telefone,predio,apto").eq("id", sel_id).execute()
                    dados = res.data or []
                    atual = dados[0] if dados else None
                except Exception:
                    atual = None
            else:
                atual = atual_df.iloc[0].to_dict()

            if not atual:
                st.warning("Morador não encontrado. Selecione novamente nos resultados.")
                st.session_state.edit_morador_id = None
            else:
                st.markdown(f"**Editando:** {label_morador(atual)}")

                with st.form("form_edit_morador"):
                    nome_e = st.text_input("Nome", value=str(atual.get("nome","")), max_chars=200)
                    telefone_e = st.text_input("Telefone", value=str(atual.get("telefone","") or ""), max_chars=30)
                    predio_e = st.text_input("Prédio", value=str(atual.get("predio","")), max_chars=30)
                    apto_e = st.text_input("Apto", value=str(atual.get("apto","")), max_chars=30)

                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        salvar_e = st.form_submit_button("Salvar alterações", type="primary")
                    with col2:
                        excluir_e = st.form_submit_button("Excluir", type="secondary")
                    with col3:
                        cancelar_e = st.form_submit_button("Cancelar edição")

                if salvar_e:
                    if not nome_e.strip():
                        st.error("Informe o nome.")
                    elif not predio_e.strip() or not apto_e.strip():
                        st.error("Informe o prédio e o apartamento.")
                    else:
                        payload = {
                            "nome": nome_e.strip(),
                            "telefone": telefone_e.strip() if telefone_e else None,
                            "predio": predio_e.strip(),
                            "apto": apto_e.strip(),
                        }
                        try:
                            table("moradores").update(payload).eq("id", sel_id).execute()
                            st.success("Morador atualizado.")
                        except Exception as e:
                            st.error("Não foi possível atualizar o morador.")
                            st.exception(e)

                if excluir_e:
                    try:
                        table("moradores").delete().eq("id", sel_id).execute()
                        st.success("Morador excluído.")
                        st.session_state.edit_morador_id = None
                        st.rerun()
                    except Exception as e:
                        st.error("Não foi possível excluir o morador.")
                        st.exception(e)

                if cancelar_e:
                    st.session_state.edit_morador_id = None
                    st.rerun()
