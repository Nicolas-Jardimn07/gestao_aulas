from datetime import date as date_cls, time as time_cls

import streamlit as st

import db
import utils

utils.inject_css()
user = utils.require_login()
turma = utils.turma_switcher(user)

st.title("Evento Especial — Recital de Encerramento")
st.caption(f"Turma ativa: **{turma['name']}**")

if "recital_editing" not in st.session_state:
    st.session_state.recital_editing = False

ev = db.get_final_event(turma["id"])
students = db.get_students(turma["id"])


def render_view():
    if ev["locked"]:
        st.error("Este registro foi validado pelo gestor(a) — a edição está bloqueada.")
    else:
        st.success("Este registro ainda está aberto e pode ser editado.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Data", utils.fmt_date(ev["date"]))
    c2.metric("Local", ev["location"] or "—")
    c3.metric("Horário", ev["time"] or "—")

    with st.container(border=True):
        st.markdown("#### Repertório executado")
        st.write(ev["repertoire"] or "—")
        st.markdown("#### Alunos participantes")
        names = [s["name"] for s in students if s["id"] in ev["participant_ids"]]
        st.write(", ".join(names) or "—")
        st.markdown("#### Público estimado")
        st.write(f"{ev['audience'] or '—'} pessoas")
        st.markdown("#### Acessibilidade aplicada")
        st.write(ev["accessibility"] or "—")
        if ev["video_note"]:
            st.markdown("#### Vídeos")
            st.write(ev["video_note"])

    b1, b2, _ = st.columns([1, 1, 3])
    if not ev["locked"]:
        if b1.button("Editar"):
            st.session_state.recital_editing = True
            st.rerun()
    if user["role"] == "gestor":
        if ev["locked"]:
            if b2.button("Destravar"):
                db.set_event_locked(turma["id"], False)
                db.log_action(turma["id"], user["id"], user["name"], user["role"], "Destravou o registro do Recital")
                st.rerun()
        else:
            if b2.button("Validar e travar"):
                db.set_event_locked(turma["id"], True)
                db.log_action(turma["id"], user["id"], user["name"], user["role"], "Validou e travou o registro do Recital")
                st.rerun()


def render_form():
    with st.form("recital_form"):
        d = st.date_input("Data", value=date_cls.fromisoformat(ev["date"]) if ev and ev["date"] else date_cls.today())
        c1, c2 = st.columns(2)
        with c1:
            location = st.text_input("Local", value=ev["location"] if ev else "")
        with c2:
            t = st.time_input("Horário", value=time_cls.fromisoformat(ev["time"]) if ev and ev["time"] else time_cls(18, 0))
        repertoire = st.text_area("Repertório executado", value=ev["repertoire"] if ev else "")
        participant_ids = st.multiselect(
            "Alunos participantes no palco",
            options=[s["id"] for s in students],
            default=ev["participant_ids"] if ev else [],
            format_func=lambda sid: next(s["name"] for s in students if s["id"] == sid),
        )
        c3, c4 = st.columns(2)
        with c3:
            audience = st.text_input("Estimativa de público comunitário", value=ev["audience"] if ev else "")
        with c4:
            accessibility = st.text_input("Acessibilidade (audiodescrição do repertório/músicos)",
                                           value=ev["accessibility"] if ev else "")
        video_note = st.text_input(
            "Vídeos (referência/link — não é possível anexar vídeo ao sistema)",
            value=ev["video_note"] if ev else "",
        )
        col_save, col_cancel = st.columns(2)
        submitted = col_save.form_submit_button("Salvar", use_container_width=True)
        cancel = col_cancel.form_submit_button("Cancelar", use_container_width=True)

    if cancel:
        st.session_state.recital_editing = False
        st.rerun()

    if submitted:
        db.upsert_final_event(
            turma["id"], d.isoformat(), location.strip(), t.strftime("%H:%M"), repertoire,
            participant_ids, audience.strip(), accessibility.strip(), video_note.strip(),
        )
        db.log_action(turma["id"], user["id"], user["name"], user["role"], "Registrou/editou o Recital de Encerramento")
        st.session_state.recital_editing = False
        st.success("Recital salvo.")
        st.rerun()


if not ev:
    st.info("Nenhum registro ainda para esta turma.")
    if st.button("Registrar apresentação final"):
        st.session_state.recital_editing = True
        st.rerun()
    if st.session_state.recital_editing:
        render_form()
elif st.session_state.recital_editing:
    render_form()
else:
    render_view()
