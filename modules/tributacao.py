"""
PRIORIDADE 1 — Tributação (NCM / CST)

Busca os produtos no Tiny, compara os campos fiscais com as regras
definidas em config/regras_tributacao.json e:

  - modo dry-run (padrão): só REPORTA as divergências encontradas
  - modo aplicar (--aplicar no main.py): CORRIGE via API as divergências

IMPORTANTE: os nomes de campo abaixo (ncm, cest, origem, cst_icms...)
seguem o padrão mais comum da documentação pública da API v3 do Tiny,
mas o Tiny pode ter pequenas variações de nome/estrutura por conta. Por
isso a primeira execução (`python main.py --diagnostico`) só imprime um
produto "cru" (JSON completo) para conferirmos juntos os nomes exatos
antes de rodar em massa.
"""
import json
from pathlib import Path

import config as cfg

REGRAS_PATH = Path(__file__).resolve().parent.parent / "config" / "regras_tributacao.json"


def carregar_regras() -> dict:
    return json.loads(REGRAS_PATH.read_text(encoding="utf-8"))


def _regra_para_produto(produto: dict, regras: dict) -> dict:
    """Decide qual regra vale para este produto: por SKU > por categoria > padrão."""
    sku = produto.get("sku") or produto.get("codigo")
    categoria = (produto.get("categoria") or {}).get("nome") if isinstance(produto.get("categoria"), dict) else produto.get("categoria")

    regra = dict(regras.get("regra_padrao", {}))
    if categoria and categoria in regras.get("por_categoria", {}):
        regra.update(regras["por_categoria"][categoria])
    if sku and sku in regras.get("por_sku", {}):
        regra.update(regras["por_sku"][sku])
    return regra


def _campos_divergentes(produto: dict, regra: dict) -> dict:
    """Retorna {campo: (valor_atual, valor_esperado)} só para os campos que batem errado."""
    divergencias = {}
    for campo, valor_esperado in regra.items():
        valor_atual = produto.get(campo)
        if str(valor_atual) != str(valor_esperado):
            divergencias[campo] = (valor_atual, valor_esperado)
    return divergencias


def diagnosticar_um_produto(client) -> dict:
    """Traz só 1 produto para inspecionarmos a estrutura real de campos."""
    produtos = client.listar_todas_paginas("/produtos", params={"limit": 1})
    return produtos[0] if produtos else {}


def rodar(client, aplicar: bool = False) -> list:
    """
    Executa a checagem de tributação em todo o catálogo.
    Retorna a lista de relatórios (1 por produto com divergência).
    """
    regras = carregar_regras()
    produtos = client.listar_todas_paginas("/produtos")
    relatorio = []

    for produto in produtos:
        regra = _regra_para_produto(produto, regras)
        divergencias = _campos_divergentes(produto, regra)
        if not divergencias:
            continue

        item = {
            "id": produto.get("id"),
            "sku": produto.get("sku") or produto.get("codigo"),
            "nome": produto.get("nome") or produto.get("descricao"),
            "divergencias": divergencias,
            "corrigido": False,
        }

        if aplicar:
            payload = {campo: esperado for campo, (atual, esperado) in divergencias.items()}
            client.put(f"/produtos/{produto['id']}/tributacao", json_body=payload)
            item["corrigido"] = True

        relatorio.append(item)

    return relatorio
