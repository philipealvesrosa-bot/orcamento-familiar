"""Autenticação usando Supabase Auth."""

import streamlit as st
from supabase import Client, create_client


def _novo_cliente() -> Client:
    configuracao = st.secrets["supabase"]
    return create_client(configuracao["url"], configuracao["anon_key"])


def obter_cliente() -> Client:
    """Obtém o cliente Supabase associado à sessão atual do Streamlit."""
    if "sb" not in st.session_state:
        st.session_state["sb"] = _novo_cliente()
    return st.session_state["sb"]


def entrar(email: str, senha: str) -> tuple[bool, str]:
    """Autentica o usuário. Mantém a mensagem de erro genérica."""
    try:
        resposta = obter_cliente().auth.sign_in_with_password(
            {
                "email": email.strip().lower(),
                "password": senha,
            }
        )

        if resposta.user is None:
            return False, "E-mail ou senha inválidos."

        st.session_state["usuario_id"] = resposta.user.id
        return True, ""
    except Exception:
        return False, "E-mail ou senha inválidos."


def sair() -> None:
    try:
        obter_cliente().auth.sign_out()
    except Exception:
        pass

    for chave in list(st.session_state.keys()):
        del st.session_state[chave]


def esta_logado() -> bool:
    return "usuario_id" in st.session_state