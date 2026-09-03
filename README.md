# Acordes de Lagoinha — Sistema de Gestão do Projeto

Aplicação em **Python + Streamlit** para o gestor e os professores do projeto
"Acordes de Lagoinha: Sons da Terra" (Edital PNAB — Berilo/MG) registrarem e
auditarem turmas, aulas, frequência, diário pedagógico, recital e a
prestação de contas (Anexo VI).

## Como as pessoas trabalham juntas

O gestor **cria a turma** e escolhe quais professores têm acesso a ela.
A partir daí, todos que entram nessa turma (gestor e professores vinculados)
enxergam os **mesmos alunos, as mesmas aulas e o mesmo diário** — o Kéviny
registra a aula 1, o Talison registra a aula 2, e as duas ficam juntas,
dentro da mesma turma, com o mesmo histórico de frequência.

Isso funciona porque todos os dados ficam em **um único banco de dados
compartilhado** (`data/acordes.db`), não em arquivos separados por pessoa.

O menu lateral só aparece depois do login, e mostra páginas diferentes
para cada perfil: professores veem Painel, Turmas, Alunos, Aulas e Recital;
o gestor vê essas mesmas páginas mais Auditoria, Exportação, Configurações
e Relatório Final. Essa restrição é aplicada em dois níveis — o menu nem
lista as páginas do gestor para um professor, e cada página sensível
também confere o perfil por conta própria antes de mostrar qualquer coisa.

> **Nota:** esta versão não inclui upload/registro de fotos — isso ficou de
> fora por enquanto, para manter o app leve e rápido, e pode ser tratado
> como um projeto à parte mais adiante.

## Estrutura do projeto

```
acordes-lagoinha/
├── app.py                      # tela de login (ponto de entrada)
├── db.py                       # banco de dados (SQLite) e todas as operações
├── utils.py                    # tema visual, seletor de turma, helpers
├── reports.py                  # geração de PDFs e planilhas CSV
├── anexo_options.py            # opções fixas do Relatório Final (Anexo VI)
├── requirements.txt
├── .streamlit/config.toml      # cores do tema (marrom/azul do projeto)
├── data/                       # banco de dados local (criado ao rodar)
└── pages/
    ├── 1_Painel.py              # dashboard (geral + por turma)
    ├── 2_Turmas.py              # gestor cria turmas e vincula professores
    ├── 3_Alunos.py              # cadastro de alunos da turma ativa
    ├── 4_Aulas.py               # diário de aulas e chamada
    ├── 5_Recital.py             # evento de encerramento
    ├── 6_Auditoria.py           # trilha de auditoria (gestor)
    ├── 7_Exportacao.py          # PDFs e CSVs para a prestação de contas (gestor)
    ├── 8_Configuracoes.py       # contas de acesso (gestor)
    └── 9_Relatorio_Final.py     # Relatório Final / Anexo VI completo (gestor)
```

## Como rodar no VS Code

1. Abra a pasta `acordes-lagoinha` no VS Code.
2. Crie um ambiente virtual (recomendado) e instale as dependências:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # no Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Rode o app:
   ```bash
   streamlit run app.py
   ```
4. O navegador abrirá em `http://localhost:8501`.

## Como os dois professores trabalham na mesma máquina/rede

- **Testando localmente**: cada pessoa acessa `http://localhost:8501` na
  própria máquina onde o `streamlit run app.py` está rodando.
- **Vários computadores na mesma rede (mesma casa/escritório)**: rode
  `streamlit run app.py --server.address 0.0.0.0` no computador que vai
  hospedar o app, e os demais acessam pelo IP dessa máquina na rede local,
  ex.: `http://192.168.0.10:8501`.
- **Acesso de qualquer lugar** (Kéviny e Talison em casas diferentes): hospede
  o projeto em um servidor ou no [Streamlit Community Cloud](https://streamlit.io/cloud)
  (gratuito para projetos assim). Nesse caso, todos acessam a mesma URL
  pública e o mesmo banco de dados.

  **Atenção**: no plano gratuito do Streamlit Community Cloud, o
  armazenamento em disco não é garantido como permanente — se o app
  reiniciar (fica inativo por vários dias, ou você atualiza o código), o
  arquivo `data/acordes.db` pode ser apagado. Enquanto isso for só para
  testes, não tem problema; para uso real e contínuo, vale considerar migrar
  para um banco externo permanente (Postgres via Supabase/Neon, por
  exemplo) mais adiante, como um projeto separado.

## Primeiro acesso

Já vêm cadastradas três contas: **Kéviny** e **Talison** (professores) e
**Nícolas** (gestor). Na primeira vez que cada um entra, o sistema pede para
**criar uma senha própria**; nos acessos seguintes, só pede a senha.

Se alguém esquecer a senha, o gestor pode redefinir o acesso na página
**Configurações** — a pessoa cria uma senha nova no próximo login.

## Relatório Final (Anexo VI)

A página **Relatório Final** (gestor) segue a estrutura oficial do Anexo VI —
Relatório de Execução Cultural da PNAB: dados do termo, cumprimento de
metas, produtos gerados, resultados, público alcançado, equipe do projeto
(com raça/etnia e deficiência), locais de realização e divulgação. O
público alcançado e a frequência são calculados automaticamente a partir
dos dados já cadastrados em Alunos e Aulas. Ao final, gera um PDF único
com todas essas seções, para revisar e anexar (ou usar como base para
preencher) o Anexo VI oficial — os anexos comprobatórios (ficha do aluno,
diário de bordo) continuam sendo gerados separadamente em **Exportação**.

## Uso pelo celular

O app foi ajustado para funcionar bem no celular, já que é assim que os
professores costumam registrar as aulas em campo: os formulários (chamada,
diário) empilham em coluna única, os botões ficam em largura total (fáceis
de tocar) e o menu lateral vira uma gaveta que abre pelo ícone `»` no canto
superior esquerdo — toque nele para navegar entre as páginas e novamente
para fechar.

## Passo a passo recomendado

1. **Nícolas (gestor)** entra, vai em **Turmas**, cria a turma do projeto e
   marca **Kéviny** e **Talison** como professores vinculados.
2. Em **Alunos**, cadastra (ou pede para os professores cadastrarem) os
   participantes.
3. **Kéviny** e **Talison** entram, escolhem a turma no seletor da barra
   lateral e registram as aulas em **Aulas / Diário**, cada um no seu dia,
   dentro da mesma turma.
4. O gestor acompanha tudo em **Painel**, valida e trava as aulas conforme
   forem concluídas, e confere a trilha em **Auditoria**.
5. Ao final, gera os documentos em **Exportação** e o **Relatório Final**
   (PDFs prontos + CSVs).

## Backup

Todos os dados (turmas, alunos, aulas) ficam na pasta `data/`. Faça backup
periódico dessa pasta — ela é o "banco de dados" inteiro do projeto. A
página **Exportação** também gera PDFs e CSVs de tudo o que importa para a
prestação de contas — guardar esses arquivos periodicamente já serve como
uma cópia de segurança adicional dos dados essenciais.

## Solução de problemas comuns

**`Could not open requirements file: No such file or directory`**
Isso significa que o terminal não está dentro da pasta do projeto. Rode `ls`
(ou `dir` no Windows) para ver o que tem na pasta atual; se não aparecer
`app.py` e `requirements.txt`, use `cd nome-da-pasta` até entrar na pasta
certa (a que contém `app.py`), ou no VS Code clique com o botão direito na
pasta do projeto no painel do Explorer e escolha "Open in Integrated
Terminal".

**A página abre em branco ou trava**
Confira o terminal onde rodou `streamlit run app.py` — qualquer erro do
Python aparece lá, mesmo que a página no navegador não mostre nada.

**Mudei algo no código e não vejo a mudança**
O Streamlit recarrega sozinho, mas às vezes é preciso apertar "R" no
navegador ou clicar em "Rerun" no canto superior direito.

## Observação sobre segurança

As senhas ficam com hash (PBKDF2) no banco local, mas este não é um sistema
com infraestrutura de segurança de nível empresarial. Como os dados
envolvem crianças e adolescentes, mantenha o acesso ao computador/servidor
restrito à equipe do projeto e faça backups em local seguro.
