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

# ---------- dados ----------
def carregar_moradores_map():
    res = table("moradores").select("id,nome,predio,apto").order("nome").execute()
    dados = res.data or []
    return {
        m["id"]: f"{m.get('nome','')} — Prédio {m.get('predio','')}, Apto {m.get('apto','')}"
        for m in dados
    }

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

def carregar_todas_ocorrencias():
    res = (
        table("ocorrencias")
        .select("id,titulo,status,data_evento")
        .order("created_at", desc=True)
        .limit(2000)
        .execute()
    )
    return pd.DataFrame(res.data or [])

moradores_map = carregar_moradores_map()
df = carregar_ocorrencias_com_data()
df_all_occ = carregar_todas_ocorrencias()

STATUS_COLORS = {
    "aberta": "#f8d7da",        # vermelho suave
    "em_andamento": "#fff3cd",  # amarelo/laranja suave
    "finalizada": "#d4edda",    # verde suave
}

# monta eventos para o FullCalendar
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

# data selecionada/clicada (para pré-preencher os formulários)
selected_date_iso: str | None = None
if result and result.get("dateClick"):
    selected_date_iso = result["dateClick"]["dateStr"]  # "YYYY-MM-DD"
elif result and result.get("select"):
    selected_date_iso = result["select"]["startStr"]    # "YYYY-MM-DD"

# ------ BOTÕES + EXPANDER COM ABAS (NOVOS ITENS) ------
default_date_iso = selected_date_iso or date.today().isoformat()

b1, b2, b3 = st.columns(3)
with b1:
    click_occ = st.button("➕ Nova Ocorrência", use_container_width=True)
with b2:
    click_task = st.button("🧹 Nova Tarefa", use_container_width=True)
with b3:
    click_event = st.button("📌 Novo Evento", use_container_width=True)

if "agenda_create_open" not in st.session_state:
    st.session_state.agenda_create_open = False
if "agenda_tab" not in st.session_state:
    st.session_state.agenda_tab = "occ"  # occ | task | event

if click_occ:
    st.session_state.agenda_create_open = True
    st.session_state.agenda_tab = "occ"
if click_task:
    st.session_state.agenda_create_open = True
    st.session_state.agenda_tab = "task"
if click_event:
    st.session_state.agenda_create_open = True
    st.session_state.agenda_tab = "event"

def _parse_iso_date(s: str) -> date:
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return date.today()

default_date = _parse_iso_date(default_date_iso)

tabs_all = [("occ", "➕ Ocorrência"), ("task", "🧹 Tarefa"), ("event", "📌 Novo Evento")]
first = st.session_state.agenda_tab
ordered = [t for t in tabs_all if t[0] == first] + [t for t in tabs_all if t[0] != first]
labels = [lbl for _, lbl in ordered]

with st.expander("Criar item", expanded=st.session_state.agenda_create_open):
    t_objs = st.tabs(labels)
    tab_map = {ordered[i][0]: t_objs[i] for i in range(len(ordered))}

    # --- Aba: Ocorrência ---
    with tab_map["occ"]:
        with st.form("form_nova_ocorrencia_botoes"):
            titulo = st.text_input("Título da ocorrência", max_chars=150)
            descricao = st.text_area("Descrição", height=120)
            status = st.selectbox("Status", ["aberta", "em_andamento", "finalizada"], index=0)
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
                }
                try:
                    table("ocorrencias").insert(payload).execute()
                    st.success(f"Ocorrência criada para {fmt_br(data_evt.isoformat())}.")
                    st.session_state.agenda_create_open = False
                except Exception as e:
                    st.error("Falha ao criar ocorrência.")
                    st.exception(e)

    # --- Aba: Tarefa (agenda_eventos) ---
    with tab_map["task"]:
        occ_labels = ["— Sem vínculo —"]
        occ_ids = [None]
        if not df_all_occ.empty:
            for _, r in df_all_occ.iterrows():
                label = f"{(r.get('data_evento') or '')} — {r.get('status','')} — {r.get('titulo','(sem título)')} — #{str(r.get('id',''))[:8].upper()}"
                occ_labels.append(label)
                occ_ids.append(r.get("id"))

        with st.form("form_nova_tarefa_botoes"):
            titulo_t = st.text_input("Título da tarefa", max_chars=150)
            descricao_t = st.text_area("Descrição", height=120)
            i_occ = st.selectbox("Vincular a ocorrência (opcional)", occ_labels, index=0)
            ocorrencia_id = occ_ids[occ_labels.index(i_occ)]
            data_inicio = st.date_input("Data (início)", value=default_date)
            salvar_t = st.form_submit_button("Salvar tarefa", type="primary")

        if salvar_t:
            if not titulo_t.strip():
                st.error("Informe um título.")
            else:
                inicio_ts = f"{data_inicio.isoformat()}T00:00:00Z"  # all-day
                payload = {
                    "titulo": titulo_t.strip(),
                    "descricao": descricao_t.strip() if descricao_t else None,
                    "inicio": inicio_ts,
                    "fim": None,
                    "ocorrencia_id": ocorrencia_id,
                }
                try:
                    table("agenda_eventos").insert(payload).execute()
                    st.success(f"Tarefa criada para {fmt_br(data_inicio.isoformat())}.")
                    st.session_state.agenda_create_open = False
                except Exception as e:
                    st.error("Falha ao criar tarefa.")
                    st.exception(e)

    # --- Aba: Evento (geral em agenda_eventos) ---
    with tab_map["event"]:
        with st.form("form_novo_evento_botoes"):
            titulo_e = st.text_input("Título do evento", max_chars=150)
            descricao_e = st.text_area("Descrição", height=120)
            all_day = st.checkbox("Dia inteiro", value=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                data_ini = st.date_input("Início", value=default_date)
            with col_d2:
                data_fim = st.date_input("Fim (opcional)", value=default_date)

            salvar_e = st.form_submit_button("Salvar evento", type="primary")

        if salvar_e:
            if not titulo_e.strip():
                st.error("Informe um título.")
            else:
                # Simples: mantemos horários 00:00–23:59 em all_day
                inicio_ts = f"{data_ini.isoformat()}T00:00:00Z" if all_day else f"{data_ini.isoformat()}T00:00:00Z"
                fim_ts = None
                if data_fim and data_fim >= data_ini:
                    fim_ts = f"{data_fim.isoformat()}T23:59:59Z" if all_day else f"{data_fim.isoformat()}T23:59:59Z"

                payload = {
                    "titulo": titulo_e.strip(),
                    "descricao": descricao_e.strip() if descricao_e else None,
                    "inicio": inicio_ts,
                    "fim": fim_ts,
                    "ocorrencia_id": None,
                }
                try:
                    table("agenda_eventos").insert(payload).execute()
                    st.success("Evento criado.")
                    st.session_state.agenda_create_open = False
                except Exception as e:
                    st.error("Falha ao criar evento.")
                    st.exception(e)
