"""
Cliente HTTP para a API v3 do Tiny (erp.tiny.com.br/public-api/v3).

IMPORTANTE: usa o binário curl (via subprocess) em vez da biblioteca
requests do Python. Na pratica, descobrimos que a protecao anti-bot da
Cloudflare na frente da API do Tiny bloqueia (HTTP 429, corpo vazio) as
requisicoes feitas pela biblioteca requests/urllib3, mesmo vindas do mesmo
aparelho/rede onde um curl comum funciona normalmente. Por isso as
chamadas para erp.tiny.com.br sao feitas via curl aqui.
"""
import json
import subprocess
import time
import urllib.parse

import config
import auth


def _curl(method: str, url: str, headers: dict, params: dict = None, json_body: dict = None, timeout: int = 30):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    cmd = ["curl", "-s", "-S", "--max-time", str(timeout), "-X", method, "-w", "\n%{http_code}"]
    for chave, valor in headers.items():
        cmd += ["-H", f"{chave}: {valor}"]
    if json_body is not None:
        cmd += ["--data-raw", json.dumps(json_body)]
    cmd.append(url)

    resultado = subprocess.run(cmd, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(f"curl falhou (codigo {resultado.returncode}): {resultado.stderr.strip()}")

    saida = resultado.stdout
    corpo, _, codigo_str = saida.rpartition("\n")
    try:
        codigo = int(codigo_str.strip())
    except ValueError:
        codigo = 0
    return codigo, corpo


class TinyClient:
    def __init__(self):
        self._token = None

    def _headers(self):
        if not self._token:
            self._token = auth.get_access_token()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, params: dict = None, json_body: dict = None) -> dict:
        url = f"{config.TINY_API_BASE_URL}{path}"
        ultimo_codigo, ultimo_corpo = None, ""

        for tentativa in range(3):
            codigo, corpo = _curl(method, url, self._headers(), params=params, json_body=json_body)
            ultimo_codigo, ultimo_corpo = codigo, corpo

            if codigo == 401:
                self._token = auth.get_access_token()
                continue

            if codigo == 429:
                print(f"[client] HTTP 429 (tentativa {tentativa + 1}/3). Corpo: {corpo[:500]!r}")
                print("[client] aguardando 5s antes de tentar de novo...")
                time.sleep(5)
                continue

            if codigo >= 400:
                print(f"[client] erro {codigo} ao chamar {url}: {corpo[:1000]!r}")
                raise RuntimeError(f"HTTP {codigo} ao chamar {url}: {corpo[:500]!r}")

            return json.loads(corpo) if corpo.strip() else {}

        raise RuntimeError(f"Falha ao chamar {url} apos 3 tentativas. Ultima resposta: {ultimo_codigo} {ultimo_corpo[:500]!r}")

    def get(self, path: str, params: dict = None) -> dict:
        return self._request("GET", path, params=params or {})

    def post(self, path: str, json_body: dict = None) -> dict:
        return self._request("POST", path, json_body=json_body or {})

    def put(self, path: str, json_body: dict = None) -> dict:
        return self._request("PUT", path, json_body=json_body or {})

    def listar_todas_paginas(self, path: str, params: dict = None, campo_itens: str = "itens"):
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
