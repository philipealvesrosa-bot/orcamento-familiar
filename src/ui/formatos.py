"""Formatação de valores e datas no padrão brasileiro."""

from datetime import date
from decimal import Decimal

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def moeda(valor) -> str:
    """Formata um número como R$ 1.234,56."""
    valor_decimal = Decimal(str(valor or 0))
    texto = f"{valor_decimal:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def data_br(valor) -> str:
    """Converte date ou string ISO em dd/mm/aaaa."""
    if isinstance(valor, str):
        valor = date.fromisoformat(valor[:10])
    return valor.strftime("%d/%m/%Y")


def nome_mes(valor: date) -> str:
    return f"{MESES[valor.month - 1]} de {valor.year}"


def primeiro_dia_mes(valor: date) -> date:
    return valor.replace(day=1)


def proximo_mes(valor: date) -> date:
    valor = valor.replace(day=1)
    if valor.month == 12:
        return date(valor.year + 1, 1, 1)
    return date(valor.year, valor.month + 1, 1)


def mes_anterior(valor: date) -> date:
    valor = valor.replace(day=1)
    if valor.month == 1:
        return date(valor.year - 1, 12, 1)
    return date(valor.year, valor.month - 1, 1)