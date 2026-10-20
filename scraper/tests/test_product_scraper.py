from types import SimpleNamespace
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.product_scraper import ProductScraper


def test_check_for_429_reads_retry_after_value():
    """Odczytuje czas retry z treści odpowiedzi 429 serwera laboratoryjnego."""
    scraper = ProductScraper.__new__(ProductScraper)
    scraper.driver = SimpleNamespace(
        page_source="429 Too Many Requests\nRetry-After: 7\n"
    )

    assert scraper._check_for_429() == 7.0


def test_check_for_429_returns_none_for_regular_page():
    """Nie zgłasza limitu dla strony, która nie zawiera odpowiedzi 429."""
    scraper = ProductScraper.__new__(ProductScraper)
    scraper.driver = SimpleNamespace(page_source="Product detail page")

    assert scraper._check_for_429() is None