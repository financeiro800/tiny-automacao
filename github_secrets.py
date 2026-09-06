"""
Cria/atualiza Secrets do repositório via API do GitHub.

Necessário porque o Tiny costuma trocar (rotacionar) o refresh_token a
cada uso, e o runner do GitHub Actions não guarda nenhum arquivo de uma
execução para a próxima — cada rodada começa "do zero". Por isso, sempre
que o Tiny devolve um refresh_token novo, gravamos ele como Secret do
próprio repositório (em vez de escrever num .env local, como acontece
quando o projeto roda na sua máquina).

Precisa de:
  - GH_PAT: um Personal Access Token com permissão de leitura/escrita em
    Secrets deste repositório (veja GITHUB_SETUP.md)
  - GITHUB_REPOSITORY: já vem preenchida automaticamente pelo Actions em
    toda execução — não precisa configurar nada
"""
import base64
import os

import requests
from nacl import encoding, public


def _repo() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY")  # formato "usuario/repositorio"
    if not repo:
        raise RuntimeError(
            "GITHUB_REPOSITORY não encontrado — esta função só funciona "
            "dentro de uma execução do GitHub Actions."
        )
    return repo


def _headers() -> dict:
    pat = os.environ.get("GH_PAT")
    if not pat:
        raise RuntimeError(
            "Secret GH_PAT não configurado no repositório. Ele é necessário "
            "para que o script possa atualizar outros secrets (como o "
            "TINY_REFRESH_TOKEN) sozinho. Veja GITHUB_SETUP.md."
        )
    return {"Authorization": f"Bearer {pat}", "Accept": "application/vnd.github+json"}


def _chave_publica_do_repo() -> dict:
    url = f"https://api.github.com/repos/{_repo()}/actions/secrets/public-key"
    resp = requests.get(url, headers=_headers())
    resp.raise_for_status()
    return resp.json()


def _criptografar_para_github(valor: str, chave_publica_b64: str) -> str:
    """O GitHub exige o valor cifrado com libsodium sealed box antes do envio."""
    chave = public.PublicKey(chave_publica_b64.encode("utf-8"), encoding.Base64Encoder())
    caixa = public.SealedBox(chave)
    cifrado = caixa.encrypt(valor.encode("utf-8"))
    return base64.b64encode(cifrado).decode("utf-8")


def salvar_secret(nome: str, valor: str):
    """Cria (ou atualiza, se já existir) um Secret do repositório."""
    chave = _chave_publica_do_repo()
    valor_cifrado = _criptografar_para_github(valor, chave["key"])

    url = f"https://api.github.com/repos/{_repo()}/actions/secrets/{nome}"
    resp = requests.put(
        url,
        headers=_headers(),
        json={"encrypted_value": valor_cifrado, "key_id": chave["key_id"]},
    )
    resp.raise_for_status()
    print(f"[github_secrets] secret '{nome}' atualizado com sucesso.")
