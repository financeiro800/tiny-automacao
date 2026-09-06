"""
Configuração central do projeto.
Carrega credenciais e parâmetros a partir do arquivo .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- Credenciais Tiny (API v3 - OAuth2) ---
TINY_CLIENT_ID = os.getenv("TINY_CLIENT_ID", "")
TINY_CLIENT_SECRET = os.getenv("TINY_CLIENT_SECRET", "")
TINY_REFRESH_TOKEN = os.getenv("TINY_REFRESH_TOKEN", "")
TINY_REDIRECT_URI = os.getenv("TINY_REDIRECT_URI", "http://localhost:8765/callback")

# --- Endpoints oficiais da API v3 ---
TINY_API_BASE_URL = "https://erp.tiny.com.br/public-api/v3"
TINY_OAUTH_AUTH_URL = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/auth"
TINY_OAUTH_TOKEN_URL = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/token"

# --- Outros ---
ALERTA_EMAIL = os.getenv("ALERTA_EMAIL", "")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Arquivo onde o token de acesso vigente fica em cache (evita gerar um novo
# a cada chamada dentro da mesma execução)
TOKEN_CACHE_FILE = BASE_DIR / ".token_cache.json"
