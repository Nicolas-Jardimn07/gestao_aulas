"""Utilidades compartilhadas por todas as páginas do app."""
import os
import uuid
from datetime import datetime, date as date_cls

import streamlit as st

import db

BRAND_ICON_SVG = """<svg width="44" height="44" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="23" cy="35" r="15.5" stroke="#7C4E22" stroke-width="3"/><circle cx="23" cy="35" r="5" fill="#7C4E22" opacity="0.9"/><line x1="23" y1="19.5" x2="53" y2="11" stroke="#7C4E22" stroke-width="3" stroke-linecap="round"/><path d="M3 47 Q 19 37, 35 47 T 67 47" stroke="#4F7C8B" stroke-width="3" stroke-linecap="round" fill="none"/></svg>"""

BRAND_ICON_SVG_LIGHT = """<svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="23" cy="35" r="15.5" stroke="#F3EBDD" stroke-width="3"/><circle cx="23" cy="35" r="5" fill="#F3EBDD" opacity="0.9"/><line x1="23" y1="19.5" x2="53" y2="11" stroke="#F3EBDD" stroke-width="3" stroke-linecap="round"/><path d="M3 47 Q 19 37, 35 47 T 67 47" stroke="#9FC4D2" stroke-width="3" stroke-linecap="round" fill="none"/></svg>"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

:root{
  --paper:#F7F5F0; --paper-deep:#EAE1CC; --panel:#FFFFFF;
  --ink:#2A1F14; --ink-soft:#5B4A38; --ink-faint:#8C7A60;
  --terra:#8A5A30; --terra-deep:#5C3A1E;
  --river:#4F7C8B; --river-deep:#375B67;
  --gold:#B8873F; --alert:#9E3F2E; --good:#4C6B3F; --line:#DCD0B4;
}
html, body, [class*="css"]  { font-family:'Inter', -apple-system, sans-serif; color: var(--ink); }
html, body { overflow-x: hidden; }
h1,h2,h3,h4 { font-family:'Poppins','Inter',sans-serif !important; color:var(--terra-deep) !important; font-weight:700 !important; letter-spacing:-0.2px; }
h1{ border-bottom:3px solid var(--terra-deep); padding-bottom:10px; margin-bottom:18px !important; }

.stApp { background: var(--paper); }
[data-testid="stHeader"] { background: transparent; }

/* sidebar */
[data-testid="stSidebar"] { background: var(--terra-deep); border-right: 1px solid var(--line); }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] { color: #F3EBDD !important; }
[data-testid="stSidebarNav"] { padding-top: 6px; }
[data-testid="stSidebarNav"] li div a { border-radius: 6px !important; font-weight:600 !important; }
[data-testid="stSidebarNav"] li div a:hover { background: rgba(255,255,255,0.12) !important; }
[data-testid="stSidebarNav"] li div[aria-selected="true"] a,
[data-testid="stSidebarNav"] li div a[aria-current="page"] { background: var(--terra) !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.25) !important; }
.sb-identity { padding:2px 0 14px 0; border-bottom:1px solid rgba(255,255,255,0.25); margin-bottom:12px; }
.sb-identity .sb-name { color:#FFFFFF !important; font-weight:700; font-size:15px; }
.sb-identity .sb-role { color:#E7C99A !important; font-size:12px; font-weight:700; margin-top:2px; letter-spacing:0.3px; }

/* botões */
.stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {
  background: var(--terra-deep) !important; color:#fff !important; border:1px solid var(--terra-deep) !important;
  border-radius: 6px !important; font-weight:600 !important; padding: 0.5rem 1.1rem !important;
}
.stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover {
  background: var(--terra) !important; border-color:var(--terra) !important;
}
[data-testid="stSidebar"] .stButton>button { background:#F3EBDD !important; color:var(--terra-deep) !important; border-color:#F3EBDD !important; }
[data-testid="stSidebar"] .stButton>button p,
[data-testid="stSidebar"] .stButton>button span,
[data-testid="stSidebar"] .stButton>button div { color:var(--terra-deep) !important; }

/* cartões / containers com borda */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--panel); border: 1px solid var(--line) !important; border-radius: 10px !important;
  padding: 4px 6px; box-shadow: 0 6px 18px -10px rgba(58,36,16,0.28);
}

/* métricas */
[data-testid="stMetric"] {
  background: var(--panel); border: 1px solid var(--line); border-top: 4px solid var(--terra-deep);
  border-radius: 6px; padding: 14px 16px 10px 16px;
}
[data-testid="stMetricLabel"] { color: var(--ink-soft) !important; font-weight:600 !important; }
[data-testid="stMetricValue"] { color: var(--terra-deep) !important; font-family:'Poppins',sans-serif !important; }

/* abas */
button[data-baseweb="tab"] { font-weight:600 !important; color:var(--ink-soft) !important; }
button[data-baseweb="tab"][aria-selected="true"] { color:var(--terra-deep) !important; border-bottom-color:var(--terra-deep) !important; }

/* tabelas */
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 6px; }

/* progress bar */
.stProgress > div > div > div { background-color: var(--terra-deep) !important; }

/* badges customizados */
.badge{ display:inline-block; padding:3px 11px; border-radius:4px; font-size:12px; font-weight:800; border:1px solid transparent; }
.badge.ok{ background:rgba(76,107,63,0.16); color:var(--good); border-color:rgba(76,107,63,0.35); }
.badge.warn{ background:rgba(158,63,46,0.14); color:var(--alert); border-color:rgba(158,63,46,0.35); }
.badge.muted{ background:rgba(42,31,20,0.08); color:var(--ink-soft); border-color:rgba(42,31,20,0.2); }
.badge.river{ background:rgba(55,91,103,0.15); color:var(--river-deep); border-color:rgba(55,91,103,0.35); }

.acl-card{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px 18px; margin-bottom:14px; }
.acl-card.accent{ border-left:4px solid var(--terra-deep); }
.acl-card.accent-river{ border-left:4px solid var(--river-deep); }
hr{ border-color: var(--line) !important; }

/* ---- landing / hero de login ---- */
.login-hero{
  width:100vw; position:relative; left:50%; right:50%; margin-left:-50vw; margin-right:-50vw;
  background:linear-gradient(135deg, #6E4423 0%, #4A2E17 65%, #3A2410 100%);
  padding:56px 24px 78px 24px; text-align:center; overflow:hidden; margin-top:-16px;
}
.login-hero::before{
  content:""; position:absolute; inset:0;
  background-image:radial-gradient(circle at 12% 20%, rgba(255,255,255,0.06) 0, transparent 40%),
                    radial-gradient(circle at 88% 75%, rgba(159,196,210,0.10) 0, transparent 45%);
  pointer-events:none;
}
.login-hero-inner{ position:relative; z-index:1; }
.login-hero h1{
  color:#FBF6EC !important; border:none !important; padding-bottom:0 !important; margin:14px 0 6px 0 !important;
  font-size:34px !important; letter-spacing:-0.3px;
}
.login-hero .tagline{ color:#9FC4D2; font-weight:700; font-size:14.5px; letter-spacing:0.3px; }
.login-hero .subtitle{ color:#D8C6AC; font-size:13px; margin-top:10px; max-width:520px; margin-left:auto; margin-right:auto; }
.login-hero-wave{ position:absolute; left:0; right:0; bottom:-1px; line-height:0; z-index:1; }

.login-card-anchor{ margin-top:-14px; }

/* ---- espaçamentos gerais ---- */
.block-container{ padding-top: 3rem !important; }

/* ---- responsivo (celular) ---- */
@media (max-width: 640px){
  .block-container{ padding-top: 1.6rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
  .login-hero{ padding: 34px 16px 52px 16px; margin-top:-8px; }
  .login-hero h1{ font-size: 23px !important; line-height:1.25; }
  .login-hero .tagline{ font-size:12.5px; }
  .login-hero .subtitle{ font-size:12px; }
  .login-hero-inner svg{ width:44px; height:44px; }
  .login-card-anchor{ margin-top:-10px; }
  h1{ font-size:22px !important; }
  h2{ font-size:17px !important; }
}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def raw_html(text):
    """Renderiza um bloco de HTML sem deixar a indentação do Python virar bloco de código no Markdown."""
    cleaned = "\n".join(line.strip() for line in text.strip("\n").split("\n"))
    st.markdown(cleaned, unsafe_allow_html=True)


def brand_header(config_name="Acordes de Lagoinha: Sons da Terra", community="Comunidade Quilombola de Lagoinha — Berilo/MG"):
    raw_html(f"""
    <div style="text-align:center;margin-bottom:6px;">
    {BRAND_ICON_SVG}
    <h1 style="border:none;margin-bottom:0;padding-bottom:0;">{config_name}</h1>
    <p style="color:var(--river-deep);font-weight:600;margin-top:2px;">{community}</p>
    </div>
    """)


def login_hero(config_name="Acordes de Lagoinha: Sons da Terra", community="Comunidade Quilombola de Lagoinha — Berilo/MG"):
    raw_html(f"""
    <div class="login-hero">
    <div class="login-hero-inner">
    {BRAND_ICON_SVG_LIGHT}
    <h1>{config_name}</h1>
    <div class="tagline">{community}</div>
    <div class="subtitle">Ferramenta interna de gestão de evidências, frequência e auditoria pedagógica — PNAB Berilo/MG.</div>
    </div>
    <svg class="login-hero-wave" viewBox="0 0 1440 60" preserveAspectRatio="none" style="width:100%;height:44px;">
    <path d="M0 30 Q 180 5, 360 30 T 720 30 T 1080 30 T 1440 30 V60 H0 Z" fill="#F7F5F0"/>
    </svg>
    </div>
    <div class="login-card-anchor"></div>
    """)


def require_login():
    """Garante que existe um usuário logado; senão avisa e para a execução."""
    if not st.session_state.get("user"):
        st.warning("Sua sessão expirou. Recarregue a página para entrar novamente.")
        st.stop()
    user = st.session_state["user"]
    with st.sidebar:
        role_label = "Gestor(a) / Auditor" if user["role"] == "gestor" else "Professor(a)"
        raw_html(f"""
        <div class="sb-identity">
        <div class="sb-name">{user['name']}</div>
        <div class="sb-role">{role_label}</div>
        </div>
        """)
        if st.button("Sair", use_container_width=True, key="logout_btn_sidebar"):
            st.session_state["user"] = None
            st.session_state["login_account_id"] = None
            st.rerun()
    return user


def turma_switcher(user, allow_create_hint=True):
    """Mostra o seletor de turma ativa na sidebar e retorna a turma (dict) escolhida."""
    if user["role"] == "gestor":
        turmas = db.get_turmas()
    else:
        turmas = db.get_turmas_for_account(user["id"])

    if not turmas:
        st.info(
            "Nenhuma turma disponível ainda. "
            + ("Crie uma turma na página Turmas." if user["role"] == "gestor" and allow_create_hint
               else "Peça ao gestor(a) para vincular você a uma turma.")
        )
        st.stop()

    options = {t["id"]: t["name"] for t in turmas}
    current = st.session_state.get("current_turma_id")
    if current not in options:
        current = list(options.keys())[0]

    with st.sidebar:
        st.markdown("---")
        chosen = st.selectbox(
            "Turma ativa",
            options.keys(),
            format_func=lambda k: options[k],
            index=list(options.keys()).index(current),
            key="turma_switcher_select",
        )
    st.session_state["current_turma_id"] = chosen
    return db.get_turma(chosen)


# ------------------------------------------------------------------ #
# Data / hora
# ------------------------------------------------------------------ #
def calc_hours(start_time, end_time):
    """start_time/end_time são objetos datetime.time."""
    s = start_time.hour * 60 + start_time.minute
    e = end_time.hour * 60 + end_time.minute
    mins = e - s
    if mins < 0:
        mins += 24 * 60
    return round(mins / 60, 2)


def fmt_date(d):
    if not d:
        return "—"
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(d)


def fmt_datetime(iso):
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return str(iso)

