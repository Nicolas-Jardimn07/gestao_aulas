import streamlit as st

import db
import utils

utils.inject_css()
user = utils.require_login()

if user["role"] != "gestor":
    st.error("Esta página é restrita ao perfil Gestor(a) / Auditor.")
    st.stop()

st.title("Trilha de Auditoria")
st.caption("Histórico de ações realizadas no sistema — quem preencheu, quando e o que foi alterado.")

all_turmas = db.get_turmas()
options = {"__all__": "Todas as turmas"}
options.update({t["id"]: t["name"] for t in all_turmas})
chosen = st.selectbox("Filtrar por turma", options.keys(), format_func=lambda k: options[k])

entries = db.get_audit(None if chosen == "__all__" else chosen)

with st.container(border=True):
    if not entries:
        st.info("Nenhum registro de auditoria ainda.")
    else:
        for e in entries:
            turma_name = options.get(e["turma_id"], "—") if e["turma_id"] else "—"
            role_label = "Gestor(a)" if e["role"] == "gestor" else "Professor(a)"
            st.write(f"**{utils.fmt_datetime(e['at'])}** — **{e['account_name']}** ({role_label}) · _{turma_name}_")
            st.write(e["action"])
            st.markdown("---")
