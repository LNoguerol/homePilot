"""Conexão com o banco de dados (MariaDB) via SQLAlchemy.

A URL de conexão é montada a partir de variáveis de ambiente (ver
`docs/banco.md`). `HOMEPILOT_DB_URL`, se definida, sobrepõe tudo — usada nos
testes automatizados para apontar para um SQLite local em vez do MariaDB.
"""
from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def obter_url_banco() -> str:
    url_explicita = os.environ.get("HOMEPILOT_DB_URL")
    if url_explicita:
        return url_explicita

    usuario = os.environ.get("HOMEPILOT_DB_USUARIO", "homepilot")
    senha = os.environ.get("HOMEPILOT_DB_SENHA", "homepilot")
    host = os.environ.get("HOMEPILOT_DB_HOST", "localhost")
    porta = os.environ.get("HOMEPILOT_DB_PORT", "3306")
    nome = os.environ.get("HOMEPILOT_DB_NOME", "homepilot")
    return f"mysql+pymysql://{usuario}:{senha}@{host}:{porta}/{nome}?charset=utf8mb4"


engine = create_engine(obter_url_banco(), pool_pre_ping=True)
SessaoLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def obter_sessao() -> Iterator[Session]:
    sessao = SessaoLocal()
    try:
        yield sessao
    finally:
        sessao.close()
