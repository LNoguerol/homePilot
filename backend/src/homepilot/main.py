"""Ponto de entrada da API do HomePilot."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from homepilot.api.simulacoes import roteador
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


@app.get("/api/health")
async def verificar_saude() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(roteador)
