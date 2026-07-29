<script lang="ts">
  import { cadastrar, login, salvarToken } from "../autenticacao";
  import Logo from "./Logo.svelte";

  export let aoAutenticar: () => void;
  export let irParaLogin: () => void;

  let nome = "";
  let email = "";
  let senha = "";
  let telefone = "";
  let cidade = "";
  let estado = "";
  let carregando = false;
  let erro: string | null = null;

  async function aoCadastrar() {
    erro = null;
    carregando = true;
    try {
      await cadastrar({ nome, email, senha, telefone: telefone || undefined, cidade, estado });
      const resultado = await login({ email, senha });
      salvarToken(resultado.token);
      aoAutenticar();
    } catch (e) {
      erro = e instanceof Error ? e.message : "Erro desconhecido no cadastro.";
    } finally {
      carregando = false;
    }
  }
</script>

<div class="tela-auth">
  <form on:submit|preventDefault={aoCadastrar}>
    <div class="marca-form">
      <Logo tamanho={36} />
      <span class="nome-marca">HomePilot</span>
    </div>
    <h2>Criar conta</h2>
    <label>
      Nome
      <input bind:value={nome} required />
    </label>
    <label>
      E-mail
      <input type="email" bind:value={email} required />
    </label>
    <label>
      Senha (mínimo 8 caracteres)
      <input type="password" bind:value={senha} minlength="8" required />
    </label>
    <label>
      Telefone (opcional)
      <input bind:value={telefone} />
    </label>
    <label>
      Cidade
      <input bind:value={cidade} required />
    </label>
    <label>
      Estado (UF)
      <input bind:value={estado} maxlength="2" required />
    </label>
    {#if erro}
      <p class="erro">{erro}</p>
    {/if}
    <button type="submit" disabled={carregando}>{carregando ? "Cadastrando..." : "Cadastrar"}</button>
    <p class="alternativa">
      Já tem conta? <button type="button" class="link" on:click={irParaLogin}>Entrar</button>
    </p>
  </form>
</div>

<style>
  .tela-auth {
    display: flex;
    justify-content: center;
    padding: 4rem 1rem;
  }
  form {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
    width: 100%;
    max-width: 380px;
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    box-shadow: var(--sombra-cartao);
    padding: 2rem;
    border-radius: var(--raio-md);
  }
  .marca-form {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
  }
  .nome-marca {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--cor-texto);
    letter-spacing: -0.02em;
  }
  h2 {
    margin: 0 0 0.25rem 0;
    text-align: center;
    font-size: 1.15rem;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--cor-texto-secundario);
  }
  input {
    padding: 0.55rem 0.7rem;
    border-radius: var(--raio-sm);
    border: 1px solid var(--cor-borda);
    font-size: 0.9rem;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }
  input:focus {
    border-color: var(--cor-destaque);
    box-shadow: 0 0 0 3px var(--cor-destaque-fundo);
  }
  button[type="submit"] {
    background: var(--cor-destaque);
    color: white;
    border: none;
    padding: 0.65rem;
    border-radius: var(--raio-sm);
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease;
  }
  button[type="submit"]:hover:not(:disabled) {
    background: var(--cor-destaque-hover);
  }
  button[type="submit"]:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .link {
    background: none;
    border: none;
    color: var(--cor-destaque);
    cursor: pointer;
    padding: 0;
    font-weight: 600;
    text-decoration: underline;
  }
  .erro {
    background: var(--cor-perigo-fundo);
    color: #a12020;
    padding: 0.55rem 0.7rem;
    border-radius: var(--raio-sm);
    font-size: 0.85rem;
  }
  .alternativa {
    font-size: 0.85rem;
    color: var(--cor-texto-secundario);
    text-align: center;
    margin: 0;
  }
</style>
