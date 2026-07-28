"""Configuração compartilhada dos testes: usa SQLite em arquivo temporário no
lugar do MariaDB, para não exigir um banco de verdade rodando ao testar."""
import os
import tempfile

os.environ.setdefault("HOMEPILOT_DB_URL", f"sqlite:///{tempfile.NamedTemporaryFile(suffix='.db', delete=False).name}")

import pytest

from homepilot.bd.conexao import Base, engine


@pytest.fixture(scope="session", autouse=True)
def _preparar_banco():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
