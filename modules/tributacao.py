"""
PRIORIDADE 1 — Tributação (NCM / origem / dados de IPI)

Busca os produtos no Tiny, compara os campos fiscais com as regras
definidas em config/regras_tributacao.json e:

  - modo dry-run (padrão): só REPORTA as divergências encontradas
  - modo aplicar (--aplicar no main.py): CORRIGE via API as divergências

IMPORTANTE (confirmado na documentação oficial da API v3): o Tiny NÃO expõe
CST de ICMS/PIS/COFINS como campo de produto nesta API — isso é calculado
na nota fiscal, não fica salvo no cadastro do produto. Os campos realmente
editáveis por produto são:
  - ncm (raiz do produto)
  - origem (raiz do produto, string "0" a "8")
  - dentro de "tributacao": classeIPI, valorIPIFixo, gtinEmbalagem

A listagem de produtos (GET /produtos) não traz esses detalhes — por isso
buscamos o produto completo (GET /produtos/{id}) um por um. Isso consome
mais chamadas da sua cota por minuto (confira os limites do seu plano em
Minha conta > Aplicativos), então para catálogos grandes rode com calma.
"""
import json
from pathlib import Path

REGRAS_PATH = Path(__file__).resolve().parent.parent / "config" / "regras_tributacao.json"

CAMPOS_RAIZ = ("ncm", "origem", "gtin", "unidade")


def carregar_regras() -> dict:
    return json.loads(REGRAS_PATH.read_text(encoding="utf-8"))


def _regra_para_produto(produto: dict, regras: dict) -> dict:
    sku = produto.get("sku")
    categoria = (produto.get("categoria") or {}).get("nome")

    regra = dict(regras.get("regra_padrao", {}))
    if categoria and categoria in regras.get("por_categoria", {}):
        regra.update(regras["por_categoria"][categoria])
    if sku and sku in regras.get("por_sku", {}):
        regra.update(regras["por_sku"][sku])
    return regra


def _valor_atual(produto: dict, campo: str):
    if campo in CAMPOS_RAIZ:
        return produto.get(campo)
    return (produto.get("tributacao") or {}).get(campo)


def _campos_divergentes(produto: dict, regra: dict) -> dict:
    divergencias = {}
    for campo, valor_esperado in regra.items():
        valor_atual = _valor_atual(produto, campo)
        if str(valor_atual) != str(valor_esperado):
            divergencias[campo] = (valor_atual, valor_esperado)
    return divergencias


def diagnosticar_um_produto(client) -> dict:
    resumos = client.listar_todas_paginas("/produtos", params={"limit": 1})
    if not resumos:
        return {}
    return client.get(f"/produtos/{resumos[0]['id']}")


def rodar(client, aplicar: bool = False) -> list:
    regras = carregar_regras()
    resumos = client.listar_todas_paginas("/produtos")
    relatorio = []

    for resumo in resumos:
        produto = client.get(f"/produtos/{resumo['id']}")
        regra = _regra_para_produto(produto, regras)
        divergencias = _campos_divergentes(produto, regra)
        if not divergencias:
            continue

        item = {
            "id": produto.get("id"),
            "sku": produto.get("sku"),
            "descricao": produto.get("descricao"),
            "divergencias": divergencias,
            "corrigido": False,
        }

        if aplicar:
            payload = {"sku": produto.get("sku"), "descricao": produto.get("descricao")}
            tributacao_payload = {}
            for campo, (_atual, esperado) in divergencias.items():
                if campo in CAMPOS_RAIZ:
                    payload[campo] = esperado
                else:
                    tributacao_payload[campo] = esperado
            if tributacao_payload:
                payload["tributacao"] = tributacao_payload

            client.put(f"/produtos/{produto['id']}", json_body=payload)
            item["corrigido"] = True

        relatorio.append(item)

    return relatorio
