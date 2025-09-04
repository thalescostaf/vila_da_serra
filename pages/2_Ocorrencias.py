# pages/2_Ocorrencias.py
import streamlit as st
import pandas as pd
from datetime import date, datetime
from src.supabase_client import table
from src.ui import back_home, require_auth

st.set_page_config(page_title="Ocorrências", page_icon="📝", layout="wide")

# Exige login e aplica token de sessão ao PostgREST
require_auth()

# Botão voltar para Home
back_home()

st.title("📝 Ocorrências")

STATUS_OPCOES = ["aberta", "em_andamento", "finalizada"]

# ---------- utilitários ----------
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

def status_badge(status: str):
    cores = {
        "aberta":       "#f8d7da",  # vermelho suave
        "em_andamento": "#fff3cd",  # amarelo/laranja suave
        "finalizada":   "#d4edda",  # verde suave
    }
    texto = {
        "aberta": "Aberta",
        "em_andamento": "Em andamento",
        "finalizada": "Finalizada",
    }.get(status, status)
    cor = cores.get(status, "#e9ecef")
    st.markdown(
        f"""<span style="
            background:{cor};
            padding:4px 10px;
            border-radius:999px;
            font-size:12px;
            border:1px solid rgba(0,0,0,0.05);
            display:inline-block;
        ">{texto}</span>""",
        unsafe_allow_html=True,
    )

def truncate(texto: str | None, max_chars: int = 240) -> str:
    if not texto:
        return "—"
    t = str(texto).strip()
    return t if len(t) <= max_chars else t[:max_chars].rstrip() + "..."

def short_id(uid: str | None):
    if not uid:
        return "#--------"
    return f"#{str(uid)[:8].upper()}"

# ---------- dados ----------
def carregar_moradores():
    res = table("moradores").select("id,nome,predio,apto").order("nome").execute()
    dados = res.data or []
    opcoes = [("— Sem vínculo —", None)]
    for m in dados:
        rotulo = f"{m.get('nome','')} — Prédio {m.get('predio','')}, Apto {m.get('apto','')}"
        opcoes.append((rotulo, m.get("id")))
    return dados, opcoes

def carregar_ocorrencias():
    res = (
        table("ocorrencias")
        .select("id,titulo,descricao,status,morador_id,data_evento,created_at")
        .order("created_at", desc=True)
        .limit(500)
        .execute()
    )
    dados = res.data or []
    return pd.DataFrame(dados)

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

moradores_raw, moradores_opcoes = carregar_moradores()
df = carregar_ocorrencias()

# Mapa id->rótulo para solicitante
mapa_morador = {m["id"]: f"{m.get('nome','')} — Prédio {m.get('predio','')}, Apto {m.get('apto','')}" for m in moradores_raw}

def rotulo_morador(mid):
    if not mid:
        return "—"
    return mapa_morador.get(mid, "—")

# ---------- filtros ----------
col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    filtro_status = st.selectbox("Filtrar status", ["Todos"] + STATUS_OPCOES, index=0)
with col_f2:
    busca = st.text_input("Buscar por título/descrição")

df_view = df.copy()
if not df_view.empty:
    if filtro_status != "Todos":
        df_view = df_view[df_view["status"] == filtro_status]
    if busca.strip():
        termo = busca.strip().lower()
        df_view = df_view[
            df_view["titulo"].str.lower().str.contains(termo, na=False)
            | df_view["descricao"].str.lower().str.contains(termo, na=False)
        ]

# ---------- cards ----------
def card_visualizacao(row):
    with st.container(border=True):
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            status_badge(row.get("status", "aberta"))
            st.markdown(f"### {row.get('titulo','(sem título)')}")
            st.caption(f"Solicitante: {rotulo_morador(row.get('morador_id'))}")
        with c2:
            st.write(short_id(row.get("id")))
            st.caption(f"Abertura: {fmt_data_ddmmaaaa(row.get('created_at'))}")

        # Resumo sempre visível
        st.markdown(f"**Resumo:** {truncate(row.get('descricao'))}")

        # Detalhes opcionais
        with st.expander("Ver mais", expanded=False):
            data_evt = fmt_data_ddmmaaaa(row.get("data_evento"))
            st.markdown(f"**Data do evento:** {data_evt or '—'}")
            desc_full = row.get("descricao") or "—"
            st.markdown(f"**Descrição completa:** {desc_full}")

        # Botão Editar por último
        if st.button("✏️ Editar", key=f"edit_{row['id']}", use_container_width=True):
            st.session_state.edit_id = row["id"]

def card_edicao(row):
    with st.container(border=True):
        st.markdown(f"### Editando {short_id(row.get('id'))}")

        with st.form(f"form_edit_{row['id']}"):
            titulo = st.text_input("Título", value=row.get("titulo",""), max_chars=150)
            descricao = st.text_area("Descrição", value=row.get("descricao",""), height=120)

            idx_status = STATUS_OPCOES.index(row.get("status","aberta")) if row.get("status") in STATUS_OPCOES else 0
            status = st.selectbox("Status", STATUS_OPCOES, index=idx_status)

            rotulos, valores = zip(*moradores_opcoes)
            mid_atual = row.get("morador_id", None)
            try:
                idx_m = valores.index(mid_atual)
            except ValueError:
                idx_m = 0
            morador_escolha = st.selectbox("Morador (opcional)", rotulos, index=idx_m)
            morador_id = valores[rotulos.index(morador_escolha)]

            data_raw = row.get("data_evento")
            if data_raw:
                try:
                    y, m, d = map(int, str(data_raw).split("-"))
                    data_default = date(y, m, d)
                except Exception:
                    data_default = None
            else:
                data_default = None
            data_evt = st.date_input("Data do evento (opcional)", value=data_default)

            col1, col2, col3 = st.columns([1,1,6])
            with col1:
                salvar = st.form_submit_button("Salvar", type="primary")
            with col2:
                cancelar = st.form_submit_button("Cancelar")
            with col3:
                excluir = st.form_submit_button("Excluir", type="secondary")

        if salvar:
            if not titulo.strip():
                st.error("Informe um título.")
            else:
                payload = {
                    "titulo": titulo.strip(),
                    "descricao": descricao.strip() if descricao else None,
                    "status": status,
                    "morador_id": morador_id,
                    "data_evento": data_evt.isoformat() if isinstance(data_evt, date) else None,
                }
                try:
                    table("ocorrencias").update(payload).eq("id", row["id"]).execute()
                    st.success("Ocorrência atualizada.")
                    st.session_state.edit_id = None
                except Exception as e:
                    st.error("Falha ao atualizar.")
                    st.exception(e)

        if cancelar:
            st.session_state.edit_id = None

        if excluir:
            try:
                table("ocorrencias").delete().eq("id", row["id"]).execute()
                st.success("Ocorrência excluída.")
                st.session_state.edit_id = None
            except Exception as e:
                st.error("Falha ao excluir.")
                st.exception(e)

# Listagem
if df_view.empty:
    st.info("Nenhuma ocorrência encontrada.")
else:
    for _, row in df_view.iterrows():
        if st.session_state.edit_id == row["id"]:
            card_edicao(row)
        else:
            card_visualizacao(row)

st.divider()

# ---------- criar nova ----------
with st.expander("Nova ocorrência"):
    with st.form("form_criar"):
        titulo = st.text_input("Título", max_chars=150)
        descricao = st.text_area("Descrição", height=120)
        status = st.selectbox("Status", STATUS_OPCOES, index=0)

        rotulos, valores = zip(*moradores_opcoes)
        morador_escolha = st.selectbox("Morador (opcional)", rotulos, index=0)
        morador_id = valores[rotulos.index(morador_escolha)]

        data_evt = st.date_input("Data do evento (opcional)", value=None)

        salvar = st.form_submit_button("Salvar ocorrência", type="primary")

    if salvar:
        if not titulo.strip():
            st.error("Informe um título.")
        else:
            payload = {
                "titulo": titulo.strip(),
                "descricao": descricao.strip() if descricao else None,
                "status": status,
                "morador_id": morador_id,
                "data_evento": data_evt.isoformat() if isinstance(data_evt, date) else None,
            }
            try:
                table("ocorrencias").insert(payload).execute()
                st.success("Ocorrência criada.")
            except Exception as e:
                st.error("Falha ao criar ocorrência.")
                st.exception(e)
