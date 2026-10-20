import sys
from pathlib import Path

# Dodanie katalogu scraper do PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processing.cleaners import clean_price, clean_product_record


def test_clean_price_pln_standard():
    """Parsuje typowe kwoty PLN z polskim separatorem dziesiętnym."""
    assert clean_price("1 299,00 zł") == 1299.00
    assert clean_price("450,50 zł") == 450.50
    assert clean_price("14 500,00 zł") == 14500.00


def test_clean_price_html_entities_and_hard_spaces():
    """Obsługuje encje HTML i twarde spacje w zapisie ceny."""
    assert clean_price("1&nbsp;299,00 zł") == 1299.00
    assert clean_price("2\xa0499,99 zł") == 2499.99


def test_clean_price_eur_and_usd():
    """Przelicza ceny EUR i USD do PLN według ustalonych kursów."""
    assert clean_price("1 299,00 EUR") == 5585.70
    assert clean_price("$1 299.00") == 5131.05
    assert clean_price("$450.99") == 1781.41


def test_clean_product_uses_authoritative_pln_price_and_preserves_source_price():
    """Preferuje cenę bazową PLN i zachowuje kwotę źródłową oddzielnie."""
    cleaned = clean_product_record({
        "waluta": "EUR",
        "cena": "100,00 EUR",
        "cena_bazowa_pln": 430,
    })

    assert cleaned["cena"] == 430.00
    assert cleaned["cena_zrodlowa"] == 100.00
    assert cleaned["waluta"] == "EUR"


def test_clean_price_numeric_inputs():
    """Akceptuje całkowite i zmiennoprzecinkowe ceny w PLN."""
    assert clean_price(1299) == 1299.00
    assert clean_price(1299.5) == 1299.50


def test_clean_price_invalid_and_missing():
    """Zwraca None dla nieprawidłowych oraz brakujących cen."""
    assert clean_price(None) is None
    assert clean_price("") is None
    assert clean_price("brak danych") is None
    assert clean_price("—") is None
