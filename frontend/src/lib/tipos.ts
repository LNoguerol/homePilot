export type Estrategia = "reducao_prazo" | "reducao_prestacao";
export type SistemaAmortizacao = "price" | "sac";

export interface DadosContrato {
  data_base: string;
  saldo_devedor: string;
  sistema_amortizacao: SistemaAmortizacao;
  indexador: "tr";
  taxa_nominal_anual: string;
  taxa_efetiva_informada: string;
  prazo_original: number;
  prazo_restante: number;
  seguros_tarifas_mensais: string;
  limite_saldo: string;
  limite_prestacao: string;
}

export interface ContratoExtraido {
  data_base: string | null;
  saldo_devedor: string | null;
  sistema_amortizacao: SistemaAmortizacao | null;
  taxa_nominal_anual: string | null;
  taxa_efetiva_informada: string | null;
  prazo_original: number | null;
  prazo_restante: number | null;
}

export interface AmortizacaoExtraordinaria {
  data: string;
  valor: string;
  estrategia: Estrategia;
}

export interface AporteRecorrente {
  valor: string;
  periodicidade_meses: number;
  mes_inicial: string;
  mes_final: string | null;
  estrategia: Estrategia;
}

export interface CenarioTR {
  nome: string;
  taxa_anual: string;
}

export interface ParcelaMensal {
  numero_mes: number;
  competencia: string;
  saldo_inicial: string;
  correcao_tr: string;
  saldo_corrigido: string;
  juros: string;
  prestacao_financeira: string;
  amortizacao_ordinaria: string;
  amortizacao_extraordinaria: string;
  seguros_tarifas: string;
  prestacao_total: string;
  saldo_final: string;
  prazo_restante: number;
  estrategia_aplicada: Estrategia | null;
  alerta_saldo: boolean;
  alerta_prestacao: boolean;
}

export interface ResumoSimulacao {
  saldo_inicial: string;
  maior_saldo_devedor: string;
  maior_prestacao_total: string;
  data_quitacao: string;
  meses_ate_quitacao: number;
  meses_antecipados: number;
  total_juros: string;
  total_correcao_tr: string;
  total_seguros_tarifas: string;
  total_amortizado_extraordinario: string;
  soma_prestacoes: string;
  status_limite_saldo: string;
  status_limite_prestacao: string;
}

export interface SimulacaoSaida {
  parcelas: ParcelaMensal[];
  resumo: ResumoSimulacao;
}

export interface ResumoCenario {
  cenario: string;
  taxa_anual: string;
  resumo: ResumoSimulacao;
}

export interface CompararSaida {
  resultados: ResumoCenario[];
}

export interface Usuario {
  id: number;
  nome: string;
  email: string;
  telefone: string | null;
  cidade: string;
  estado: string;
}

export interface UsuarioCadastroEntrada {
  nome: string;
  email: string;
  senha: string;
  telefone?: string;
  cidade: string;
  estado: string;
}

export interface UsuarioLoginEntrada {
  email: string;
  senha: string;
}

export interface TokenSaida {
  token: string;
  tipo: string;
}
