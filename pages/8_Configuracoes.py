import streamlit as st

import db
import utils

utils.inject_css()
user = utils.require_login()

if user["role"] != "gestor":
    st.error("Esta página é restrita ao perfil Gestor(a) / Auditor.")
    st.stop()

st.title("Configurações")

st.subheader("Contas de acesso")
st.caption(
    "Cada pessoa cria a própria senha no primeiro login. Se alguém esquecer a senha, use "
    "\"Redefinir\"para forçar a criação de uma senha nova no próximo acesso."
)

with st.container(border=True):
    accounts = db.get_accounts()
    for a in accounts:
        c1, c2, c3, c4 = st.columns([2.4, 1.6, 1.4, 1.4])
        c1.write(f"**{a['name']}**")
        c2.write("Gestor(a)" if a["role"] == "gestor" else "Professor(a)")
        c3.markdown('<span class="badge ok">Definida</span>' if a["pass_hash"] else '<span class="badge muted">Ainda não criada</span>', unsafe_allow_html=True)
        with c4:
            bcol1, bcol2 = st.columns(2)
            if a["pass_hash"] and bcol1.button("Redefinir", key=f"reset_{a['id']}"):
                db.reset_password(a["id"])
                db.log_action(None, user["id"], user["name"], user["role"], f"Redefiniu a senha de acesso de {a['name']}")
                st.success(f"Senha de {a['name']} redefinida.")
                st.rerun()
            if bcol2.button("Remover", key=f"remove_{a['id']}"):
                db.delete_account(a["id"])
                db.log_action(None, user["id"], user["name"], user["role"], f"Removeu a conta de acesso de {a['name']}")
                st.success(f"Conta de {a['name']} removida.")
                st.rerun()

    st.markdown("---")
    with st.form("new_account_form"):
        c1, c2, c3 = st.columns([2, 1.4, 1])
        with c1:
            new_name = st.text_input("Nome da nova pessoa")
        with c2:
            new_role = st.selectbox("Perfil", ["professor", "gestor"], format_func=lambda r: "Professor(a)" if r == "professor" else "Gestor(a)")
        with c3:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("Adicionar", use_container_width=True)
    if submitted:
        if not new_name.strip():
            st.error("Informe o nome da pessoa.")
        else:
            db.create_account(new_name, new_role)
            db.log_action(None, user["id"], user["name"], user["role"], f"Adicionou nova conta de acesso: {new_name} ({new_role})")
            st.success(f"Conta de {new_name} criada.")
            st.rerun()

st.info(
    "As senhas ficam salvas com hash no banco de dados local do projeto (data/acordes.db), sem "
    "criptografia de nível empresarial — evite reutilizar senhas sensíveis nesta ferramenta e faça "
    "backups periódicos da pasta `data/`."
)
