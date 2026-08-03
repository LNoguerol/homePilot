"""Endpoint de importação de dados do contrato a partir de um extrato em PDF."""
from fastapi import APIRouter, HTTPException, UploadFile

from homepilot.esquemas.importacao import ContratoExtraidoSaida
from homepilot.importacao.extrato_pdf import ErroLeituraPdf, extrair_de_pdf

roteador = APIRouter(prefix="/api", tags=["importação"])


@roteador.post("/contratos/importar-pdf", response_model=ContratoExtraidoSaida)
async def importar_contrato_pdf(arquivo: UploadFile) -> ContratoExtraidoSaida:
    conteudo = await arquivo.read()
    try:
        dados = extrair_de_pdf(conteudo)
    except ErroLeituraPdf as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ContratoExtraidoSaida(
        data_base=dados.data_base,
        saldo_devedor=dados.saldo_devedor,
        sistema_amortizacao=dados.sistema_amortizacao,
        taxa_nominal_anual=dados.taxa_nominal_anual,
        taxa_efetiva_informada=dados.taxa_efetiva_informada,
        prazo_original=dados.prazo_original,
        prazo_restante=dados.prazo_restante,
    )
