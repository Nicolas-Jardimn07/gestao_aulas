import streamlit as st

import anexo_options as opt
import db
import reports
import utils

utils.inject_css()
user = utils.require_login()

if user["role"] != "gestor":
    st.error("Esta página é restrita ao perfil Gestor(a) / Auditor.")
    st.stop()

turma = utils.turma_switcher(user)

st.title("Relatório Final (Anexo VI)")
st.caption(
    f"Turma ativa: **{turma['name']}** — preencha aqui os dados exigidos pelo Relatório de Execução Cultural "
    "da PNAB. Os dados de frequência, aulas e evidências já cadastrados no sistema alimentam partes deste "
    "relatório automaticamente."
)

report = db.get_project_report(turma["id"]) or {}
students = db.get_students(turma["id"])
active_students = [s for s in students if s["active"]]
classes = db.get_classes(turma["id"])
team = db.get_team_members(turma["id"])
metas = db.get_metas(turma["id"])
event = db.get_final_event(turma["id"])

tabs = st.tabs([
    "1. Dados do Termo", "2. Metas e Ações", "3. Produtos e Resultados",
    "4-5. Público e Equipe", "6-7. Locais e Divulgação", "8. Tópicos Adicionais", "Gerar PDF",
])

# ------------------------------------------------------------------ #
# 1. Dados do termo
# ------------------------------------------------------------------ #
with tabs[0]:
    with st.form("form_dados_termo"):
        c1, c2 = st.columns(2)
        with c1:
            proponente = st.text_input("Nome do agente cultural proponente", value=report.get("proponente") or "")
            termo_numero = st.text_input("Nº do Termo de Execução Cultural", value=report.get("termo_numero") or "")
            valor_repassado = st.text_input("Valor repassado para o projeto", value=report.get("valor_repassado") or "")
        with c2:
            vig_inicio = st.text_input("Vigência — início (AAAA-MM-DD)", value=report.get("vigencia_inicio") or "")
            vig_fim = st.text_input("Vigência — fim (AAAA-MM-DD)", value=report.get("vigencia_fim") or "")
            data_entrega = st.text_input("Data de entrega deste relatório (AAAA-MM-DD)", value=report.get("data_entrega") or "")
        resumo = st.text_area(
            "Resumo da execução do projeto",
            value=report.get("resumo") or "",
            help="Descreva de forma resumida como foi a execução do projeto, principais resultados e benefícios gerados.",
            height=140,
        )
        acoes_status = st.radio(
            "As ações planejadas para o projeto foram realizadas?",
            list(opt.ACOES_PLANEJADAS_OPTIONS.keys()),
            index=list(opt.ACOES_PLANEJADAS_OPTIONS.keys()).index(report["acoes_planejadas_status"])
            if report.get("acoes_planejadas_status") in opt.ACOES_PLANEJADAS_OPTIONS else 0,
            format_func=lambda k: opt.ACOES_PLANEJADAS_OPTIONS[k],
        )
        acoes_dev = st.text_area(
            "Ações desenvolvidas (datas, locais, horários, alterações em relação ao planejado)",
            value=report.get("acoes_desenvolvidas") or "", height=140,
        )
        if st.form_submit_button("Salvar dados do termo", use_container_width=True):
            db.upsert_project_report(
                turma["id"], proponente=proponente.strip(), termo_numero=termo_numero.strip(),
                valor_repassado=valor_repassado.strip(), vigencia_inicio=vig_inicio.strip(),
                vigencia_fim=vig_fim.strip(), data_entrega=data_entrega.strip(), resumo=resumo,
                acoes_planejadas_status=acoes_status, acoes_desenvolvidas=acoes_dev,
            )
            db.log_action(turma["id"], user["id"], user["name"], user["role"], "Atualizou os dados do termo no Relatório Final")
            st.success("Dados salvos.")
            st.rerun()

# ------------------------------------------------------------------ #
# 2. Metas
# ------------------------------------------------------------------ #
with tabs[1]:
    st.markdown("#### Cumprimento das metas")
    st.caption("Cadastre cada meta do projeto (conforme consta na proposta) e o status de cumprimento.")
    with st.container(border=True):
        if metas:
            for m in metas:
                c1, c2, c3 = st.columns([3, 1.3, 0.6])
                c1.write(f"**{m['descricao']}**")
                c1.caption(m.get("observacao") or m.get("justificativa") or "")
                status_label = opt.META_STATUS_OPTIONS.get(m["status"], m["status"])
                badge_class = "ok" if m["status"] == "integral" else ("warn" if m["status"] == "nao_cumprida" else "muted")
                c2.markdown(f'<span class="badge {badge_class}">{status_label}</span>', unsafe_allow_html=True)
                if c3.button("Remover", key=f"del_meta_{m['id']}"):
                    db.delete_meta(m["id"])
                    st.rerun()
                st.markdown("---")
        else:
            st.info("Nenhuma meta cadastrada ainda.")

    with st.form("form_nova_meta", clear_on_submit=True):
        st.markdown("##### Adicionar meta")
        desc = st.text_area("Descrição da meta (conforme consta no projeto apresentado)")
        status = st.selectbox("Status", list(opt.META_STATUS_OPTIONS.keys()), format_func=lambda k: opt.META_STATUS_OPTIONS[k])
        obs = st.text_input("Observação (como a meta foi cumprida / qual parte foi cumprida)")
        just = st.text_input("Justificativa (apenas se parcial ou não cumprida)")
        if st.form_submit_button("Adicionar meta", use_container_width=True):
            if not desc.strip():
                st.error("Descreva a meta antes de adicionar.")
            else:
                db.add_meta(turma["id"], desc.strip(), status, obs.strip(), just.strip())
                db.log_action(turma["id"], user["id"], user["name"], user["role"], f"Adicionou meta ao Relatório Final: {desc.strip()[:60]}")
                st.rerun()

# ------------------------------------------------------------------ #
# 3. Produtos e resultados
# ------------------------------------------------------------------ #
with tabs[2]:
    with st.form("form_produtos"):
        st.markdown("#### Produtos gerados")
        gerou = st.radio("A execução do projeto gerou algum produto?", ["sim", "nao"],
                          index=0 if report.get("gerou_produtos") != "nao" else 1,
                          format_func=lambda v: "Sim" if v == "sim" else "Não")
        produtos_existentes = {p["tipo"]: p["quantidade"] for p in (report.get("produtos_gerados") or [])}
        produtos_novos = []
        cols = st.columns(3)
        for i, tipo in enumerate(opt.PRODUTO_TIPOS):
            with cols[i % 3]:
                marcado = tipo in produtos_existentes
                check = st.checkbox(tipo, value=marcado, key=f"prod_{tipo}")
                qtd = st.text_input("Quantidade", value=produtos_existentes.get(tipo, ""), key=f"prod_qtd_{tipo}",
                                     label_visibility="collapsed", placeholder="Quantidade")
                if check:
                    produtos_novos.append({"tipo": tipo, "quantidade": qtd})
        disponibilizacao = st.text_area(
            "Como os produtos ficaram disponíveis para o público após o fim do projeto?",
            value=report.get("produtos_disponibilizacao") or "",
        )

        st.markdown("#### Resultados gerados pelo projeto")
        resultados_texto = st.text_area(
            "Detalhe os resultados gerados por cada atividade prevista no projeto",
            value=report.get("resultados_texto") or "",
        )
        resultados_existentes = report.get("resultados_checkboxes") or []
        resultados_marcados = []
        for r in opt.RESULTADOS_OPTIONS:
            if st.checkbox(r, value=(r in resultados_existentes), key=f"res_{r}"):
                resultados_marcados.append(r)

        if st.form_submit_button("Salvar produtos e resultados", use_container_width=True):
            db.upsert_project_report(
                turma["id"], gerou_produtos=gerou, produtos_gerados=produtos_novos,
                produtos_disponibilizacao=disponibilizacao, resultados_texto=resultados_texto,
                resultados_checkboxes=resultados_marcados,
            )
            db.log_action(turma["id"], user["id"], user["name"], user["role"], "Atualizou produtos e resultados no Relatório Final")
            st.success("Salvo.")
            st.rerun()

# ------------------------------------------------------------------ #
# 4-5. Público e equipe
# ------------------------------------------------------------------ #
with tabs[3]:
    st.markdown("#### Público alcançado")
    attendance_rows = db.get_attendance_for_turma(turma["id"])
    total_att = len(attendance_rows)
    presentes_att = sum(1 for a in attendance_rows if a["present"])
    pct = round((presentes_att / total_att) * 100) if total_att else 0
    st.info(
        f"Calculado automaticamente a partir do sistema: **{len(active_students)}** aluno(s) ativo(s), "
        f"mecanismo de mensuração: lista de presença digital (chamada em cada aula, {len(classes)} aula(s) registradas). "
        f"Frequência média da turma: {pct}%."
        + (f" Público estimado no recital de encerramento: {event['audience']}." if event and event.get("audience") else "")
    )

    st.markdown("#### Equipe do projeto")
    st.caption("Inclua todas as pessoas que participaram da execução (instrutores, gestor, colaboradores).")
    with st.container(border=True):
        if team:
            for m in team:
                c1, c2, c3, c4, c5, c6 = st.columns([1.6, 1.4, 1.3, 1.3, 1.3, 0.6])
                c1.write(f"**{m['nome']}**")
                c2.write(m["funcao"] or "—")
                c3.write(m["cpf_cnpj"] or "—")
                c4.write(m["negra_indigena"] or "—")
                c5.write(m["deficiencia"] or "—")
                if c6.button("Remover", key=f"del_team_{m['id']}"):
                    db.delete_team_member(m["id"])
                    st.rerun()
        else:
            st.info("Nenhum integrante cadastrado ainda.")

    with st.form("form_novo_membro", clear_on_submit=True):
        st.markdown("##### Adicionar integrante da equipe")
        c1, c2 = st.columns(2)
        with c1:
            nome_m = st.text_input("Nome do profissional/empresa")
            funcao_m = st.text_input("Função no projeto")
        with c2:
            cpf_m = st.text_input("CPF/CNPJ")
        c3, c4 = st.columns(2)
        with c3:
            negra_m = st.text_input("Pessoa negra ou indígena?", placeholder="Ex.: Sim, negra / Não")
        with c4:
            def_m = st.text_input("Pessoa com deficiência?", placeholder="Ex.: Sim, visual / Não")
        if st.form_submit_button("Adicionar", use_container_width=True):
            if not nome_m.strip():
                st.error("Informe o nome.")
            else:
                db.add_team_member(turma["id"], nome_m.strip(), funcao_m.strip(), cpf_m.strip(), negra_m.strip(), def_m.strip())
                db.log_action(turma["id"], user["id"], user["name"], user["role"], f"Adicionou {nome_m.strip()} à equipe do projeto")
                st.rerun()

    st.markdown("#### Mudanças na equipe")
    with st.form("form_equipe_mudancas"):
        mudou = st.radio("Houve mudanças na equipe ao longo da execução do projeto?", ["nao", "sim"],
                          index=1 if report.get("equipe_mudancas") == "sim" else 0,
                          format_func=lambda v: "Sim" if v == "sim" else "Não")
        mudou_obs = st.text_area("Se sim, informe quem entrou ou saiu da equipe", value=report.get("equipe_mudancas_obs") or "")
        if st.form_submit_button("Salvar", use_container_width=True):
            db.upsert_project_report(turma["id"], equipe_mudancas=mudou, equipe_mudancas_obs=mudou_obs)
            db.log_action(turma["id"], user["id"], user["name"], user["role"], "Atualizou informações da equipe no Relatório Final")
            st.success("Salvo.")
            st.rerun()

# ------------------------------------------------------------------ #
# 6-7. Locais e divulgação
# ------------------------------------------------------------------ #
with tabs[4]:
    with st.form("form_locais"):
        st.markdown("#### Locais de realização")
        modo = st.radio("De que modo o público acessou a ação ou o produto cultural do projeto?",
                         list(opt.MODO_ACESSO_OPTIONS.keys()),
                         index=list(opt.MODO_ACESSO_OPTIONS.keys()).index(report["modo_acesso"])
                         if report.get("modo_acesso") in opt.MODO_ACESSO_OPTIONS else 0,
                         format_func=lambda k: opt.MODO_ACESSO_OPTIONS[k])

        plataformas_existentes = report.get("plataformas") or []
        plataformas_marcadas = []
        st.write("Plataformas virtuais usadas (se aplicável):")
        cols = st.columns(3)
        for i, p in enumerate(opt.PLATAFORMAS_OPTIONS):
            with cols[i % 3]:
                if st.checkbox(p, value=(p in plataformas_existentes), key=f"plat_{p}"):
                    plataformas_marcadas.append(p)
        links = st.text_input("Links dessas plataformas", value=report.get("links_plataformas") or "")

        forma = st.radio("Forma das ações e atividades presenciais (se aplicável)",
                          list(opt.FORMA_PRESENCIAL_OPTIONS.keys()),
                          index=list(opt.FORMA_PRESENCIAL_OPTIONS.keys()).index(report["forma_presencial"])
                          if report.get("forma_presencial") in opt.FORMA_PRESENCIAL_OPTIONS else 0,
                          format_func=lambda k: opt.FORMA_PRESENCIAL_OPTIONS[k])
        municipio = st.text_input("Município e Estado onde o projeto aconteceu",
                                   value=report.get("municipio_estado") or "Berilo/MG")

        locais_existentes = report.get("locais_realizacao") or []
        locais_marcados = []
        st.write("Onde o projeto foi realizado:")
        cols2 = st.columns(3)
        for i, loc in enumerate(opt.LOCAIS_OPTIONS):
            with cols2[i % 3]:
                if st.checkbox(loc, value=(loc in locais_existentes), key=f"loc_{loc}"):
                    locais_marcados.append(loc)

        st.markdown("#### Divulgação")
        divulgacao = st.text_area("Informe como o projeto foi divulgado", value=report.get("divulgacao") or "")

        if st.form_submit_button("Salvar locais e divulgação", use_container_width=True):
            db.upsert_project_report(
                turma["id"], modo_acesso=modo, plataformas=plataformas_marcadas, links_plataformas=links,
                forma_presencial=forma, municipio_estado=municipio.strip(), locais_realizacao=locais_marcados,
                divulgacao=divulgacao,
            )
            db.log_action(turma["id"], user["id"], user["name"], user["role"], "Atualizou locais e divulgação no Relatório Final")
            st.success("Salvo.")
            st.rerun()

# ------------------------------------------------------------------ #
# 8. Tópicos adicionais
# ------------------------------------------------------------------ #
with tabs[5]:
    with st.form("form_topicos"):
        topicos = st.text_area(
            "Informações relevantes que não foram abordadas nos tópicos anteriores (se houver)",
            value=report.get("topicos_adicionais") or "", height=160,
        )
        if st.form_submit_button("Salvar", use_container_width=True):
            db.upsert_project_report(turma["id"], topicos_adicionais=topicos)
            db.log_action(turma["id"], user["id"], user["name"], user["role"], "Atualizou tópicos adicionais no Relatório Final")
            st.success("Salvo.")
            st.rerun()

# ------------------------------------------------------------------ #
# Gerar PDF
# ------------------------------------------------------------------ #
with tabs[6]:
    st.markdown("#### Relatório de Execução Cultural — Anexo VI")
    st.caption(
        "Gera um PDF com todos os dados preenchidos nas abas anteriores, organizado na mesma estrutura do "
        "formulário oficial da PNAB, pronto para revisar e anexar (ou copiar) ao Anexo VI."
    )
    report_now = db.get_project_report(turma["id"]) or {}
    team_now = db.get_team_members(turma["id"])
    metas_now = db.get_metas(turma["id"])
    pdf_bytes = reports.anexo_vi_pdf(turma, report_now, metas_now, team_now, active_students, classes, event)
    st.download_button("Baixar Relatório Final em PDF", data=pdf_bytes,
                        file_name=f"anexo_vi_{turma['name'].replace(' ', '_')}.pdf", mime="application/pdf",
                        use_container_width=True)
    st.caption(
        "Lembrete: a ficha de alunos e o diário de bordo (anexos comprobatórios) são gerados "
        "separadamente na página Exportação."
    )
