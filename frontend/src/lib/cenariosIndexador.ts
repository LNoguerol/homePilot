import type { Indexador } from "./tipos";

export interface OpcaoCenario {
  nome: string;
  taxa: string;
}

/** Cenários padrão de taxa anual constante por indexador, espelhando
 * `CENARIOS_PADRAO_POR_INDEXADOR` do backend (`core/taxas.py`). */
export const CENARIOS_POR_INDEXADOR: Record<Indexador, OpcaoCenario[]> = {
  tr: [
    { nome: "TR 0,0% a.a.", taxa: "0.0" },
    { nome: "TR 1,5% a.a.", taxa: "0.015" },
    { nome: "TR 2,0% a.a.", taxa: "0.02" },
    { nome: "TR 2,5% a.a.", taxa: "0.025" },
  ],
  poupanca: [
    { nome: "Poupança 5,0% a.a.", taxa: "0.05" },
    { nome: "Poupança 6,0% a.a.", taxa: "0.06" },
    { nome: "Poupança 7,0% a.a.", taxa: "0.07" },
    { nome: "Poupança 8,0% a.a.", taxa: "0.08" },
  ],
};

export const ROTULO_INDEXADOR: Record<Indexador, string> = {
  tr: "TR",
  poupanca: "Poupança",
};
