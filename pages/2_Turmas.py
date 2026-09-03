import streamlit as st

import db
import utils

utils.inject_css()
user = utils.require_login()

st.title("Turmas")
st.caption("Uma turma reúne alunos, aulas, diário e recital em um único espaço de trabalho compartilhado entre o gestor e os professores vinculados a ela.")

# ------------------------------------------------------------------ #
# Gestor: criar nova turma
# ------------------------------------------------------------------ #
if user["role"] == "gestor":
    with st.expander("Criar nova turma", expanded=(len(db.get_turmas()) == 0)):
        professores = db.get_accounts(role="professor")
        with st.form("new_turma_form"):
            name = st.text_input("Nome da turma", placeholder="Ex.: Acordes de Lagoinha — Turma 2026")
            community = st.text_input("Comunidade / edital", value="Comunidade Quilombola de Lagoinha — Berilo/MG")
            c1, c2, c3 = st.columns(3)
            with c1:
                hmin = st.number_input("Carga horária mínima (h)", min_value=1, value=20)
            with c2:
                smin = st.number_input("Público mínimo", min_value=1, value=15)
            with c3:
                smax = st.number_input("Público máximo", min_value=1, value=20)
            member_names = st.multiselect(
                "Professores com acesso a esta turma",
                options=[p["id"] for p in professores],
                format_func=lambda pid: next(p["name"] for p in professores if p["id"] == pid),
            )
            submitted = st.form_submit_button("Criar turma", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Dê um nome para a turma.")
            else:
                tid = db.create_turma(name, community, hmin, smin, smax, user["id"], member_names)
                db.log_action(tid, user["id"], user["name"], user["role"], f"Criou a turma '{name}'")
                st.session_state["current_turma_id"] = tid
                st.success(f"Turma '{name}'criada!")
                st.rerun()

st.markdown("---")

# ------------------------------------------------------------------ #
# Lista de turmas
# ------------------------------------------------------------------ #
if user["role"] == "gestor":
    turmas = db.get_turmas()
else:
    turmas = db.get_turmas_for_account(user["id"])

if not turmas:
    st.info("Nenhuma turma disponível ainda." if user["role"] == "gestor" else "Você ainda não foi vinculado(a) a nenhuma turma. Peça ao gestor(a) para te adicionar.")
    st.stop()

for t in turmas:
    students = db.get_active_students(t["id"])
    classes = db.get_classes(t["id"])
    hours = sum(c["hours"] or 0 for c in classes)
    members = db.get_turma_members(t["id"])

    with st.container(border=True):
        colL, colR = st.columns([3, 1])
        with colL:
            st.markdown(f"### {t['name']}")
            st.caption(t["community"] or "")
            st.write(
                f"**{len(students)}** aluno(s) ativo(s) · **{len(classes)}** aula(s) · **{hours:.1f}h** de {t['target_hours_min']:.0f}h · "
                f"‍ {', '.join(m['name'] for m in members) if members else 'nenhum professor vinculado'}"
            )
        with colR:
            if st.button("Usar esta turma", key=f"use_{t['id']}", use_container_width=True):
                st.session_state["current_turma_id"] = t["id"]
                st.success(f"Turma ativa: {t['name']}")

        if user["role"] == "gestor":
            with st.expander("Editar turma e professores vinculados"):
                professores = db.get_accounts(role="professor")
                with st.form(f"edit_turma_{t['id']}"):
                    new_name = st.text_input("Nome", value=t["name"], key=f"name_{t['id']}")
                    new_community = st.text_input("Comunidade / edital", value=t["community"] or "", key=f"comm_{t['id']}")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        new_hmin = st.number_input("Carga horária mínima (h)", min_value=1, value=int(t["target_hours_min"]), key=f"hmin_{t['id']}")
                    with c2:
                        new_smin = st.number_input("Público mínimo", min_value=1, value=int(t["target_students_min"]), key=f"smin_{t['id']}")
                    with c3:
                        new_smax = st.number_input("Público máximo", min_value=1, value=int(t["target_students_max"]), key=f"smax_{t['id']}")
                    current_member_ids = [m["id"] for m in members]
                    new_members = st.multiselect(
                        "Professores com acesso",
                        options=[p["id"] for p in professores],
                        default=current_member_ids,
                        format_func=lambda pid: next(p["name"] for p in professores if p["id"] == pid),
                        key=f"members_{t['id']}",
                    )
                    save = st.form_submit_button("Salvar alterações", use_container_width=True)
                if save:
                    db.update_turma(
                        t["id"], name=new_name.strip(), community=new_community.strip(),
                        target_hours_min=new_hmin, target_students_min=new_smin, target_students_max=new_smax,
                    )
                    db.set_turma_members(t["id"], new_members)
                    db.log_action(t["id"], user["id"], user["name"], user["role"], f"Editou a turma '{new_name}'e seus professores vinculados")
                    st.success("Turma atualizada.")
                    st.rerun()
