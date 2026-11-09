"""Orçamento Familiar — MVP."""

from datetime import date
from decimal import Decimal

import plotly.express as px
import streamlit as st

from src.config import CORES, FORMAS_PAGAMENTO, LIMITE_ALERTA, NOME_APP
from src.services import auth, dados
from src.ui.formatos import (
    data_br,
    mes_anterior,
    moeda,
    nome_mes,
    primeiro_dia_mes,
    proximo_mes,
)
from src.ui.tema import aplicar_tema


st.set_page_config(page_title=NOME_APP, layout="centered")
aplicar_tema()


def tela_login() -> None:
    st.title(NOME_APP)
    st.caption("Acesso restrito à família.")

    with st.form("login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        enviar = st.form_submit_button(
            "Entrar",
            type="primary",
            width="stretch",
        )

    if enviar:
        sucesso, mensagem = auth.entrar(email, senha)
        if sucesso:
            st.rerun()
        else:
            st.error(mensagem)


def seletor_mes() -> date:
    if "mes" not in st.session_state:
        st.session_state["mes"] = primeiro_dia_mes(date.today())

    coluna_esquerda, coluna_centro, coluna_direita = st.columns([1, 3, 1])

    if coluna_esquerda.button("◀", width="stretch"):
        st.session_state["mes"] = mes_anterior(st.session_state["mes"])
        st.rerun()

    coluna_centro.markdown(
        f"<h3 style='text-align:center;margin:0'>"
        f"{nome_mes(st.session_state['mes'])}</h3>",
        unsafe_allow_html=True,
    )

    if coluna_direita.button("▶", width="stretch"):
        st.session_state["mes"] = proximo_mes(st.session_state["mes"])
        st.rerun()

    return st.session_state["mes"]


def nome_membro(contexto: dict, membro_id) -> str:
    for membro in contexto["membros"]:
        if membro["id"] == membro_id:
            return membro["nome"]
    return "-"


def barra_categoria(nome: str, gasto: Decimal, planejado: Decimal) -> None:
    if planejado > 0:
        percentual = float(gasto / planejado)
    else:
        percentual = 1.0 if gasto > 0 else 0.0

    if percentual > 1:
        cor, status = "#B00020", "Acima do limite"
    elif percentual >= LIMITE_ALERTA:
        cor, status = "#E0A100", "Próximo do limite"
    else:
        cor, status = "#2E7D32", "Dentro do limite"

    largura = min(percentual, 1.0) * 100
    saldo = planejado - gasto

    st.markdown(
        f"""
        <div class="cat-linha">
          <div class="cat-topo">
            <b>{nome}</b>
            <span>{moeda(gasto)} de {moeda(planejado)}</span>
          </div>
          <div class="barra-fundo">
            <div class="barra"
                 style="width:{largura}%;background:{cor}"></div>
          </div>
          <small>{status} · Saldo: {moeda(saldo)}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pagina_resumo(mes: date) -> None:
    df = dados.listar_lancamentos(mes)

    if df.empty:
        receitas = Decimal("0")
        despesas = Decimal("0")
    else:
        receitas = sum(
            df.loc[df["tipo"] == "receita", "valor"],
            Decimal("0"),
        )
        despesas = sum(
            df.loc[df["tipo"] == "despesa", "valor"],
            Decimal("0"),
        )

    col_receitas, col_despesas = st.columns(2)
    col_receitas.metric("Receitas", moeda(receitas))
    col_despesas.metric("Despesas", moeda(despesas))
    st.metric("Saldo do mês", moeda(receitas - despesas))

    st.caption(
        "Registre as receitas pelo valor líquido efetivamente disponível."
    )

    if not df.empty and (df["tipo"] == "despesa").any():
        despesas_categoria = df[df["tipo"] == "despesa"].copy()
        despesas_categoria["valor"] = despesas_categoria["valor"].astype(float)

        resumo = (
            despesas_categoria
            .groupby("categoria", as_index=False)["valor"]
            .sum()
        )

        figura = px.pie(
            resumo,
            names="categoria",
            values="valor",
            hole=0.5,
            color_discrete_sequence=[
                CORES["bordo"],
                CORES["marrom_rosado"],
                CORES["rosa_claro"],
                "#A64B5F",
                "#C98E8E",
            ],
        )
        figura.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.subheader("Despesas por categoria")
        st.plotly_chart(figura, width="stretch")
    else:
        st.info("Ainda não há despesas neste mês.")


def pagina_lancamentos(contexto: dict, mes: date) -> None:
    st.subheader("Novo lançamento")

    tipo = st.radio(
        "Tipo",
        ["despesa", "receita"],
        horizontal=True,
        format_func=str.capitalize,
    )

    categorias = dados.listar_categorias(tipo)
    mapa_categorias = {item["nome"]: item["id"] for item in categorias}
    mapa_membros = {
        membro["nome"]: membro["id"]
        for membro in contexto["membros"]
    }

    if not mapa_categorias:
        st.warning("Não há categorias disponíveis para este tipo.")
        return

    if not mapa_membros:
        st.error("Não foram encontrados membros ativos na família.")
        return

    with st.form("novo_lancamento", clear_on_submit=True):
        descricao = st.text_input("Descrição", max_chars=200)
        valor = st.number_input(
            "Valor (R$)",
            min_value=0.0,
            step=0.01,
            format="%.2f",
        )
        data_lancamento = st.date_input(
            "Data",
            value=date.today(),
            format="DD/MM/YYYY",
        )
        categoria = st.selectbox(
            "Categoria",
            list(mapa_categorias.keys()),
        )
        forma = st.selectbox(
            "Forma de pagamento",
            list(FORMAS_PAGAMENTO.keys()),
            format_func=lambda chave: FORMAS_PAGAMENTO[chave],
        )

        rotulo = "Quem pagou" if tipo == "despesa" else "Quem recebeu"
        pessoa = st.selectbox(rotulo, list(mapa_membros.keys()))
        observacoes = st.text_area("Observações", max_chars=500)

        salvar = st.form_submit_button(
            "Salvar lançamento",
            type="primary",
            width="stretch",
        )

    if salvar:
        if not descricao.strip():
            st.error("Informe a descrição.")
        elif valor <= 0:
            st.error("O valor deve ser maior que zero.")
        else:
            try:
                dados.inserir_lancamento(
                    {
                        "familia_id": contexto["familia_id"],
                        "tipo": tipo,
                        "descricao": descricao.strip(),
                        "valor": round(valor, 2),
                        "data_lancamento": data_lancamento.isoformat(),
                        "categoria_id": mapa_categorias[categoria],
                        "forma_pagamento": forma,
                        "pago_por": mapa_membros[pessoa],
                        "registrado_por": contexto["eu"]["id"],
                        "observacoes": observacoes.strip() or None,
                    }
                )
                st.success("Lançamento salvo.")
                st.rerun()
            except Exception:
                st.error(
                    "Não foi possível salvar o lançamento. "
                    "Confira as configurações e permissões do banco."
                )

    st.divider()
    st.subheader(f"Lançamentos de {nome_mes(mes)}")

    df = dados.listar_lancamentos(mes)

    if df.empty:
        st.info("Nenhum lançamento neste mês.")
        return

    for _, registro in df.iterrows():
        sinal = "−" if registro["tipo"] == "despesa" else "+"
        titulo = (
            f"{data_br(registro['data_lancamento'])} · "
            f"{registro['descricao']} · "
            f"{sinal}{moeda(registro['valor'])}"
        )

        with st.expander(titulo):
            st.write(f"**Categoria:** {registro['categoria']}")
            st.write(
                "**Forma de pagamento:** "
                f"{FORMAS_PAGAMENTO.get(registro['forma_pagamento'], '-')}"
            )
            st.write(
                "**Pago/recebido por:** "
                f"{nome_membro(contexto, registro['pago_por'])}"
            )
            st.write(
                "**Registrado por:** "
                f"{nome_membro(contexto, registro['registrado_por'])}"
            )

            if registro["observacoes"]:
                st.write(f"**Observações:** {registro['observacoes']}")

            confirmar = st.checkbox(
                "Confirmo que quero excluir este lançamento",
                key=f"confirmar_{registro['id']}",
            )

            if st.button(
                "Excluir lançamento",
                key=f"excluir_{registro['id']}",
                disabled=not confirmar,
            ):
                try:
                    dados.excluir_lancamento(registro["id"])
                    st.rerun()
                except Exception:
                    st.error("Não foi possível excluir o lançamento.")


def pagina_orcamento(contexto: dict, mes: date) -> None:
    categorias = dados.listar_categorias("despesa")
    planejado = dados.listar_orcamento(mes)
    df = dados.listar_lancamentos(mes)

    gastos = {}
    if not df.empty:
        despesas = df[df["tipo"] == "despesa"]
        gastos = {
            categoria_id: Decimal(str(total))
            for categoria_id, total in
            despesas.groupby("categoria_id")["valor"].sum().items()
        }

    st.subheader("Acompanhamento por categoria")

    for categoria in categorias:
        barra_categoria(
            categoria["nome"],
            gastos.get(categoria["id"], Decimal("0")),
            planejado.get(categoria["id"], Decimal("0")),
        )

    st.divider()
    st.subheader("Definir valores planejados")

    with st.form("form_orcamento"):
        novos_valores = {}

        for categoria in categorias:
            atual = float(
                planejado.get(categoria["id"], Decimal("0"))
            )
            novos_valores[categoria["id"]] = st.number_input(
                categoria["nome"],
                min_value=0.0,
                step=10.0,
                value=atual,
                format="%.2f",
                key=f"orcamento_{categoria['id']}",
            )

        salvar = st.form_submit_button(
            "Salvar orçamento",
            type="primary",
            width="stretch",
        )

    if salvar:
        try:
            for categoria_id, valor in novos_valores.items():
                dados.salvar_orcamento(
                    contexto["familia_id"],
                    categoria_id,
                    mes,
                    Decimal(str(valor)),
                )

            st.success("Orçamento salvo.")
            st.rerun()
        except Exception:
            st.error("Não foi possível salvar o orçamento.")


def principal() -> None:
    try:
        contexto = dados.carregar_contexto()
    except Exception:
        st.error(
            "Não foi possível carregar os dados. "
            "Confira as chaves, o login e as políticas do Supabase."
        )
        if st.button("Voltar ao login"):
            auth.sair()
            st.rerun()
        return

    if contexto is None or contexto["eu"]["papel"] != "admin":
        st.error("Este usuário não tem acesso à área administrativa.")
        if st.button("Sair"):
            auth.sair()
            st.rerun()
        return

    coluna_titulo, coluna_sair = st.columns([4, 1])
    coluna_titulo.title(NOME_APP)
    coluna_titulo.caption(f"Olá, {contexto['eu']['nome']}")

    if coluna_sair.button("Sair"):
        auth.sair()
        st.rerun()

    mes = seletor_mes()

    aba_resumo, aba_lancamentos, aba_orcamento = st.tabs(
        ["Resumo", "Lançamentos", "Orçamento"]
    )

    with aba_resumo:
        pagina_resumo(mes)

    with aba_lancamentos:
        pagina_lancamentos(contexto, mes)

    with aba_orcamento:
        pagina_orcamento(contexto, mes)


if auth.esta_logado():
    principal()
else:
    tela_login()