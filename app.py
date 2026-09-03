import streamlit as st

import db
import utils

st.set_page_config(page_title="Acordes de Lagoinha", layout="wide")
db.init_db()
utils.inject_css()

if "user" not in st.session_state:
    st.session_state.user = None
if "login_account_id" not in st.session_state:
    st.session_state.login_account_id = None
if "login_error" not in st.session_state:
    st.session_state.login_error = ""


def login_view():
    utils.login_hero()

    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        with st.container(border=True):
            accounts = db.get_accounts()
            acc = db.get_account(st.session_state.login_account_id) if st.session_state.login_account_id else None

            if not acc:
                st.markdown("##### Quem é você?")
                for a in accounts:
                    role_label = "Gestor(a) / Auditor" if a["role"] == "gestor" else "Professor(a)"
                    icon = ":material/admin_panel_settings:" if a["role"] == "gestor" else ":material/school:"
                    if st.button(f"{a['name']}  ·  {role_label}", key=f"pick_{a['id']}", use_container_width=True, icon=icon):
                        st.session_state.login_account_id = a["id"]
                        st.session_state.login_error = ""
                        st.rerun()

            elif not acc["pass_hash"]:
                st.markdown(f"##### Olá, **{acc['name']}**!")
                st.caption("Este é seu primeiro acesso — crie uma senha para entrar nas próximas vezes.")
                with st.form("create_pw_form"):
                    p1 = st.text_input("Criar senha (mín. 4 caracteres)", type="password")
                    p2 = st.text_input("Confirmar senha", type="password")
                    submitted = st.form_submit_button("Criar senha e entrar", use_container_width=True)
                if submitted:
                    if not p1 or len(p1) < 4:
                        st.session_state.login_error = "A senha precisa ter pelo menos 4 caracteres."
                    elif p1 != p2:
                        st.session_state.login_error = "As senhas não coincidem."
                    else:
                        db.set_password(acc["id"], p1)
                        st.session_state.user = {"id": acc["id"], "name": acc["name"], "role": acc["role"]}
                        db.log_action(None, acc["id"], acc["name"], acc["role"], "Criou a senha e entrou pela primeira vez")
                        st.session_state.login_account_id = None
                        st.session_state.login_error = ""
                        st.rerun()
                if st.session_state.login_error:
                    st.error(st.session_state.login_error)
                if st.button("Trocar de pessoa"):
                    st.session_state.login_account_id = None
                    st.rerun()

            else:
                st.markdown(f"##### Olá, **{acc['name']}**!")
                st.caption("Digite sua senha para entrar.")
                with st.form("enter_pw_form"):
                    pw = st.text_input("Senha", type="password")
                    submitted = st.form_submit_button("Entrar", use_container_width=True)
                if submitted:
                    if db.verify_login(acc["id"], pw):
                        st.session_state.user = {"id": acc["id"], "name": acc["name"], "role": acc["role"]}
                        db.log_action(None, acc["id"], acc["name"], acc["role"], "Entrou no sistema")
                        st.session_state.login_account_id = None
                        st.session_state.login_error = ""
                        st.rerun()
                    else:
                        st.session_state.login_error = "Senha incorreta."
                if st.session_state.login_error:
                    st.error(st.session_state.login_error)
                st.caption("Esqueceu a senha? Peça ao gestor(a) para redefinir seu acesso em Configurações.")
                if st.button("Trocar de pessoa"):
                    st.session_state.login_account_id = None
                    st.rerun()


# ------------------------------------------------------------------ #
# Navegação: o menu lateral só existe (e só mostra as páginas certas)
# depois que a pessoa está logada. Antes disso, fica escondido.
# ------------------------------------------------------------------ #
if not st.session_state.user:
    pg = st.navigation([st.Page(login_view, title="Login")], position="hidden")
    pg.run()
    st.stop()

user = st.session_state.user
pages = [
    st.Page("pages/1_Painel.py", title="Painel", default=True),
    st.Page("pages/2_Turmas.py", title="Turmas"),
    st.Page("pages/3_Alunos.py", title="Alunos"),
    st.Page("pages/4_Aulas.py", title="Aulas"),
    st.Page("pages/5_Recital.py", title="Recital"),
]
if user["role"] == "gestor":
    pages += [
        st.Page("pages/6_Auditoria.py", title="Auditoria"),
        st.Page("pages/7_Exportacao.py", title="Exportação"),
        st.Page("pages/8_Configuracoes.py", title="Configurações"),
        st.Page("pages/9_Relatorio_Final.py", title="Relatório Final"),
    ]

pg = st.navigation(pages)
pg.run()
