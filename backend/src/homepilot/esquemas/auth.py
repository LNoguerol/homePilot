"""Schemas Pydantic de cadastro e login."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UsuarioCadastroEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=100)
    telefone: str | None = Field(default=None, max_length=20)
    cidade: str = Field(min_length=1, max_length=100)
    estado: str = Field(min_length=2, max_length=2)


class UsuarioLoginEntrada(BaseModel):
    email: EmailStr
    senha: str


class UsuarioSaida(BaseModel):
    id: int
    nome: str
    email: str
    telefone: str | None
    cidade: str
    estado: str

    model_config = {"from_attributes": True}


class TokenSaida(BaseModel):
    token: str
    tipo: str = "bearer"
