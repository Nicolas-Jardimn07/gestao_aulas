"""Opções de múltipla escolha do Anexo VI (Relatório de Execução Cultural — PNAB), compartilhadas
entre a página de preenchimento e a geração do PDF."""

ACOES_PLANEJADAS_OPTIONS = {
    "todas_planejado": "Sim, todas as ações foram feitas conforme o planejado.",
    "todas_adaptacoes": "Sim, todas as ações foram feitas, mas com adaptações e/ou alterações.",
    "parte_nao_feita": "Uma parte das ações planejadas não foi feita.",
    "nao_conforme": "As ações não foram feitas conforme o planejado.",
}

META_STATUS_OPTIONS = {
    "integral": "Cumprida integralmente",
    "parcial": "Cumprida parcialmente",
    "nao_cumprida": "Não cumprida",
}

PRODUTO_TIPOS = [
    "Publicação", "Livro", "Catálogo", "Live (transmissão on-line)", "Vídeo", "Documentário",
    "Filme", "Relatório de pesquisa", "Produção musical", "Jogo", "Artesanato", "Obras",
    "Espetáculo", "Show musical", "Site", "Música", "Outros",
]

RESULTADOS_OPTIONS = [
    "Desenvolveu processos de criação, de investigação ou de pesquisa.",
    "Desenvolveu estudos, pesquisas e análises sobre o contexto de atuação.",
    "Colaborou para manter as atividades culturais do coletivo.",
    "Fortaleceu a identidade cultural do coletivo.",
    "Promoveu as práticas culturais do coletivo no espaço em que foi desenvolvido.",
    "Promoveu a formação em linguagens, técnicas e práticas artísticas e culturais.",
    "Ofereceu programações artísticas e culturais para a comunidade do entorno.",
    "Atuou na preservação, na proteção e na salvaguarda de bens e manifestações culturais.",
]

MODO_ACESSO_OPTIONS = {
    "presencial": "Presencial",
    "virtual": "Virtual",
    "hibrido": "Híbrido (presencial e virtual)",
}

PLATAFORMAS_OPTIONS = ["YouTube", "Instagram / IGTV", "Facebook", "TikTok", "Google Meet, Zoom etc.", "Outros"]

FORMA_PRESENCIAL_OPTIONS = {
    "fixas": "Fixas, sempre no mesmo local.",
    "itinerantes": "Itinerantes, em diferentes locais.",
    "principal_base": "Principalmente em um local base, mas com ações também em outros locais.",
}

LOCAIS_OPTIONS = [
    "Equipamento cultural público municipal", "Equipamento cultural público estadual",
    "Espaço cultural independente", "Escola", "Praça", "Rua", "Parque", "Outros",
]
