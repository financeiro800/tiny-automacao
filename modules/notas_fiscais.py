"""
PRIORIDADE 2 — Notas fiscais (NF-e)

DECISAO: a geracao/autorizacao da nota fiscal a partir do pedido fica por
conta da automacao NATIVA do Tiny (Configuracoes > Notas Fiscais >
Automacoes > "Gerar nota fiscal automaticamente ao aprovar pedido" +
"Autorizar automaticamente notas fiscais geradas a partir da venda"),
em vez de um script customizado aqui. Esse modulo fica como stub
intencionalmente vazio - o trabalho relevante deste projeto pra notas
fiscais e indireto: o modulo de tributacao (prioridade 1) mantem NCM e
origem corretos no produto ANTES do pedido ser aprovado, que e o dado
que a nota gerada automaticamente pelo Tiny vai usar.
"""


def rodar(client, aplicar: bool = False) -> list:
    return []
