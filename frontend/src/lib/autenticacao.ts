import type { TokenSaida, Usuario, UsuarioCadastroEntrada, UsuarioLoginEntrada } from "./tipos";

const CHAVE_TOKEN = "homepilot_token";

export function obterToken(): string | null {
  return localStorage.getItem(CHAVE_TOKEN);
}

export function salvarToken(token: string): void {
  localStorage.setItem(CHAVE_TOKEN, token);
}

export function limparToken(): void {
  localStorage.removeItem(CHAVE_TOKEN);
}

async function tratarResposta<T>(resposta: Response): Promise<T> {
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({ detail: "Erro desconhecido." }));
    throw new Error(corpo.detail ?? "Erro desconhecido.");
  }
  return resposta.json();
}

export async function cadastrar(dados: UsuarioCadastroEntrada): Promise<Usuario> {
  const resposta = await fetch("/api/auth/cadastro", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  return tratarResposta<Usuario>(resposta);
}

export async function login(dados: UsuarioLoginEntrada): Promise<TokenSaida> {
  const resposta = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  return tratarResposta<TokenSaida>(resposta);
}

export async function buscarUsuarioAtual(): Promise<Usuario> {
  const token = obterToken();
  const resposta = await fetch("/api/auth/eu", {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return tratarResposta<Usuario>(resposta);
}
