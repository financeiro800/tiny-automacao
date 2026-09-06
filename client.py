"""
Cliente HTTP genérico para a API v3 do Tiny (erp.tiny.com.br/public-api/v3).
Cuida de: header de autenticação, paginação automática e espera em caso
de rate limit (HTTP 429).
"""
import time
import requests

import config
import auth


class TinyClient:
    def __init__(self):
        self._token = None

    def _headers(self):
        if not self._token:
            self._token = auth.get_access_token()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{config.TINY_API_BASE_URL}{path}"
        for tentativa in range(3):
            resp = requests.request(method, url, headers=self._headers(), **kwargs)

            if resp.status_code == 401:
                # token expirado no meio da execução: renova e tenta de novo
                self._token = auth.get_access_token()
                continue

            if resp.status_code == 429:
                espera = int(resp.headers.get("Retry-After", 5))
                print(f"[client] rate limit atingido, aguardando {espera}s...")
                time.sleep(espera)
                continue

            resp.raise_for_status()
            return resp.json() if resp.content else {}

        raise RuntimeError(f"Falha ao chamar {url} após 3 tentativas.")

    def get(self, path: str, params: dict = None) -> dict:
        return self._request("GET", path, params=params or {})

    def post(self, path: str, json_body: dict = None) -> dict:
        return self._request("POST", path, json=json_body or {})

    def put(self, path: str, json_body: dict = None) -> dict:
        return self._request("PUT", path, json=json_body or {})

    def listar_todas_paginas(self, path: str, params: dict = None, campo_itens: str = "itens"):
        """
        Percorre todas as páginas de um endpoint de listagem e retorna a
        lista completa de itens (a API do Tiny pagina os resultados).
        """
        params = dict(params or {})
        params.setdefault("limit", 100)
        offset = 0
        todos = []
        while True:
            params["offset"] = offset
            pagina = self.get(path, params=params)
            itens = pagina.get(campo_itens, [])
            if not itens:
                break
            todos.extend(itens)
            if len(itens) < params["limit"]:
                break
            offset += params["limit"]
        return todos
