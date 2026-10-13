import sys
from pathlib import Path

# Dodanie katalogu scraper do PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processing.cleaners import clean_price


def test_clean_price_pln_standard():
    assert clean_price("1 299,00 zł") == 1299.00
    assert clean_price("450,50 zł") == 450.50
    assert clean_price("14 500,00 zł") == 14500.00


def test_clean_price_html_entities_and_hard_spaces():
    assert clean_price("1&nbsp;299,00 zł") == 1299.00
    assert clean_price("2\xa0499,99 zł") == 2499.99


def test_clean_price_eur_and_usd():
    assert clean_price("1 299,00 EUR") == 1299.00
    assert clean_price("$1 299.00") == 1299.00
    assert clean_price("$450.99") == 450.99


def test_clean_price_numeric_inputs():
    assert clean_price(1299) == 1299.00
    assert clean_price(1299.5) == 1299.50


def test_clean_price_invalid_and_missing():
    assert clean_price(None) is None
    assert clean_price("") is None
    assert clean_price("brak danych") is None
    assert clean_price("—") is None
