import streamlit as st

import db
import utils

utils.inject_css()
user = utils.require_login()
turma = utils.turma_switcher(user)

st.title("Gestão de Turma e Participantes")
st.caption(f"Turma ativa: **{turma['name']}**")

students = db.get_students(turma["id"])
active = [s for s in students if s["active"]]
target_ok = turma["target_students_min"] <= len(active) <= turma["target_students_max"]

badge = '<span class="badge ok">meta em dia</span>' if target_ok else '<span class="badge warn">fora da meta</span>'
st.markdown(
    f"{len(active)} aluno(s) ativo(s) — meta: {turma['target_students_min']} a {turma['target_students_max']} {badge}",
    unsafe_allow_html=True,
)

if "editing_student_id" not in st.session_state:
    st.session_state.editing_student_id = None
if "new_student" not in st.session_state:
    st.session_state.new_student = False

top_l, top_r = st.columns([4, 1])
with top_r:
    if st.button("Novo aluno", use_container_width=True):
        st.session_state.new_student = True
        st.session_state.editing_student_id = None

with st.container(border=True):
    if students:
        for s in students:
            c1, c2, c3, c4, c5, c6 = st.columns([2.2, 1.1, 1.6, 1.6, 1.4, 0.9])
            c1.write(f"**{s['name']}**")
            c2.write(utils.fmt_date(s["birth_date"]))
            c3.write(s["guardian_name"] or "—")
            c4.write(s["school"] or "—")
            auth_badge = {"assinado": '<span class="badge ok">Assinado</span>',
                          "pendente": '<span class="badge warn">Pendente</span>'}.get(s["image_auth"], '<span class="badge muted">N/A</span>')
            c5.markdown(auth_badge, unsafe_allow_html=True)
            if c6.button("Editar", key=f"edit_{s['id']}"):
                st.session_state.editing_student_id = s["id"]
                st.session_state.new_student = False
        st.markdown("---")
    else:
        st.info("Nenhum aluno cadastrado ainda nesta turma.")


def student_form(existing=None):
    label = "Editar aluno" if existing else "Novo aluno"
    with st.form("student_form"):
        st.markdown(f"#### {label}")
        name = st.text_input("Nome completo", value=existing["name"] if existing else "")
        c1, c2 = st.columns(2)
        with c1:
            birth = st.text_input("Data de nascimento (AAAA-MM-DD)", value=existing["birth_date"] if existing else "")
            guardian = st.text_input("Filiação / responsável legal", value=existing["guardian_name"] if existing else "")
        with c2:
            school = st.text_input("Escola pública em que estuda", value=existing["school"] if existing else "")
            address = st.text_input("Endereço / território (Lagoinha)", value=existing["address"] if existing else "")
        c3, c4 = st.columns(2)
        with c3:
            auth_opts = ["pendente", "assinado", "nao_aplicavel"]
            auth_labels = {"pendente": "Pendente", "assinado": "Assinado (anexado/arquivado)", "nao_aplicavel": "Não aplicável"}
            auth = st.selectbox(
                "Termo de Autorização de Uso de Imagem e Voz", auth_opts,
                index=auth_opts.index(existing["image_auth"]) if existing else 0,
                format_func=lambda k: auth_labels[k],
            )
        with c4:
            active = st.selectbox("Status na turma", [True, False],
                                   index=0 if (not existing or existing["active"]) else 1,
                                   format_func=lambda v: "Ativo" if v else "Inativo")
        note = st.text_input("Observação sobre a autorização (ex.: local do arquivo físico)",
                              value=existing["image_auth_note"] if existing else "")
        c5, c6 = st.columns(2)
        submitted = c5.form_submit_button("Salvar aluno", use_container_width=True)
        cancel = c6.form_submit_button("Cancelar", use_container_width=True)

    if cancel:
        st.session_state.editing_student_id = None
        st.session_state.new_student = False
        st.rerun()

    if submitted:
        if not name.strip():
            st.error("Informe o nome do aluno.")
            return
        fields = dict(
            name=name.strip(), birth_date=birth.strip(), guardian_name=guardian.strip(),
            school=school.strip(), address=address.strip(), image_auth=auth,
            image_auth_note=note.strip(), active=int(active),
        )
        if existing:
            db.update_student(existing["id"], **fields)
            db.log_action(turma["id"], user["id"], user["name"], user["role"], f"Editou o cadastro do aluno {name}")
        else:
            db.create_student(turma["id"], **fields)
            db.log_action(turma["id"], user["id"], user["name"], user["role"], f"Cadastrou o novo aluno {name}")
        st.session_state.editing_student_id = None
        st.session_state.new_student = False
        st.success("Aluno salvo.")
        st.rerun()


if st.session_state.new_student:
    with st.container(border=True):
        student_form(None)
elif st.session_state.editing_student_id:
    existing = db.get_student(st.session_state.editing_student_id)
    with st.container(border=True):
        student_form(existing)
