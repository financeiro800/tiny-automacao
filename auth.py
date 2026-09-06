"""
Autenticação OAuth2 com a API v3 do Tiny/Olist.

A API v3 usa OAuth2 (Authorization Code + Refresh Token), não mais o
token fixo da API v2. O fluxo é:

  1) Uma única vez, manualmente: autorizar a aplicação no navegador e
     trocar o "code" retornado por um refresh_token (função
     `autorizacao_inicial`, chamada via `python auth.py`).
  2) Nas execuções diárias automáticas: usar o refresh_token salvo para
     gerar um access_token novo a cada rodada (função `get_access_token`,
     usada pelo client.py). O access_token dura pouco (geralmente ~1h),
     por isso ele é sempre renovado a cada execução do script.
"""
import os
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs

import requests

import config


def _salvar_refresh_token_no_env(refresh_token: str):
    """Grava/atualiza a linha TINY_REFRESH_TOKEN no arquivo .env."""
    env_path = config.BASE_DIR / ".env"
    linhas = []
    if env_path.exists():
        linhas = env_path.read_text().splitlines()

    achou = False
    for i, linha in enumerate(linhas):
        if linha.startswith("TINY_REFRESH_TOKEN="):
            linhas[i] = f"TINY_REFRESH_TOKEN={refresh_token}"
            achou = True
            break
    if not achou:
        linhas.append(f"TINY_REFRESH_TOKEN={refresh_token}")

    env_path.write_text("\n".join(linhas) + "\n")
    print("[auth] refresh_token salvo em .env — não precisa repetir esse passo.")


def _persistir_novo_refresh_token(refresh_token: str):
    """
    Local (sua máquina): grava no .env, como antes.
    GitHub Actions: o runner é descartado a cada execução, então salvamos
    como Secret do repositório via API (veja github_secrets.py).
    """
    if os.environ.get("GITHUB_ACTIONS") == "true":
        import github_secrets
        github_secrets.salvar_secret("TINY_REFRESH_TOKEN", refresh_token)
    else:
        _salvar_refresh_token_no_env(refresh_token)


def trocar_code_por_tokens(code: str) -> dict:
    """
    Troca um 'code' de autorização por access_token/refresh_token.
    Usada tanto pelo fluxo local interativo quanto pelo modo não-interativo
    (`python auth.py --code "XXXX"`, usado dentro do GitHub Actions).
    """
    resp = requests.post(
        config.TINY_OAUTH_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": config.TINY_CLIENT_ID,
            "client_secret": config.TINY_CLIENT_SECRET,
            "redirect_uri": config.TINY_REDIRECT_URI,
        },
    )
    resp.raise_for_status()
    dados = resp.json()
    _persistir_novo_refresh_token(dados["refresh_token"])
    return dados


def autorizacao_inicial():
    """
    Passo manual, executado UMA VEZ por quem configura o projeto (uso local,
    com navegador). Abre o navegador para o usuário logar no Tiny e
    autorizar a aplicação, depois troca o código por um refresh_token.
    """
    params = {
        "client_id": config.TINY_CLIENT_ID,
        "redirect_uri": config.TINY_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid",
    }
    url = f"{config.TINY_OAUTH_AUTH_URL}?{urlencode(params)}"
    print("Abrindo o navegador para autorizar a aplicação no Tiny...")
    print("Se não abrir sozinho, acesse manualmente:\n", url)
    webbrowser.open(url)

    redirecionado = input(
        "\nDepois de autorizar, cole aqui a URL completa para a qual você "
        "foi redirecionado (contém '?code=...'):\n> "
    ).strip()

    code = parse_qs(urlparse(redirecionado).query).get("code", [None])[0]
    if not code:
        raise ValueError("Não encontrei o parâmetro 'code' na URL colada.")

    return trocar_code_por_tokens(code)


def get_access_token() -> str:
    """
    Usa o refresh_token salvo para gerar um access_token válido.
    Chamado automaticamente pelo client.py antes de cada lote de chamadas.
    """
    if not config.TINY_REFRESH_TOKEN:
        raise RuntimeError(
            "Nenhum refresh_token configurado. Rode `python auth.py` "
            "primeiro para autorizar a aplicação (passo único)."
        )

    resp = requests.post(
        config.TINY_OAUTH_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": config.TINY_REFRESH_TOKEN,
            "client_id": config.TINY_CLIENT_ID,
            "client_secret": config.TINY_CLIENT_SECRET,
        },
    )
    resp.raise_for_status()
    dados = resp.json()

    # O Tiny costuma rotacionar o refresh_token a cada uso — se vier um novo,
    # salvamos, senão a automação para de funcionar depois de um tempo.
    if dados.get("refresh_token") and dados["refresh_token"] != config.TINY_REFRESH_TOKEN:
        _persistir_novo_refresh_token(dados["refresh_token"])

    return dados["access_token"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--code",
        help="Code recebido do Tiny, para uso não-interativo (ex: dentro do GitHub Actions)",
    )
    args = parser.parse_args()

    if args.code:
        trocar_code_por_tokens(args.code)
        print("[auth] autorização concluída com sucesso.")
    else:
        autorizacao_inicial()
