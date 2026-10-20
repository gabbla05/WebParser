import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processing.validators import ProductValidator


def test_validator_valid_product():
    """Akceptuje rekord z poprawnymi typami i wartościami."""
    validator = ProductValidator()
    products = [{
        "id": 1,
        "nazwa": "Dell XPS 15",
        "kategoria": "Ultrabooki",
        "producent": "Dell",
        "cena": 6500.00,
        "ocena": 4.8,
        "ram_gb": 32,
        "data_dodania": "2025-05-20"
    }]

    validated, report = validator.validate(products)

    assert len(validated) == 1
    assert report["total_rejected_values"] == 0


def test_validator_invalid_types_and_ranges():
    """Odrzuca wartości poza zakresem i czyści błędne pola."""
    validator = ProductValidator()
    products = [{
        "id": 1,
        "nazwa": "Dell XPS 15",
        "kategoria": "Ultrabooki",
        "producent": "Dell",
        "cena": -50.0,         # błędna ujemna cena
        "ocena": 8.5,          # ocena > 5.0
        "data_dodania": "niepoprawna data" # zły format daty
    }]

    validated, report = validator.validate(products)

    assert report["total_rejected_values"] == 3
    assert validated[0]["cena"] is None
    assert validated[0]["ocena"] is None
    assert validated[0]["data_dodania"] is None
