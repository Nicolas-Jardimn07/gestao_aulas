"""Geração de PDFs (Anexo VI / dossiê) e planilhas CSV para exportação."""
import csv
import io

from fpdf import FPDF
from fpdf.enums import XPos, YPos

import anexo_options as opt
import db
import utils

TERRA = (160, 107, 59)
INK = (58, 42, 24)


class ReportPDF(FPDF):
    def normalize_text(self, text):
        try:
            return super().normalize_text(text)
        except Exception:
            return str(text).encode("latin-1", "replace").decode("latin-1")

    def multi_cell(self, w, h=None, text="", *args, **kwargs):
        kwargs.setdefault("new_x", XPos.LMARGIN)
        kwargs.setdefault("new_y", YPos.NEXT)
        return super().multi_cell(w, h, text, *args, **kwargs)

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*TERRA)
        self.cell(0, 10, self.title_text, ln=True)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*INK)
        self.cell(0, 6, self.subtitle_text, ln=True)
        self.ln(2)
        self.set_draw_color(*TERRA)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 140, 120)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def _new_pdf(title, subtitle):
    pdf = ReportPDF()
    pdf.title_text = title
    pdf.subtitle_text = subtitle
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_text_color(*INK)
    return pdf


def _section(pdf, text):
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*TERRA)
    pdf.cell(0, 8, text, ln=True)
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "", 10.5)


def ficha_aluno_pdf(turma, student, classes):
    pdf = _new_pdf(f"Ficha do Aluno - {student['name']}", f"{turma['name']} · {turma['community'] or ''}")
    _section(pdf, "Dados do aluno")
    pdf.multi_cell(0, 6, f"Nascimento: {utils.fmt_date(student['birth_date'])}    Responsável: {student['guardian_name'] or '-'}")
    pdf.multi_cell(0, 6, f"Escola: {student['school'] or '-'}    Endereço: {student['address'] or '-'}")
    pdf.multi_cell(0, 6, f"Autorização de imagem/voz: {student['image_auth']}")
    pdf.ln(3)

    class_dates = {c["id"]: c["date"] for c in classes}
    records = [
        (class_dates.get(a["class_id"]), a["present"], a["justification"])
        for a in db.get_attendance_for_turma(turma["id"])
        if a["student_id"] == student["id"]
    ]
    present_count = sum(1 for r in records if r[1])

    _section(pdf, f"Extrato de presença ({present_count}/{len(records)})")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(40, 7, "Data", border=1)
    pdf.cell(40, 7, "Situação", border=1)
    pdf.cell(0, 7, "Justificativa", border=1, ln=True)
    pdf.set_font("Helvetica", "", 10)
    for dt, present, just in sorted(records, key=lambda r: r[0] or ""):
        pdf.cell(40, 7, utils.fmt_date(dt), border=1)
        pdf.cell(40, 7, "Presente" if present else "Ausente", border=1)
        pdf.cell(0, 7, (just or "")[:60], border=1, ln=True)

    return bytes(pdf.output())


def diario_unificado_pdf(turma, classes):
    pdf = _new_pdf("Diário de Bordo Unificado", f"{turma['name']} · {turma['community'] or ''}")
    total_hours = 0.0
    for c in sorted(classes, key=lambda x: x["date"] or ""):
        total_hours += c["hours"] or 0
        _section(pdf, f"{utils.fmt_date(c['date'])} · {c['start_time']}-{c['end_time']} ({c['hours']:.1f}h) · {', '.join(c['professors']) or '-'}")
        pdf.multi_cell(0, 6, f"Acordes ensinados: {c['diary_acordes'] or '-'}")
        pdf.multi_cell(0, 6, f"Exercícios rítmicos: {c['diary_exercicios'] or '-'}")
        pdf.multi_cell(0, 6, f"Repertório trabalhado: {c['diary_repertorio'] or '-'}")
        pdf.multi_cell(0, 6, f"Dinâmicas de grupo: {c['diary_dinamicas'] or '-'}")
        acc = ", ".join(c["access"]) or "-"
        if c["access_other"]:
            acc += f" · {c['access_other']}"
        pdf.multi_cell(0, 6, f"Acessibilidade: {acc}")
        pdf.ln(2)
    _section(pdf, f"Total geral de carga horária: {total_hours:.1f}h")
    return bytes(pdf.output())


# ------------------------------------------------------------------ #
# CSV
# ------------------------------------------------------------------ #
def students_csv(students):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Nome", "Nascimento", "Responsável", "Endereço", "Escola", "Autorização imagem/voz", "Status"])
    for s in students:
        w.writerow([s["name"], s["birth_date"], s["guardian_name"], s["address"], s["school"],
                    s["image_auth"], "Ativo" if s["active"] else "Inativo"])
    return buf.getvalue()


def classes_csv(classes):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Data", "Início", "Fim", "Horas", "Instrutores", "Presentes", "Total", "Validada"])
    attendance_rows = db.get_attendance_for_turma(classes[0]["turma_id"]) if classes else []
    for c in classes:
        att = [a for a in attendance_rows if a["class_id"] == c["id"]]
        present = len([a for a in att if a["present"]])
        w.writerow([c["date"], c["start_time"], c["end_time"], f"{c['hours']:.2f}",
                    " | ".join(c["professors"]), present, len(att), "Sim" if c["locked"] else "Não"])
    return buf.getvalue()


def attendance_csv(classes, students):
    student_names = {s["id"]: s["name"] for s in students}
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Data da aula", "Aluno", "Presente", "Justificativa"])
    class_dates = {c["id"]: c["date"] for c in classes}
    attendance_rows = db.get_attendance_for_turma(classes[0]["turma_id"]) if classes else []
    for a in attendance_rows:
        w.writerow([class_dates.get(a["class_id"]), student_names.get(a["student_id"], a["student_id"]),
                    "Sim" if a["present"] else "Não", a["justification"] or ""])
    return buf.getvalue()


# ------------------------------------------------------------------ #
# Anexo VI — Relatório de Execução Cultural
# ------------------------------------------------------------------ #
def anexo_vi_pdf(turma, report, metas, team, students, classes, event):
    pdf = _new_pdf("Anexo VI - Relatorio de Execucao Cultural", turma["name"])

    def field(label, value):
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.write(6, f"{label}: ")
        pdf.set_font("Helvetica", "", 10.5)
        pdf.write(6, value or "-")
        pdf.ln(7)

    _section(pdf, "1. Dados do projeto")
    field("Nome do projeto", turma["name"])
    field("Nome do agente cultural proponente", report.get("proponente"))
    field("Nº do Termo de Execução Cultural", report.get("termo_numero"))
    field("Vigência", f"{utils.fmt_date(report.get('vigencia_inicio'))} a {utils.fmt_date(report.get('vigencia_fim'))}")
    field("Valor repassado para o projeto", report.get("valor_repassado"))
    field("Data de entrega deste relatório", utils.fmt_date(report.get("data_entrega")))
    pdf.ln(2)

    _section(pdf, "2. Resultados do projeto")
    pdf.multi_cell(0, 6, f"Resumo: {report.get('resumo') or '-'}")
    pdf.ln(1)
    status_label = opt.ACOES_PLANEJADAS_OPTIONS.get(report.get("acoes_planejadas_status"), "-")
    pdf.multi_cell(0, 6, f"As ações planejadas foram realizadas? {status_label}")
    pdf.ln(1)
    pdf.multi_cell(0, 6, f"Ações desenvolvidas: {report.get('acoes_desenvolvidas') or '-'}")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10.5)
    pdf.cell(0, 7, "Cumprimento das metas", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10.5)
    if metas:
        for m in metas:
            label = opt.META_STATUS_OPTIONS.get(m["status"], m["status"])
            pdf.multi_cell(0, 6, f"- {m['descricao']} [{label}]")
            if m.get("observacao"):
                pdf.multi_cell(0, 6, f"  Observação: {m['observacao']}")
            if m.get("justificativa"):
                pdf.multi_cell(0, 6, f"  Justificativa: {m['justificativa']}")
            pdf.ln(1)
    else:
        pdf.multi_cell(0, 6, "Nenhuma meta cadastrada.")
    pdf.ln(2)

    _section(pdf, "3. Produtos gerados")
    field("A execução gerou algum produto?", "Sim" if report.get("gerou_produtos") != "nao" else "Não")
    produtos = report.get("produtos_gerados") or []
    if produtos:
        pdf.multi_cell(0, 6, "Produtos: " + "; ".join(f"{p['tipo']} ({p['quantidade'] or 's/qtd'})" for p in produtos))
    pdf.multi_cell(0, 6, f"Disponibilização ao público: {report.get('produtos_disponibilizacao') or '-'}")
    pdf.ln(2)
    pdf.multi_cell(0, 6, f"Resultados detalhados: {report.get('resultados_texto') or '-'}")
    resultados = report.get("resultados_checkboxes") or []
    if resultados:
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 6, "O projeto, entre outros pontos:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10.5)
        for r in resultados:
            pdf.multi_cell(0, 6, f"- {r}")
    pdf.ln(2)

    _section(pdf, "4. Público alcançado")
    attendance_rows = db.get_attendance_for_turma(turma["id"])
    total_att = len(attendance_rows)
    presentes_att = sum(1 for a in attendance_rows if a["present"])
    pct = round((presentes_att / total_att) * 100) if total_att else 0
    pdf.multi_cell(
        0, 6,
        f"{len(students)} aluno(s) ativo(s), mensurados por lista de presença digital em {len(classes)} "
        f"aula(s) registradas no sistema. Frequência média da turma: {pct}%."
        + (f" Público estimado no recital de encerramento: {event['audience']}." if event and event.get("audience") else "")
    )
    pdf.ln(2)

    _section(pdf, "5. Equipe do projeto")
    field("Quantidade de pessoas na equipe", str(len(team)))
    field("Houve mudanças na equipe?", "Sim" if report.get("equipe_mudancas") == "sim" else "Não")
    if report.get("equipe_mudancas_obs"):
        pdf.multi_cell(0, 6, f"Observações: {report['equipe_mudancas_obs']}")
    pdf.ln(2)
    if team:
        pdf.set_font("Helvetica", "B", 9.5)
        widths = [45, 35, 35, 35, 30]
        headers = ["Nome", "Função", "CPF/CNPJ", "Negra/Indígena", "Deficiência"]
        for w_, h_ in zip(widths, headers):
            pdf.cell(w_, 7, h_, border=1)
        pdf.ln(7)
        pdf.set_font("Helvetica", "", 9)
        for m in team:
            pdf.cell(widths[0], 7, (m["nome"] or "")[:26], border=1)
            pdf.cell(widths[1], 7, (m["funcao"] or "")[:20], border=1)
            pdf.cell(widths[2], 7, (m["cpf_cnpj"] or "")[:18], border=1)
            pdf.cell(widths[3], 7, (m["negra_indigena"] or "")[:20], border=1)
            pdf.cell(widths[4], 7, (m["deficiencia"] or "")[:16], border=1)
            pdf.ln(7)
    else:
        pdf.multi_cell(0, 6, "Nenhum integrante cadastrado.")
    pdf.ln(3)

    _section(pdf, "6. Locais de realização")
    field("Modo de acesso do público", opt.MODO_ACESSO_OPTIONS.get(report.get("modo_acesso"), "-"))
    plataformas = report.get("plataformas") or []
    if plataformas:
        field("Plataformas virtuais", ", ".join(plataformas))
        field("Links", report.get("links_plataformas"))
    field("Forma das atividades presenciais", opt.FORMA_PRESENCIAL_OPTIONS.get(report.get("forma_presencial"), "-"))
    field("Município e Estado", report.get("municipio_estado"))
    locais = report.get("locais_realizacao") or []
    if locais:
        field("Locais", ", ".join(locais))
    pdf.ln(2)

    _section(pdf, "7. Divulgação")
    pdf.multi_cell(0, 6, report.get("divulgacao") or "-")
    pdf.ln(2)

    if report.get("topicos_adicionais"):
        _section(pdf, "8. Tópicos adicionais")
        pdf.multi_cell(0, 6, report["topicos_adicionais"])
        pdf.ln(2)

    _section(pdf, "9. Anexos")
    pdf.multi_cell(
        0, 6,
        "Ficha do aluno e diário de bordo unificado são gerados separadamente na página Exportação "
        "e devem acompanhar este relatório, junto com listas de presença e outros registros comprobatórios."
    )

    return bytes(pdf.output())
