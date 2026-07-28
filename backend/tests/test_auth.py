"""Testes de cadastro e login."""
from fastapi.testclient import TestClient

from homepilot.main import app

cliente = TestClient(app)

USUARIO_BASE = {
    "nome": "Luana Noguerol",
    "email": "luana@example.com",
    "senha": "senha-forte-123",
    "cidade": "Rio de Janeiro",
    "estado": "rj",
}


def test_cadastro_cria_usuario_sem_expor_senha():
    resposta = cliente.post("/api/auth/cadastro", json=USUARIO_BASE)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["email"] == USUARIO_BASE["email"]
    assert corpo["estado"] == "RJ"
    assert "senha" not in corpo
    assert "senha_hash" not in corpo


def test_cadastro_com_email_duplicado_retorna_409():
    cliente.post("/api/auth/cadastro", json={**USUARIO_BASE, "email": "duplicado@example.com"})
    resposta = cliente.post("/api/auth/cadastro", json={**USUARIO_BASE, "email": "duplicado@example.com"})
    assert resposta.status_code == 409


def test_cadastro_com_senha_curta_retorna_422():
    resposta = cliente.post("/api/auth/cadastro", json={**USUARIO_BASE, "email": "curta@example.com", "senha": "123"})
    assert resposta.status_code == 422


def test_login_com_credenciais_corretas_devolve_token():
    cliente.post("/api/auth/cadastro", json={**USUARIO_BASE, "email": "login-ok@example.com"})
    resposta = cliente.post("/api/auth/login", json={"email": "login-ok@example.com", "senha": USUARIO_BASE["senha"]})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["tipo"] == "bearer"
    assert len(corpo["token"]) > 20


def test_login_com_senha_errada_retorna_401():
    cliente.post("/api/auth/cadastro", json={**USUARIO_BASE, "email": "login-errado@example.com"})
    resposta = cliente.post(
        "/api/auth/login", json={"email": "login-errado@example.com", "senha": "senha-incorreta"}
    )
    assert resposta.status_code == 401


def test_login_com_email_inexistente_retorna_401():
    resposta = cliente.post("/api/auth/login", json={"email": "nao-existe@example.com", "senha": "qualquercoisa123"})
    assert resposta.status_code == 401


def test_rota_protegida_sem_token_retorna_401():
    resposta = cliente.get("/api/auth/eu")
    assert resposta.status_code == 401


def test_rota_protegida_com_token_invalido_retorna_401():
    resposta = cliente.get("/api/auth/eu", headers={"Authorization": "Bearer token-invalido"})
    assert resposta.status_code == 401


def test_rota_protegida_com_token_devolve_usuario():
    cliente.post("/api/auth/cadastro", json={**USUARIO_BASE, "email": "protegida@example.com"})
    login = cliente.post("/api/auth/login", json={"email": "protegida@example.com", "senha": USUARIO_BASE["senha"]})
    token = login.json()["token"]
    resposta = cliente.get("/api/auth/eu", headers={"Authorization": f"Bearer {token}"})
    assert resposta.status_code == 200
    assert resposta.json()["email"] == "protegida@example.com"
