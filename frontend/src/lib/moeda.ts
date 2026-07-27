export function formatarMoeda(valor: string | number): string {
  const numero = typeof valor === "string" ? Number(valor) : valor;
  return numero.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export function formatarData(data: string): string {
  const [ano, mes, dia] = data.split("-");
  return `${dia}/${mes}/${ano}`;
}

const MESES_PT: string[] = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

export function formatarCompetencia(data: string): string {
  const [ano, mes] = data.split("-");
  return `${MESES_PT[Number(mes) - 1]}/${ano}`;
}
