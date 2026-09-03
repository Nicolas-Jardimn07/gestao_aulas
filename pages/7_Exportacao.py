import streamlit as st

import db
import reports
import utils

utils.inject_css()
user = utils.require_login()

if user["role"] != "gestor":
    st.error("Esta página é restrita ao perfil Gestor(a) / Auditor.")
    st.stop()

turma = utils.turma_switcher(user)

st.title("Exportação e Dossiê Final")
st.caption(f"Turma ativa: **{turma['name']}** — documentos prontos para a prestação de contas (Anexo VI da PNAB).")

students = db.get_students(turma["id"])
classes = db.get_classes(turma["id"])

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("#### Ficha do aluno")
        st.caption("Extrato individual de presença por participante, em PDF.")
        if students:
            sid = st.selectbox("Aluno", [s["id"] for s in students], format_func=lambda i: next(s["name"] for s in students if s["id"] == i))
            student = next(s for s in students if s["id"] == sid)
            pdf_bytes = reports.ficha_aluno_pdf(turma, student, classes)
            st.download_button("Baixar ficha em PDF", data=pdf_bytes,
                                file_name=f"ficha_{student['name'].replace(' ', '_')}.pdf", mime="application/pdf")
        else:
            st.info("Cadastre alunos primeiro.")

with col2:
    with st.container(border=True):
        st.markdown("#### Diário de bordo unificado")
        st.caption("Compilado de todas as aulas com datas, instrutores e temas pedagógicos.")
        pdf_bytes = reports.diario_unificado_pdf(turma, classes)
        st.download_button("Baixar diário em PDF", data=pdf_bytes, file_name="diario_unificado.pdf", mime="application/pdf")

    with st.container(border=True):
        st.markdown("#### Planilhas (CSV)")
        st.caption("Dados estruturados de alunos, aulas e frequência.")
        st.download_button("Alunos.csv", data=reports.students_csv(students), file_name="alunos.csv", mime="text/csv")
        st.download_button("Aulas.csv", data=reports.classes_csv(classes), file_name="aulas.csv", mime="text/csv")
        st.download_button("Frequência.csv", data=reports.attendance_csv(classes, students), file_name="frequencia.csv", mime="text/csv")
