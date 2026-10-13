import sys
from pathlib import Path

# Dodanie katalogu scraper do PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processing.cleaners import normalize_missing, clean_product_record


def test_normalize_missing_standard_phrases():
    assert normalize_missing("Brak danych") is None
    assert normalize_missing("brak informacji") is None
    assert normalize_missing("Brak danych gwarancyjnych") is None
    assert normalize_missing("brak opinii") is None
    assert normalize_missing("—") is None
    assert normalize_missing("-") is None
    assert normalize_missing("") is None
    assert normalize_missing(None) is None


def test_normalize_missing_valid_data():
    assert normalize_missing("Lenovo") == "Lenovo"
    assert normalize_missing("Windows 11") == "Windows 11"
    assert normalize_missing("16 GB") == "16 GB"


def test_clean_product_record_missing_handling():
    raw = {
        "id": "1",
        "nazwa": "Laptop Testowy",
        "kategoria": "Laptopy",
        "producent": "Producent: Dell",
        "cena": "2 500,00 zł",
        "dostepnosc": "W magazynie",
        "ocena": "⭐ 4.5 / 5.0 (brak opinii)",
        "liczba_opinii": "brak opinii",
        "data_dodania": "2025-01-01",
        "gwarancja": "Brak danych gwarancyjnych",
        "kod_producenta": "brak informacji",
        "ram_gb": "16 GB",
        "dysk_ssd_gb": "512 GB"
    }

    cleaned = clean_product_record(raw)

    assert cleaned["id"] == 1
    assert cleaned["producent"] == "Dell"
    assert cleaned["cena"] == 2500.00
    assert cleaned["ocena"] == 4.5
    assert cleaned["liczba_opinii"] is None
    assert cleaned["gwarancja_miesiace"] is None
    assert cleaned["kod_producenta"] is None
    assert cleaned["ram_gb"] == 16
    assert cleaned["dysk_ssd_gb"] == 512
