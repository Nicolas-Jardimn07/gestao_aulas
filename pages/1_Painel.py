import streamlit as st

import db
import utils

utils.inject_css()
user = utils.require_login()


def turma_compliance(turma):
    students = db.get_active_students(turma["id"])
    classes = db.get_classes(turma["id"])
    hours = sum(c["hours"] or 0 for c in classes)
    attendance_rows = db.get_attendance_for_turma(turma["id"])
    total = len(attendance_rows)
    present = sum(1 for a in attendance_rows if a["present"])
    att_pct = round((present / total) * 100) if total else 0
    students_ok = turma["target_students_min"] <= len(students) <= turma["target_students_max"]
    hours_pct = min(100, round((hours / turma["target_hours_min"]) * 100)) if turma["target_hours_min"] else 100
    pending_auth = len([s for s in students if s.get("image_auth") == "pendente"])
    return {
        "students": len(students), "hours": hours, "hours_pct": hours_pct, "att_pct": att_pct,
        "students_ok": students_ok, "n_classes": len(classes),
        "locked": len([c for c in classes if c["locked"]]), "pending_auth": pending_auth,
    }


st.title("Painel de Conformidade")
st.caption("Acompanhamento das metas pactuadas no Edital PNAB de Berilo/MG.")

# ------------------------------------------------------------------ #
# Visão geral — todas as turmas (gestor)
# ------------------------------------------------------------------ #
if user["role"] == "gestor":
    all_turmas = db.get_turmas()
    if all_turmas:
        st.subheader("Visão geral de todas as turmas")
        c1, c2, c3, c4 = st.columns(4)
        total_students = sum(len(db.get_active_students(t["id"])) for t in all_turmas)
        total_hours = sum(turma_compliance(t)["hours"] for t in all_turmas)
        below_target = [t for t in all_turmas if not turma_compliance(t)["students_ok"]]
        c1.metric("Turmas ativas", len(all_turmas))
        c2.metric("Alunos ativos (total)", total_students)
        c3.metric("Horas somadas", f"{total_hours:.1f}h")
        c4.metric("Turmas fora da meta", len(below_target))

        rows_html = ""
        for t in all_turmas:
            c = turma_compliance(t)
            badge_students = '<span class="badge ok">Meta ok</span>' if c["students_ok"] else '<span class="badge warn">Fora da meta</span>'
            badge_hours = '<span class="badge ok">Concluída</span>' if c["hours_pct"] >= 100 else f'<span class="badge muted">{c["hours_pct"]}%</span>'
            rows_html += f"""<tr>
              <td><b>{t['name']}</b><br><span style="color:var(--ink-faint);font-size:12px;">{t['community'] or ''}</span></td>
              <td>{c['students']} / {t['target_students_min']}–{t['target_students_max']} {badge_students}</td>
              <td>{c['hours']:.1f}h / {t['target_hours_min']:.0f}h {badge_hours}</td>
              <td>{c['att_pct']}%</td>
              <td>{c['n_classes']} ({c['locked']} validada(s))</td>
              <td>{'<span class="badge warn">'+str(c['pending_auth'])+'pendente(s)</span>' if c['pending_auth'] else '<span class="badge ok">Em dia</span>'}</td>
            </tr>"""
        utils.raw_html(
            f"""<div class="acl-card" style="overflow-x:auto;"><table style="width:100%;min-width:640px;border-collapse:collapse;font-size:13.5px;">
            <thead><tr style="text-align:left;color:var(--ink-soft);font-size:12px;">
            <th style="padding:6px;">Turma</th><th style="padding:6px;">Alunos</th><th style="padding:6px;">Carga horária</th>
            <th style="padding:6px;">Frequência</th><th style="padding:6px;">Aulas</th><th style="padding:6px;">Autorização img/voz</th>
            </tr></thead><tbody>{rows_html}</tbody></table></div>"""
        )
        st.markdown("---")

turma = utils.turma_switcher(user)
st.subheader(f"Detalhamento — {turma['name']}")

students = db.get_active_students(turma["id"])
classes = db.get_classes(turma["id"])
attendance_rows = db.get_attendance_for_turma(turma["id"])
c = turma_compliance(turma)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Carga horária acumulada", f"{c['hours']:.1f}h", f"meta: {turma['target_hours_min']:.0f}h")
    st.progress(min(1.0, c["hours"] / turma["target_hours_min"]) if turma["target_hours_min"] else 1.0)
with col2:
    st.metric("Alunos ativos", c["students"], f"meta: {turma['target_students_min']}–{turma['target_students_max']}")
    st.markdown('<span class="badge ok">Dentro da meta</span>' if c["students_ok"] else '<span class="badge warn">Fora da faixa exigida</span>', unsafe_allow_html=True)
with col3:
    st.metric("Frequência geral da turma", f"{c['att_pct']}%")
    st.progress(c["att_pct"] / 100)

st.write("")
colA, colB = st.columns(2)

with colA:
    with st.container(border=True):
        st.markdown("#### Horas de oficina por mês")
        by_month = {}
        for cl in classes:
            m = (cl["date"] or "—")[:7]
            by_month[m] = by_month.get(m, 0) + (cl["hours"] or 0)
        if by_month:
            st.bar_chart(dict(sorted(by_month.items())))
        else:
            st.caption("Nenhuma aula registrada ainda.")

with colB:
    with st.container(border=True):
        st.markdown("#### Frequência por aluno")
        if students:
            for s in students:
                recs = [a["present"] for a in attendance_rows if a["student_id"] == s["id"]]
                pct = round((sum(recs) / len(recs)) * 100) if recs else 0
                st.write(f"**{s['name']}** — {pct}%")
                st.progress(pct / 100)
                if pct < 50 and recs:
                    st.caption("Frequência abaixo de 50% — atenção.")
        else:
            st.caption("Cadastre alunos para ver a frequência.")

st.write("")
colC, colD = st.columns(2)

with colC:
    with st.container(border=True):
        st.markdown("#### Aulas recentes")
        recent = classes[:5]
        if recent:
            for cl in recent:
                lock = "validada" if cl["locked"] else "aberta"
                st.write(f"**{utils.fmt_date(cl['date'])}** · {cl['start_time']}–{cl['end_time']} · {cl['hours']:.1f}h · {lock}")
        else:
            st.caption("Nenhuma aula ainda.")

with colD:
    with st.container(border=True):
        st.markdown("#### Atividade recente (auditoria)")
        entries = db.get_audit(turma["id"], limit=6)
        if entries:
            for e in entries:
                st.write(f"**{e['account_name']}** — {e['action']}")
                st.caption(utils.fmt_datetime(e["at"]))
        else:
            st.caption("Nenhum registro ainda.")

if c["pending_auth"]:
    st.warning(f" {c['pending_auth']} aluno(s) com o Termo de Autorização de Uso de Imagem e Voz pendente.")
