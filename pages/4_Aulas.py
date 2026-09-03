from datetime import date as date_cls, time as time_cls

import streamlit as st

import db
import utils

utils.inject_css()
user = utils.require_login()
turma = utils.turma_switcher(user)

st.title("Diário de Aulas")
st.caption(f"Turma ativa: **{turma['name']}** — registro do ciclo de oficinas, frequência e conteúdo pedagógico.")

if "aulas_mode" not in st.session_state:
    st.session_state.aulas_mode = "list"
if "aulas_selected_id" not in st.session_state:
    st.session_state.aulas_selected_id = None

ACCESS_OPTIONS = ["Linguagem simples", "Audiodescrição oral", "Apoio a dificuldades específicas"]


def go(mode, cid=None):
    st.session_state.aulas_mode = mode
    st.session_state.aulas_selected_id = cid
    st.rerun()


# ------------------------------------------------------------------ #
# LISTA
# ------------------------------------------------------------------ #
def render_list():
    top_l, top_r = st.columns([4, 1])
    with top_r:
        if st.button("Nova aula", use_container_width=True):
            go("new")

    classes = db.get_classes(turma["id"])
    with st.container(border=True):
        if not classes:
            st.info("Nenhuma aula registrada ainda nesta turma.")
            return
        attendance_rows = db.get_attendance_for_turma(turma["id"])
        for c in classes:
            class_att = [a for a in attendance_rows if a["class_id"] == c["id"]]
            present = len([a for a in class_att if a["present"]])
            total = len(class_att)
            lock = '<span class="badge ok">Validada</span>' if c["locked"] else '<span class="badge muted">Aberta</span>'
            col1, col2, col3, col4, col5, col6 = st.columns([1.3, 1.6, 2, 1, 1.4, 1])
            col1.write(f"**{utils.fmt_date(c['date'])}**")
            col2.write(f"{c['start_time']}–{c['end_time']}")
            col3.write(", ".join(c["professors"]) or "—")
            col4.write(f"{c['hours']:.1f}h")
            col5.write(f"{present}/{total} presentes")
            col6.markdown(lock, unsafe_allow_html=True)
            if st.button("Ver detalhes", key=f"view_{c['id']}"):
                go("detail", c["id"])
            st.markdown("---")


# ------------------------------------------------------------------ #
# FORMULÁRIO (nova / editar)
# ------------------------------------------------------------------ #
def render_form(existing=None):
    students = db.get_active_students(turma["id"])
    members = db.get_turma_members(turma["id"])
    existing_attendance = {a["student_id"]: a for a in db.get_attendance(existing["id"])} if existing else {}

    st.subheader("Editar aula" if existing else "Nova aula")
    if not students:
        st.warning("Cadastre alunos ativos nesta turma antes de lançar uma aula.")
        if st.button("Voltar"):
            go("list")
        return

    with st.form("class_form"):
        st.markdown("##### Dados da sessão")
        c1, c2, c3 = st.columns(3)
        with c1:
            d = st.date_input(
                "Data", value=date_cls.fromisoformat(existing["date"]) if existing else date_cls.today()
            )
        with c2:
            start = st.time_input(
                "Início", value=time_cls.fromisoformat(existing["start_time"]) if existing else time_cls(14, 0)
            )
        with c3:
            end = st.time_input(
                "Término", value=time_cls.fromisoformat(existing["end_time"]) if existing else time_cls(16, 0)
            )
        professors = st.multiselect(
            "Instrutor(es) presente(s)",
            options=[m["name"] for m in members],
            default=existing["professors"] if existing else ([user["name"]] if user["role"] == "professor" else []),
        )

        st.markdown("##### Chamada escolar (frequência)")
        attendance_inputs = {}
        for s in students:
            rec = existing_attendance.get(s["id"])
            default_present = rec["present"] == 1 if rec else True
            default_just = rec["justification"] if rec else ""
            cc1, cc2, cc3 = st.columns([2.2, 1, 3])
            cc1.write(f"**{s['name']}**")
            present = cc2.checkbox("Presente", value=bool(default_present), key=f"att_p_{s['id']}")
            just = cc3.text_input("Justificativa (se ausente)", value=default_just or "", key=f"att_j_{s['id']}")
            attendance_inputs[s["id"]] = (present, just)

        st.markdown("##### Diário pedagógico")
        acordes = st.text_area("Acordes ensinados", value=existing["diary_acordes"] if existing else "")
        exercicios = st.text_area("Exercícios rítmicos", value=existing["diary_exercicios"] if existing else "")
        repertorio = st.text_area("Repertório trabalhado", value=existing["diary_repertorio"] if existing else "")
        dinamicas = st.text_area("Dinâmicas de grupo", value=existing["diary_dinamicas"] if existing else "")

        st.markdown("##### Acessibilidade praticada")
        access_selected = []
        existing_access = existing["access"] if existing else []
        acc_cols = st.columns(3)
        for i, opt in enumerate(ACCESS_OPTIONS):
            with acc_cols[i]:
                if st.checkbox(opt, value=(opt in existing_access), key=f"acc_{i}"):
                    access_selected.append(opt)
        access_other = st.text_input("Outra prática de acessibilidade (opcional)",
                                      value=existing["access_other"] if existing else "")

        col_save, col_cancel = st.columns(2)
        submitted = col_save.form_submit_button("Salvar aula", use_container_width=True)
        cancel = col_cancel.form_submit_button("Cancelar", use_container_width=True)

    if cancel:
        go("detail" if existing else "list", existing["id"] if existing else None)

    if submitted:
        hours = utils.calc_hours(start, end)
        attendance_records = [
            {"student_id": sid, "present": present, "justification": just}
            for sid, (present, just) in attendance_inputs.items()
        ]
        diary = {"acordes": acordes, "exercicios": exercicios, "repertorio": repertorio, "dinamicas": dinamicas}

        if existing:
            db.update_class(
                existing["id"], d.isoformat(), start.strftime("%H:%M"), end.strftime("%H:%M"), hours,
                professors, diary, access_selected, access_other, attendance_records, user["name"],
            )
            class_id = existing["id"]
            db.log_action(turma["id"], user["id"], user["name"], user["role"],
                           f"Editou a aula de {utils.fmt_date(d.isoformat())}")
        else:
            class_id = db.create_class(
                turma["id"], d.isoformat(), start.strftime("%H:%M"), end.strftime("%H:%M"), hours,
                professors, diary, access_selected, access_other, attendance_records, user["name"],
            )
            db.log_action(turma["id"], user["id"], user["name"], user["role"],
                           f"Registrou nova aula em {utils.fmt_date(d.isoformat())} ({hours}h)")

        st.success("Aula salva com sucesso.")
        go("detail", class_id)


# ------------------------------------------------------------------ #
# DETALHE
# ------------------------------------------------------------------ #
def render_detail(class_id):
    c = db.get_class(class_id)
    if not c:
        st.error("Aula não encontrada.")
        if st.button("Voltar"):
            go("list")
        return

    if st.button("Voltar para a lista"):
        go("list")

    st.subheader(f"Aula de {utils.fmt_date(c['date'])}")
    if c["locked"]:
        st.error("Esta aula foi validada pelo gestor(a) — a edição está bloqueada.")
    else:
        st.success("Esta aula ainda está aberta e pode ser editada.")

    students = {s["id"]: s for s in db.get_students(turma["id"])}
    attendance = db.get_attendance(class_id)

    c1, c2, c3 = st.columns(3)
    c1.metric("Horário", f"{c['start_time']}–{c['end_time']}")
    c2.metric("Carga horária", f"{c['hours']:.1f}h")
    c3.metric("Presenças", f"{len([a for a in attendance if a['present']])}/{len(attendance)}")
    st.write("**Instrutor(es):** " + (", ".join(c["professors"]) or "—"))

    with st.container(border=True):
        st.markdown("#### Frequência")
        for a in attendance:
            s = students.get(a["student_id"])
            status = '<span class="badge ok">Presente</span>' if a["present"] else '<span class="badge warn">Ausente</span>'
            just = f" — _{a['justification']}_" if (not a["present"] and a["justification"]) else ""
            st.markdown(f"- **{s['name'] if s else '—'}**: {status}{just}", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Diário pedagógico")
        st.write(f"**Acordes ensinados:** {c['diary_acordes'] or '—'}")
        st.write(f"**Exercícios rítmicos:** {c['diary_exercicios'] or '—'}")
        st.write(f"**Repertório trabalhado:** {c['diary_repertorio'] or '—'}")
        st.write(f"**Dinâmicas de grupo:** {c['diary_dinamicas'] or '—'}")
        acc_text = ", ".join(c["access"]) or "—"
        if c["access_other"]:
            acc_text += f" · {c['access_other']}"
        st.write(f"**Acessibilidade:** {acc_text}")


    st.write("")
    b1, b2, _ = st.columns([1, 1, 3])
    if not c["locked"]:
        if b1.button("Editar aula"):
            go("edit", class_id)
    if user["role"] == "gestor":
        if c["locked"]:
            if b2.button("Destravar"):
                db.set_class_locked(class_id, False)
                db.log_action(turma["id"], user["id"], user["name"], user["role"],
                               f"Destravou a aula de {utils.fmt_date(c['date'])}")
                st.rerun()
        else:
            if b2.button("Validar e travar"):
                db.set_class_locked(class_id, True)
                db.log_action(turma["id"], user["id"], user["name"], user["role"],
                               f"Validou e travou a aula de {utils.fmt_date(c['date'])}")
                st.rerun()


# ------------------------------------------------------------------ #
mode = st.session_state.aulas_mode
if mode == "list":
    render_list()
elif mode == "new":
    render_form(None)
elif mode == "edit":
    render_form(db.get_class(st.session_state.aulas_selected_id))
elif mode == "detail":
    render_detail(st.session_state.aulas_selected_id)
