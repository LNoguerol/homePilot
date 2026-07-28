"""Ponto de entrada da API do HomePilot."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from homepilot.api.auth import roteador as roteador_auth
from homepilot.api.simulacoes import roteador
from homepilot.auth.excecoes import ErroCadastroInvalido, ErroCredenciaisInvalidas, ErroTokenInvalido
from homepilot.core.excecoes import ErroSimulacaoInvalida

app = FastAPI(
    title="HomePilot",
    description="Simulação e planejamento de financiamentos imobiliários brasileiros",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ErroSimulacaoInvalida)
async def tratar_erro_simulacao_invalida(request: Request, exc: ErroSimulacaoInvalida) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(ErroCadastroInvalido)
async def tratar_erro_cadastro_invalido(request: Request, exc: ErroCadastroInvalido) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ErroCredenciaisInvalidas)
async def tratar_erro_credenciais_invalidas(request: Request, exc: ErroCredenciaisInvalidas) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(ErroTokenInvalido)
async def tratar_erro_token_invalido(request: Request, exc: ErroTokenInvalido) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.get("/api/health")
async def verificar_saude() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(roteador)
app.include_router(roteador_auth)
