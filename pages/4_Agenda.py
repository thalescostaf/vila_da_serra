# pages/4_Agenda.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from src.supabase_client import table
from src.ui import back_home, require_auth

st.set_page_config(page_title="Agenda", page_icon="🗓️", layout="wide")

# exige login e aplica token
user = require_auth()

# voltar para home
back_home()

st.title("🗓️ Agenda")

# ---- componente de calendário ----
try:
    from streamlit_calendar import calendar  # type: ignore
except Exception:
    st.error(
        "Para exibir o calendário, instale e use o ambiente do projeto:\n\n"
        "1) `poetry add streamlit-calendar`\n"
        "2) Rode o app com `poetry run streamlit run app.py`\n"
        "3) No editor (ex.: VS Code), selecione o interpretador da venv do projeto (.venv)"
    )
    st.stop()

# ---------- utilitários ----------
def fmt_br(yyyy_mm_dd: str | None) -> str:
    if not yyyy_mm_dd:
        return ""
    try:
        d = datetime.strptime(yyyy_mm_dd[:10], "%Y-%m-%d").date()
        return d.strftime("%d/%m/%Y")
    except Exception:
        return yyyy_mm_dd or ""

def parse_iso_date(s: str | None) -> date:
    if not s:
        return date.today()
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return date.today()

# ---------- dados ----------
def carregar_moradores():
    res = table("moradores").select("id,nome,predio,apto").order("nome").execute()
    dados = res.data or []
    # opções para formulário
    opcoes = [("— Sem vínculo —", None)]
    for m in dados:
        rotulo = f"{m.get('nome','')} — Prédio {m.get('predio','')}, Apto {m.get('apto','')}"
        opcoes.append((rotulo, m.get("id")))
    # mapa para exibição
    mapa = {m["id"]: f"{m.get('nome','')} — Prédio {m.get('predio','')}, Apto {m.get('apto','')}" for m in dados}
    return opcoes, mapa

def carregar_ocorrencias_com_data():
    res = (
        table("ocorrencias")
        .select("id,titulo,descricao,status,morador_id,data_evento")
        .order("data_evento")
        .limit(2000)
        .execute()
    )
    df = pd.DataFrame(res.data or [])
    if df.empty or "data_evento" not in df.columns:
        return pd.DataFrame([])
    return df.dropna(subset=["data_evento"])

moradores_opcoes, moradores_map = carregar_moradores()
df = carregar_ocorrencias_com_data()

STATUS_COLORS = {
    "aberta": "#f8d7da",        # vermelho suave
    "em_andamento": "#fff3cd",  # amarelo/laranja suave
    "finalizada": "#d4edda",    # verde suave
}

# monta eventos para o FullCalendar a partir das ocorrências
events = []
if not df.empty:
    for _, r in df.iterrows():
        titulo = r.get("titulo") or "(Sem título)"
        status = r.get("status") or "aberta"
        morador = moradores_map.get(r.get("morador_id")) if r.get("morador_id") else "—"
        desc = r.get("descricao") or ""
        data_iso = str(r.get("data_evento"))  # "YYYY-MM-DD"

        events.append(
            {
                "id": r.get("id"),
                "title": titulo,
                "start": data_iso,   # dia inteiro
                "allDay": True,
                "color": STATUS_COLORS.get(status, "#e9ecef"),
                "extendedProps": {
                    "status": status,
                    "morador": morador,
                    "descricao": desc,
                },
            }
        )

# opções do calendário: PT-BR + botões ordenados (ANO, MÊS, SEMANA, DIA)
# 'multiMonthYear' = grade anual (12 meses) com navegação anual
calendar_options = {
    "initialView": "dayGridMonth",
    "locale": "pt-br",
    "height": 720,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "multiMonthYear,dayGridMonth,timeGridWeek,timeGridDay",
    },
    "buttonText": {
        "today": "Hoje",
        "multiMonthYear": "Ano",
        "month": "Mês",
        "week": "Semana",
        "day": "Dia",
    },
    "views": {
        "multiMonthYear": {
            "type": "multiMonth",
            "duration": {"years": 1},       # mostra 1 ano
            "dateIncrement": {"years": 1},  # setas mudam 1 ano
            "multiMonthMaxColumns": 3,      # 3 col x 4 lin = 12 meses
        }
    },
    "weekNumbers": False,
    "navLinks": True,
    "editable": False,
    "selectable": True,     # criar por seleção/clique
    "selectMirror": True,
    "dayMaxEventRows": True,
}

# render e interações
result = calendar(events=events, options=calendar_options)

# feedback ao clicar em evento existente
if result and result.get("eventClick"):
    ev = result["eventClick"]["event"]
    ext = ev.get("_def", {}).get("extendedProps", {})
    st.info(
        f"**{ev.get('title','')}**\n\n"
        f"Status: {ext.get('status','—')}\n\n"
        f"Morador: {ext.get('morador','—')}\n\n"
        f"Descrição: {ext.get('descricao','—')}"
    )

# data selecionada/clicada (para pré-preencher o formulário de nova ocorrência)
selected_date_iso: str | None = None
if result and result.get("dateClick"):
    selected_date_iso = result["dateClick"]["dateStr"]  # "YYYY-MM-DD"
elif result and result.get("select"):
    selected_date_iso = result["select"]["startStr"]    # "YYYY-MM-DD"

# ------ botão + expander para NOVA OCORRÊNCIA ------
default_date = parse_iso_date(selected_date_iso)

col_btn, _ = st.columns([1, 3])
with col_btn:
    open_occ = st.button("➕ Nova Ocorrência", use_container_width=True)

if "agenda_create_open" not in st.session_state:
    st.session_state.agenda_create_open = False

# abre o expander automaticamente se clicou no botão ou se selecionou uma data
if open_occ or selected_date_iso:
    st.session_state.agenda_create_open = True

with st.expander("Criar ocorrência", expanded=st.session_state.agenda_create_open):
    with st.form("form_nova_ocorrencia_agenda"):
        titulo = st.text_input("Título da ocorrência", max_chars=150)
        descricao = st.text_area("Descrição", height=120)
        status = st.selectbox("Status", ["aberta", "em_andamento", "finalizada"], index=0)

        # morador (opcional)
        rotulos, valores = zip(*moradores_opcoes)
        morador_escolha = st.selectbox("Morador (opcional)", rotulos, index=0)
        morador_id = valores[rotulos.index(morador_escolha)]

        data_evt = st.date_input("Data do evento", value=default_date)
        salvar_occ = st.form_submit_button("Salvar ocorrência", type="primary")

    if salvar_occ:
        if not titulo.strip():
            st.error("Informe um título.")
        else:
            payload = {
                "titulo": titulo.strip(),
                "descricao": descricao.strip() if descricao else None,
                "status": status,
                "data_evento": data_evt.isoformat(),  # ISO YYYY-MM-DD
                "morador_id": morador_id,
            }
            try:
                table("ocorrencias").insert(payload).execute()
                st.success(f"Ocorrência criada para {fmt_br(data_evt.isoformat())}.")
                st.session_state.agenda_create_open = False
            except Exception as e:
                st.error("Falha ao criar ocorrência.")
                st.exception(e)
