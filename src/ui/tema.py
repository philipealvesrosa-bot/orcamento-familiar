"""Estilo visual do aplicativo."""

import streamlit as st

from src.config import CORES


def aplicar_tema() -> None:
    st.markdown(
        f"""
        <style>
        .block-container {{
            padding-top: 1.5rem;
            max-width: 1100px;
        }}

        h1, h2, h3 {{
            color: {CORES["bordo"]};
        }}

        div[data-testid="stMetric"] {{
            background: #FFFFFF;
            border-left: 5px solid {CORES["bordo"]};
            border-radius: 10px;
            padding: 12px 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}

        .cat-linha {{
            margin-bottom: 14px;
        }}

        .cat-topo {{
            display: flex;
            justify-content: space-between;
            font-size: 0.95rem;
            gap: 8px;
        }}

        .barra-fundo {{
            background: {CORES["rosa_claro"]};
            border-radius: 8px;
            height: 12px;
            overflow: hidden;
        }}

        .barra {{
            height: 12px;
            border-radius: 8px;
        }}

        @media (max-width: 640px) {{
            .block-container {{
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )