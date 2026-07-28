"""Dependências do FastAPI para proteger rotas com autenticação."""
from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from homepilot.auth.excecoes import ErroTokenInvalido
from homepilot.auth.token import decodificar_token
from homepilot.bd.conexao import obter_sessao
from homepilot.bd.modelos import Usuario


def usuario_atual(
    authorization: str | None = Header(default=None),
    sessao: Session = Depends(obter_sessao),
) -> Usuario:
    if not authorization or not authorization.startswith("Bearer "):
        raise ErroTokenInvalido("Token de autenticação ausente.")

    token = authorization.removeprefix("Bearer ").strip()
    usuario_id = decodificar_token(token)

    usuario = sessao.get(Usuario, usuario_id)
    if usuario is None:
        raise ErroTokenInvalido("Usuário do token não existe mais.")
    return usuario
