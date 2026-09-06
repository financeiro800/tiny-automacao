"""
Script principal da integração com o Tiny/Olist.

Uso:
  python main.py --diagnostico   # mostra 1 produto "cru" p/ conferirmos os campos
  python main.py                 # roda em modo simulação (só reporta, não altera nada)
  python main.py --aplicar       # roda de verdade e aplica as correções

Para automação diária, agende este comando (sem --aplicar até você validar
os primeiros relatórios, depois com --aplicar) no cron (Linux/Mac) ou no
Agendador de Tarefas (Windows). Exemplo de cron rodando todo dia às 7h:

  0 7 * * * cd /caminho/do/projeto && /usr/bin/python3 main.py --aplicar >> logs/cron.log 2>&1
"""
import argparse
import json
from datetime import datetime

from client import TinyClient
from modules import tributacao, notas_fiscais, pedidos, produtos
import config as cfg


def salvar_log(nome: str, dados: dict):
    caminho = cfg.LOG_DIR / f"{nome}_{datetime.now():%Y-%m-%d_%H%M%S}.json"
    caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"[log] relatório salvo em {caminho}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true", help="Aplica as correções de verdade (padrão é só simular)")
    parser.add_argument("--diagnostico", action="store_true", help="Mostra 1 produto cru da API para conferir os nomes de campo")
    args = parser.parse_args()

    client = TinyClient()

    if args.diagnostico:
        produto_exemplo = tributacao.diagnosticar_um_produto(client)
        print(json.dumps(produto_exemplo, indent=2, ensure_ascii=False))
        return

    modo = "APLICANDO CORREÇÕES" if args.aplicar else "SIMULAÇÃO (nada será alterado)"
    print(f"=== Rodando integração Tiny/Olist — {modo} — {datetime.now():%d/%m/%Y %H:%M} ===")

    resultado = {
        "executado_em": datetime.now().isoformat(),
        "modo": "aplicar" if args.aplicar else "simulacao",
        "tributacao": tributacao.rodar(client, aplicar=args.aplicar),
        "notas_fiscais": notas_fiscais.rodar(client, aplicar=args.aplicar),
        "pedidos": pedidos.rodar(client, aplicar=args.aplicar),
        "produtos": produtos.rodar(client, aplicar=args.aplicar),
    }

    print(f"\nTributação: {len(resultado['tributacao'])} produto(s) com divergência")
    print(f"Notas fiscais: {len(resultado['notas_fiscais'])} item(ns)")
    print(f"Pedidos: {len(resultado['pedidos'])} item(ns)")
    print(f"Produtos: {len(resultado['produtos'])} item(ns)")

    salvar_log("relatorio_diario", resultado)


if __name__ == "__main__":
    main()
