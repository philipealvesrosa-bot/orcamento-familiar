"""Consultas ao Supabase; o RLS do banco controla o acesso aos dados."""

from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from src.services.auth import obter_cliente
from src.ui.formatos import primeiro_dia_mes, proximo_mes


def _sb():
    return obter_cliente()


def carregar_contexto() -> dict | None:
    """Carrega o membro autenticado e os membros da família."""
    usuario_id = st.session_state.get("usuario_id")

    resposta = (
        _sb()
        .table("membros_familia")
        .select("id, familia_id, nome, papel")
        .eq("user_id", usuario_id)
        .eq("ativo", True)
        .limit(1)
        .execute()
    )

    if not resposta.data:
        return None

    usuario = resposta.data[0]

    resposta_membros = (
        _sb()
        .table("membros_familia")
        .select("id, nome")
        .eq("familia_id", usuario["familia_id"])
        .eq("ativo", True)
        .execute()
    )

    return {
        "eu": usuario,
        "familia_id": usuario["familia_id"],
        "membros": resposta_membros.data,
    }


def listar_categorias(tipo: str | None = None) -> list[dict]:
    consulta = (
        _sb()
        .table("categorias")
        .select("id, nome, tipo")
        .eq("ativa", True)
        .order("nome")
    )

    if tipo:
        consulta = consulta.eq("tipo", tipo)

    return consulta.execute().data


def inserir_lancamento(dados: dict) -> None:
    _sb().table("lancamentos").insert(dados).execute()


def excluir_lancamento(lancamento_id: str) -> None:
    _sb().table("lancamentos").delete().eq("id", lancamento_id).execute()


def listar_lancamentos(mes: date) -> pd.DataFrame:
    inicio = primeiro_dia_mes(mes)
    fim = proximo_mes(mes)

    resposta = (
        _sb()
        .table("lancamentos")
        .select(
            "id, tipo, descricao, valor, data_lancamento, categoria_id, "
            "forma_pagamento, pago_por, registrado_por, observacoes, "
            "categorias(nome)"
        )
        .gte("data_lancamento", inicio.isoformat())
        .lt("data_lancamento", fim.isoformat())
        .order("data_lancamento", desc=True)
        .execute()
    )

    linhas = []
    for registro in resposta.data:
        categoria = registro.pop("categorias", None) or {}
        registro["categoria"] = categoria.get("nome", "-")
        registro["valor"] = Decimal(str(registro["valor"]))
        linhas.append(registro)

    colunas = [
        "id", "tipo", "descricao", "valor", "data_lancamento",
        "categoria_id", "forma_pagamento", "pago_por", "registrado_por",
        "observacoes", "categoria",
    ]

    return pd.DataFrame(linhas, columns=colunas)


def listar_orcamento(mes: date) -> dict[str, Decimal]:
    resposta = (
        _sb()
        .table("orcamentos")
        .select("categoria_id, valor_planejado")
        .eq("mes", primeiro_dia_mes(mes).isoformat())
        .execute()
    )

    return {
        registro["categoria_id"]: Decimal(str(registro["valor_planejado"]))
        for registro in resposta.data
    }


def salvar_orcamento(
    familia_id: str,
    categoria_id: str,
    mes: date,
    valor: Decimal,
) -> None:
    _sb().table("orcamentos").upsert(
        {
            "familia_id": familia_id,
            "categoria_id": categoria_id,
            "mes": primeiro_dia_mes(mes).isoformat(),
            "valor_planejado": str(valor),
        },
        on_conflict="familia_id,categoria_id,mes",
    ).execute()

def atualizar_lancamento(lancamento_id, campos: dict) -> None:
    """Atualiza um lançamento existente da família."""
    from src.services import auth

    (
        auth.obter_cliente()
        .table("lancamentos")
        .update(campos)
        .eq("id", str(lancamento_id))
        .execute()
    )