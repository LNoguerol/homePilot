"""Emissão e validação de JWT para autenticação de usuários."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt

from homepilot.auth.excecoes import ErroTokenInvalido

ALGORITMO = "HS256"
HORAS_EXPIRACAO = 24
SEGREDO_PADRAO_DEV = "chave-secreta-dev-trocar-em-producao"


def _segredo() -> str:
    return os.environ.get("HOMEPILOT_JWT_SECRET", SEGREDO_PADRAO_DEV)


def gerar_token(usuario_id: int) -> str:
    agora = datetime.now(timezone.utc)
    payload = {"sub": str(usuario_id), "iat": agora, "exp": agora + timedelta(hours=HORAS_EXPIRACAO)}
    return jwt.encode(payload, _segredo(), algorithm=ALGORITMO)


def decodificar_token(token: str) -> int:
    try:
        payload = jwt.decode(token, _segredo(), algorithms=[ALGORITMO])
    except jwt.PyJWTError as erro:
        raise ErroTokenInvalido("Token de autenticação inválido ou expirado.") from erro
    return int(payload["sub"])
