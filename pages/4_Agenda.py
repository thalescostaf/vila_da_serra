# pages/4_Agenda.py
import streamlit as st
import pandas as pd
from datetime import datetime
from src.supabase_client import table
from src.ui import back_home, require_auth
from streamlit_calendar import calendar

st.set_page_config(page_title="Agenda", page_icon="🗓️", layout="wide")

# exige login e aplica token
user = require_auth()

# voltar para home
back_home()

st.title("🗓️ Agenda")

# ---------- dados ----------
def carregar_moradores_map():
    res = table("moradores").select("id,nome,predio,apto").order("nome").execute()
    dados = res.data or []
    return {m["id"]: f"{m.get('nome','')} — Prédio {m.get('predio','')}, Apto {m.get('apto','')}" for m in dados}

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
# -> Usamos 'multiMonthYear' (grade anual 12 meses) com navegação anual
calendar_options = {
    "initialView": "dayGridMonth",
    "locale": "pt-br",
    "height": 720,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "multiMonthYear,dayGridMonth,timeGridWeek,timeGridDay",
    },
    # Traduções dos botões
    "buttonText": {
        "today": "Hoje",
        "multiMonthYear": "Ano",
        "month": "Mês",
        "week": "Semana",
        "day": "Dia",
    },
    # Configura a visão anual (12 meses em grade) e faz as setas mudarem 1 ano
    "views": {
        "multiMonthYear": {
            "type": "multiMonth",               # usa o plugin MultiMonth
            "duration": {"years": 1},           # mostra 1 ano completo
            "dateIncrement": {"years": 1},      # prev/next mudam 1 ano
            "multiMonthMaxColumns": 3,          # 3 colunas x 4 linhas = 12 meses
        }
    },
    "weekNumbers": False,
    "navLinks": True,
    "editable": False,
    "selectable": True,     # para criar itens via seleção/clique
    "selectMirror": True,
    "dayMaxEventRows": True,
}

# renderiza e captura interações
result = calendar(events=events, options=calendar_options)

# feedback visual ao clicar em um evento existente
if result and result.get("eventClick"):
    ev = result["eventClick"]["event"]
    ext = ev.get("_def", {}).get("extendedProps", {})
    st.info(
        f"**{ev.get('title','')}**\n\n"
        f"Status: {ext.get('status','—')}\n\n"
        f"Morador: {ext.get('morador','—')}\n\n"
        f"Descrição: {ext.get('descricao','—')}"
    )

# captura de data via clique/seleção para criar novos itens
selected_date_iso = None
if result and result.get("dateClick"):
    selected_date_iso = result["dateClick"]["dateStr"]  # "YYYY-MM-DD"
elif result and result.get("select"):
    selected_date_iso = result["select"]["startStr"]    # "YYYY-MM-DD"

def fmt_br(yyyy_mm_dd: str | None) -> str:
    if not yyyy_mm_dd:
        return ""
    try:
        d = datetime.strptime(yyyy_mm_dd[:10], "%Y-%m-%d").date()
        return d.strftime("%d/%m/%Y")
    except Exception:
        return yyyy_mm_dd or ""

# Formulários de criação (Ocorrência / Tarefa) ao selecionar uma data
if selected_date_iso:
    st.divider()
    st.subheader(f"Novo item em {fmt_br(selected_date_iso)}")

    tab_occ, tab_task = st.tabs(["➕ Ocorrência", "🧹 Tarefa (empregados)"])

    # -------- Criar Ocorrência --------
    with tab_occ:
        with st.form("form_nova_ocorrencia_agenda"):
            titulo = st.text_input("Título da ocorrência", max_chars=150)
            descricao = st.text_area("Descrição", height=120)
            status = st.selectbox("Status", ["aberta", "em_andamento", "finalizada"], index=0)
            st.write(f"Data do evento: **{fmt_br(selected_date_iso)}**")
            salvar_occ = st.form_submit_button("Salvar ocorrência", type="primary")

        if salvar_occ:
            if not titulo.strip():
                st.error("Informe um título.")
            else:
                payload = {
                    "titulo": titulo.strip(),
                    "descricao": descricao.strip() if descricao else None,
                    "status": status,
                    "data_evento": selected_date_iso,  # ISO YYYY-MM-DD
                }
                try:
                    table("ocorrencias").insert(payload).execute()
                    st.success("Ocorrência criada.")
                except Exception as e:
                    st.error("Falha ao criar ocorrência.")
                    st.exception(e)

    # -------- Criar Tarefa (agenda_eventos) --------
    with tab_task:
        df_all_occ = df_all_occ if not df_all_occ.empty else pd.DataFrame()
        occ_labels = ["— Sem vínculo —"]
        occ_ids = [None]
        if not df_all_occ.empty:
            for _, r in df_all_occ.iterrows():
                label = f"{(r.get('data_evento') or '')} — {r.get('status','')} — {r.get('titulo','(sem título)')} — #{str(r.get('id',''))[:8].upper()}"
                occ_labels.append(label)
                occ_ids.append(r.get("id"))

        with st.form("form_nova_tarefa_agenda"):
            titulo_ev = st.text_input("Título da tarefa", max_chars=150)
            descricao_ev = st.text_area("Descrição", height=120)
            i_occ = st.selectbox("Vincular a ocorrência (opcional)", occ_labels, index=0)
            ocorrencia_id = occ_ids[occ_labels.index(i_occ)]
            st.write(f"Início (dia inteiro): **{fmt_br(selected_date_iso)}**")
            salvar_ev = st.form_submit_button("Salvar tarefa", type="primary")

        if salvar_ev:
            if not titulo_ev.strip():
                st.error("Informe um título.")
            else:
                inicio_ts = f"{selected_date_iso}T00:00:00Z"  # all-day
                payload = {
                    "titulo": titulo_ev.strip(),
                    "descricao": descricao_ev.strip() if descricao_ev else None,
                    "inicio": inicio_ts,
                    "fim": None,
                    "ocorrencia_id": ocorrencia_id,
                }
                try:
                    table("agenda_eventos").insert(payload).execute()
                    st.success("Tarefa criada.")
                except Exception as e:
                    st.error("Falha ao criar tarefa.")
                    st.exception(e)
