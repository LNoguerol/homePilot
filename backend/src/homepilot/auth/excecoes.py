"""Exceções de negócio de autenticação."""


class ErroCadastroInvalido(ValueError):
    """E-mail já cadastrado ou dados de cadastro inválidos."""


class ErroCredenciaisInvalidas(ValueError):
    """E-mail ou senha incorretos no login."""


class ErroTokenInvalido(ValueError):
    """Token de autenticação ausente, inválido ou expirado."""
