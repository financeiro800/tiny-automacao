"""
PRIORIDADE 2 — Notas fiscais (NF-e)

Esqueleto pronto para a próxima etapa. Endpoints já confirmados na API v3
(categoria "Notas Fiscais", 18 rotas: emissão, consulta, XML, cancelamento).

Ideias de automação para detalharmos juntos:
  - Listar pedidos faturados sem NF-e emitida e emitir automaticamente
  - Checar notas rejeitadas pela SEFAZ e reenviar após correção
  - Baixar XML/DANFE das notas do dia para arquivamento
"""


def rodar(client, aplicar: bool = False) -> list:
    # TODO: implementar na próxima fase, junto com você definindo as regras
    # de quando uma nota deve ser emitida/reemitida automaticamente.
    return []
