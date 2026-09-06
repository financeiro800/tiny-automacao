"""
Autorização inicial da aplicação, pensada para rodar dentro do GitHub
Actions (workflow "Autorizar Tiny"), sem precisar de navegador/Python
locais.

Funciona em 2 execuções manuais do mesmo workflow:

  1ª execução (campo "code" vazio): imprime no log da Action a URL de
     autorização do Tiny. Você abre essa URL no navegador do celular,
     loga, autoriza, e é redirecionado pro webhook.site — de lá você
     copia o valor do parâmetro "code" da URL recebida.

  2ª execução (campo "code" preenchido): troca esse código por um
     refresh_token e salva ele como Secret do repositório (via
     github_secrets.py), pronto pra rotina diária usar.
"""
import os
from urllib.parse import urlencode

import requests

import config
from github_secrets import salvar_secret


def main():
    code = os.environ.get("CODE_INPUT", "").strip()

    if not code:
        params = {
            "client_id": config.TINY_CLIENT_ID,
            "redirect_uri": config.TINY_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid",
        }
        url = f"{config.TINY_OAUTH_AUTH_URL}?{urlencode(params)}"
        print("=" * 70)
        print("PASSO 1 CONCLUÍDO — copie a URL abaixo e abra no navegador:")
        print(url)
        print("=" * 70)
        print("Depois de autorizar, você cai numa página do webhook.site.")
        print("Copie o valor do parâmetro 'code' da URL que aparecer lá e")
        print("rode esta Action de novo, preenchendo o campo 'code'.")
        return

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

    salvar_secret("TINY_REFRESH_TOKEN", dados["refresh_token"])
    print("Autorização concluída! O TINY_REFRESH_TOKEN foi salvo como Secret.")
    print("A partir de agora, a rotina diária já pode rodar sozinha.")


if __name__ == "__main__":
    main()
