from datetime import date

from src.ui.formatos import data_br, mes_anterior, moeda, proximo_mes


def test_moeda():
    assert moeda(1234.5) == "R$ 1.234,50"
    assert moeda(0) == "R$ 0,00"


def test_data_br():
    assert data_br("2026-11-08") == "08/11/2026"


def test_virada_de_ano():
    assert proximo_mes(date(2026, 12, 15)) == date(2027, 1, 1)
    assert mes_anterior(date(2026, 1, 20)) == date(2025, 12, 1)