<script lang="ts">
  import { login, salvarToken } from "../autenticacao";

  export let aoAutenticar: () => void;
  export let irParaCadastro: () => void;

  let email = "";
  let senha = "";
  let carregando = false;
  let erro: string | null = null;

  async function aoEntrar() {
    erro = null;
    carregando = true;
    try {
      const resultado = await login({ email, senha });
      salvarToken(resultado.token);
      aoAutenticar();
    } catch (e) {
      erro = e instanceof Error ? e.message : "Erro desconhecido no login.";
    } finally {
      carregando = false;
    }
  }
</script>

<div class="tela-auth">
  <form on:submit|preventDefault={aoEntrar}>
    <h2>Entrar</h2>
    <label>
      E-mail
      <input type="email" bind:value={email} required />
    </label>
    <label>
      Senha
      <input type="password" bind:value={senha} required />
    </label>
    {#if erro}
      <p class="erro">{erro}</p>
    {/if}
    <button type="submit" disabled={carregando}>{carregando ? "Entrando..." : "Entrar"}</button>
    <p class="alternativa">
      Não tem conta? <button type="button" class="link" on:click={irParaCadastro}>Cadastre-se</button>
    </p>
  </form>
</div>

<style>
  .tela-auth {
    display: flex;
    justify-content: center;
    padding: 3rem 1rem;
  }
  form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    width: 100%;
    max-width: 360px;
    background: var(--cor-cartao);
    padding: 1.5rem;
    border-radius: 8px;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.9rem;
  }
  input {
    padding: 0.5rem;
    border-radius: 4px;
    border: 1px solid #ccc;
  }
  button[type="submit"] {
    background: var(--cor-destaque);
    color: white;
    border: none;
    padding: 0.6rem;
    border-radius: 6px;
    cursor: pointer;
  }
  .link {
    background: none;
    border: none;
    color: var(--cor-destaque);
    cursor: pointer;
    padding: 0;
    text-decoration: underline;
  }
  .erro {
    background: #fdeaea;
    color: #a12020;
    padding: 0.5rem;
    border-radius: 6px;
    font-size: 0.85rem;
  }
  .alternativa {
    font-size: 0.85rem;
    text-align: center;
  }
</style>
