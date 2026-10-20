import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processing.deduplicator import ProductDeduplicator


def test_deduplicator_removes_exact_duplicates():
    """Usuwa powtórzony produkt o innym technicznym ID."""
    products = [
        {"id": 1, "nazwa": "Laptop Dell", "producent": "Dell", "cena": 3000.0, "procesor": "i7", "ram_gb": 16},
        {"id": 2, "nazwa": "Laptop HP", "producent": "HP", "cena": 2500.0, "procesor": "i5", "ram_gb": 8},
        {"id": 3, "nazwa": "Laptop Dell", "producent": "Dell", "cena": 3000.0, "procesor": "i7", "ram_gb": 16}, # duplikat id 1
    ]

    dedup = ProductDeduplicator()
    unique, report = dedup.deduplicate(products)

    assert len(unique) == 2
    assert report["total_before"] == 3
    assert report["unique_after"] == 2
    assert report["duplicates_removed"] == 1
    assert report["duplicates_details"][0]["duplicate_id"] == 3
    assert report["duplicates_details"][0]["matched_primary_id"] == 1


def test_deduplicator_case_insensitive():
    """Rozpoznaje duplikaty mimo różnic wielkości liter i spacji."""
    products = [
        {"id": 1, "nazwa": "Laptop Lenovo ", "producent": "LENOVO", "cena": 4000.0, "procesor": "Ryzen 7", "ram_gb": 32},
        {"id": 2, "nazwa": "laptop lenovo", "producent": "lenovo", "cena": 4000.0, "procesor": "ryzen 7", "ram_gb": 32},
    ]

    dedup = ProductDeduplicator()
    unique, report = dedup.deduplicate(products)

    assert len(unique) == 1
    assert report["duplicates_removed"] == 1
