<script lang="ts">
  import { cadastrar, login, salvarToken } from "../autenticacao";

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
