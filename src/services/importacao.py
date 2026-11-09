"""Leitura de extratos bancários nos formatos OFX e CSV."""

import csv
import hashlib
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd


def _decodificar(conteudo: bytes) -> str:
    for codificacao in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return conteudo.decode(codificacao)
        except UnicodeDecodeError:
            continue
    return conteudo.decode("latin-1", errors="ignore")


def _gerar_id(origem: str, data: date, valor: Decimal, descricao: str,
              ordem: int) -> str:
    """Identificador estável para detectar duplicidades."""
    base = f"{origem}|{data.isoformat()}|{valor}|{descricao.strip().lower()}"
    resumo = hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]
    return f"{resumo}-{ordem}"


def _tag(bloco: str, nome: str) -> str:
    achado = re.search(
        rf"<{nome}>([^<\r\n]*)", bloco, flags=re.IGNORECASE
    )
    return achado.group(1).strip() if achado else ""


def _converter_valor(texto: str) -> Decimal:
    texto = texto.strip().replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return Decimal(texto)


def ler_ofx(conteudo: bytes) -> pd.DataFrame:
    texto = _decodificar(conteudo)
    blocos = re.findall(
        r"<STMTTRN>(.*?)</STMTTRN>|<STMTTRN>(.*?)(?=<STMTTRN>|</BANKTRANLIST>)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )

    linhas = []
    contagem = {}
    for par in blocos:
        bloco = par[0] or par[1]
        data_texto = _tag(bloco, "DTPOSTED")[:8]
        valor_texto = _tag(bloco, "TRNAMT")
        if not data_texto or not valor_texto:
            continue

        data = datetime.strptime(data_texto, "%Y%m%d").date()
        valor = Decimal(valor_texto.replace(",", "."))
        descricao = _tag(bloco, "MEMO") or _tag(bloco, "NAME") or "Sem descrição"
        fitid = _tag(bloco, "FITID")

        if fitid:
            id_externo = f"ofx-{fitid}"
        else:
            chave = (data, valor, descricao)
            contagem[chave] = contagem.get(chave, 0) + 1
            id_externo = _gerar_id("ofx", data, valor, descricao, contagem[chave])

        linhas.append(
            {
                "data": data,
                "descricao": descricao[:200],
                "valor": abs(valor),
                "tipo": "receita" if valor > 0 else "despesa",
                "id_externo": id_externo,
            }
        )

    return pd.DataFrame(linhas)


def ler_csv(conteudo: bytes, col_data: str, col_descricao: str,
            col_valor: str) -> pd.DataFrame:
    texto = _decodificar(conteudo)
    try:
        separador = csv.Sniffer().sniff(texto[:2000], delimiters=";,\t").delimiter
    except csv.Error:
        separador = ";"

    tabela = pd.read_csv(io.StringIO(texto), sep=separador, dtype=str)

    linhas = []
    contagem = {}
    for _, registro in tabela.iterrows():
        try:
            data = pd.to_datetime(
                registro[col_data], dayfirst=True
            ).date()
            valor = _converter_valor(str(registro[col_valor]))
        except (ValueError, InvalidOperation, TypeError):
            continue

        descricao = str(registro[col_descricao]).strip() or "Sem descrição"
        chave = (data, valor, descricao)
        contagem[chave] = contagem.get(chave, 0) + 1

        linhas.append(
            {
                "data": data,
                "descricao": descricao[:200],
                "valor": abs(valor),
                "tipo": "receita" if valor > 0 else "despesa",
                "id_externo": _gerar_id(
                    "csv", data, valor, descricao, contagem[chave]
                ),
            }
        )

    return pd.DataFrame(linhas)


def colunas_csv(conteudo: bytes) -> list[str]:
    texto = _decodificar(conteudo)
    try:
        separador = csv.Sniffer().sniff(texto[:2000], delimiters=";,\t").delimiter
    except csv.Error:
        separador = ";"
    return list(pd.read_csv(io.StringIO(texto), sep=separador, nrows=0).columns)