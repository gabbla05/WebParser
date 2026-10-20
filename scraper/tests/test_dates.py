import sys
from datetime import datetime
from pathlib import Path

# Dodanie katalogu scraper do PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processing.cleaners import clean_date


REF_DATE = datetime(2025, 6, 15)


def test_clean_date_iso():
    """Akceptuje poprawne daty zapisane w formacie ISO."""
    assert clean_date("2025-04-12", reference_date=REF_DATE) == "2025-04-12"
    assert clean_date("2026-08-26", reference_date=REF_DATE) == "2026-08-26"


def test_clean_date_polish_format():
    """Konwertuje daty zapisane jako DD.MM.YYYY do ISO."""
    assert clean_date("12.04.2025", reference_date=REF_DATE) == "2025-04-12"
    assert clean_date("26.08.2026", reference_date=REF_DATE) == "2026-08-26"


def test_clean_date_relative_yesterday():
    """Przelicza określenie „wczoraj” względem daty referencyjnej."""
    assert clean_date("wczoraj", reference_date=REF_DATE) == "2025-06-14"


def test_clean_date_relative_days_ago():
    """Przelicza określenia liczby dni wstecz na daty ISO."""
    assert clean_date("3 dni temu", reference_date=REF_DATE) == "2025-06-12"
    assert clean_date("5 dni temu", reference_date=REF_DATE) == "2025-06-10"


def test_clean_date_with_prefixes():
    """Usuwa prefiksy prezentacyjne przed normalizacją daty."""
    assert clean_date("Dodano: 2025-04-12", reference_date=REF_DATE) == "2025-04-12"
    assert clean_date("Data wprowadzenia do oferty: 12.04.2025", reference_date=REF_DATE) == "2025-04-12"


def test_clean_date_invalid_and_missing():
    """Zwraca brak wartości dla pustych i nieobsługiwanych dat."""
    assert clean_date(None) is None
    assert clean_date("") is None
    assert clean_date("brak danych") is None
    assert clean_date("niepoprawny format") is None
