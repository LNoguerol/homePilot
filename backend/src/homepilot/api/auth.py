"""Endpoints de cadastro e login."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from homepilot.auth.dependencias import usuario_atual
from homepilot.auth.excecoes import ErroCadastroInvalido, ErroCredenciaisInvalidas
from homepilot.auth.senha import gerar_hash, verificar_senha
from homepilot.auth.token import gerar_token
from homepilot.bd.conexao import obter_sessao
from homepilot.bd.modelos import Usuario
from homepilot.esquemas.auth import TokenSaida, UsuarioCadastroEntrada, UsuarioLoginEntrada, UsuarioSaida

roteador = APIRouter(prefix="/api/auth", tags=["autenticação"])


@roteador.post("/cadastro", response_model=UsuarioSaida, status_code=201)
def cadastrar(dados: UsuarioCadastroEntrada, sessao: Session = Depends(obter_sessao)) -> Usuario:
    existente = sessao.scalar(select(Usuario).where(Usuario.email == dados.email))
    if existente is not None:
        raise ErroCadastroInvalido("Já existe uma conta com este e-mail.")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash(dados.senha),
        telefone=dados.telefone,
        cidade=dados.cidade,
        estado=dados.estado.upper(),
    )
    sessao.add(usuario)
    sessao.commit()
    sessao.refresh(usuario)
    return usuario


@roteador.post("/login", response_model=TokenSaida)
def login(dados: UsuarioLoginEntrada, sessao: Session = Depends(obter_sessao)) -> TokenSaida:
    usuario = sessao.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None or not verificar_senha(dados.senha, usuario.senha_hash):
        raise ErroCredenciaisInvalidas("E-mail ou senha inválidos.")
    return TokenSaida(token=gerar_token(usuario.id))


@roteador.get("/eu", response_model=UsuarioSaida)
def eu(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    return usuario
