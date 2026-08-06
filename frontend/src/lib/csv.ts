import type { ParcelaMensal } from "./tipos";
import { formatarCompetencia } from "./moeda";

function paraDecimalBr(valor: string): string {
  return Number(valor).toFixed(2).replace(".", ",");
}

export function exportarCronogramaCsv(parcelas: ParcelaMensal[]): void {
  const cabecalho = [
    "Mes",
    "Competencia",
    "Saldo inicial",
    "Correcao indexador",
    "Saldo corrigido",
    "Juros",
    "Prestacao financeira",
    "Amortizacao ordinaria",
    "Amortizacao extraordinaria",
    "Seguros e tarifas",
    "Prestacao total",
    "Saldo final",
  ];

  const linhas = parcelas.map((p) =>
    [
      p.numero_mes,
      formatarCompetencia(p.competencia),
      paraDecimalBr(p.saldo_inicial),
      paraDecimalBr(p.correcao_indexador),
      paraDecimalBr(p.saldo_corrigido),
      paraDecimalBr(p.juros),
      paraDecimalBr(p.prestacao_financeira),
      paraDecimalBr(p.amortizacao_ordinaria),
      paraDecimalBr(p.amortizacao_extraordinaria),
      paraDecimalBr(p.seguros_tarifas),
      paraDecimalBr(p.prestacao_total),
      paraDecimalBr(p.saldo_final),
    ].join(";"),
  );

  const conteudo = [cabecalho.join(";"), ...linhas].join("\r\n");
  const bom = "﻿";
  const blob = new Blob([bom + conteudo], { type: "text/csv;charset=utf-8;" });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "cronograma-homepilot.csv";
  link.click();
  URL.revokeObjectURL(url);
}
