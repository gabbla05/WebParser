import re
from typing import List, Dict, Any, Tuple, Optional


class ProductValidator:
    """
    Walidator typów kolumn i poprawności danych (wymóg: walidacja typów wszystkich kolumn
    i raport z liczbą odrzuconych wartości).
    """

    SCHEMA = {
        "id": {"type": int, "required": True, "min": 1},
        "nazwa": {"type": str, "required": True, "min_len": 2},
        "kategoria": {"type": str, "required": True, "min_len": 2},
        "producent": {"type": str, "required": True, "min_len": 2},
        "cena": {"type": float, "required": True, "min": 1.0},
        "cena_zrodlowa": {"type": float, "required": False, "min": 0.0},
        "waluta": {"type": str, "required": False, "allowed": {"PLN", "EUR", "USD"}},
        "dostepnosc": {"type": str, "required": False},
        "ocena": {"type": float, "required": False, "min": 1.0, "max": 5.0},
        "liczba_opinii": {"type": int, "required": False, "min": 0},
        "data_dodania": {"type": str, "required": False, "regex": r"^\d{4}-\d{2}-\d{2}$"},
        "gwarancja_miesiace": {"type": int, "required": False, "min": 0},
        "procesor": {"type": str, "required": False},
        "ram_gb": {"type": int, "required": False, "min": 1},
        "dysk_ssd_gb": {"type": int, "required": False, "min": 1},
        "karta_graficzna": {"type": str, "required": False},
        "ekran_cale": {"type": float, "required": False, "min": 5.0, "max": 30.0},
        "rozdzielczosc": {"type": str, "required": False},
        "system_operacyjny": {"type": str, "required": False},
        "waga_kg": {"type": float, "required": False, "min": 0.1, "max": 20.0},
        "kolor": {"type": str, "required": False},
        "kod_producenta": {"type": str, "required": False},
        "porty_usb": {"type": int, "required": False, "min": 0},
        "pojemnosc_baterii_wh": {"type": int, "required": False, "min": 1},
        "stawka_vat": {"type": str, "required": False},
        "klasa_energetyczna": {"type": str, "required": False},
        "stan_magazynowy_sztuk": {"type": int, "required": False, "min": 0}
    }

    def validate_single_field(self, field: str, value: Any, rule: dict) -> Tuple[bool, Optional[str]]:
        """Sprawdza pojedynczą wartość pod kątem typu i ograniczeń."""
        if value is None:
            if rule.get("required", False):
                return False, f"Pole wymagane '{field}' ma wartość None"
            return True, None

        expected_type = rule.get("type")
        if expected_type and not isinstance(value, expected_type):
            return False, f"Oczekiwano typu {expected_type.__name__}, otrzymano {type(value).__name__}"

        # Sprawdzenie zakresów liczbowych
        if isinstance(value, (int, float)):
            if "min" in rule and value < rule["min"]:
                return False, f"Wartość {value} mniejsza niż min ({rule['min']})"
            if "max" in rule and value > rule["max"]:
                return False, f"Wartość {value} większa niż max ({rule['max']})"

        # Sprawdzenie ograniczeń tekstowych
        if isinstance(value, str):
            if "min_len" in rule and len(value.strip()) < rule["min_len"]:
                return False, f"Długość tekstu mniejsza niż {rule['min_len']}"
            if "allowed" in rule and value not in rule["allowed"]:
                return False, f"Wartość '{value}' spoza dozwolonych {rule['allowed']}"
            if "regex" in rule and not re.match(rule["regex"], value):
                return False, f"Wartość '{value}' nie pasuje do wzorca {rule['regex']}"

        return True, None

    def validate(self, products: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Waliduje listę produktów, koryguje nieprawidłowe wartości (zamiana na None)
        i generuje szczegółowy raport walidacji.
        """
        validated_products = []
        invalid_counts = {col: 0 for col in self.SCHEMA}
        missing_counts = {col: 0 for col in self.SCHEMA}
        rejection_details = []

        for p_idx, prod in enumerate(products):
            clean_item = dict(prod)
            for field, rule in self.SCHEMA.items():
                val = clean_item.get(field)
                if val is None:
                    missing_counts[field] += 1
                    if rule.get("required", False):
                        invalid_counts[field] += 1
                        rejection_details.append({
                            "product_id": clean_item.get("id", p_idx),
                            "field": field,
                            "reason": "Brak wymaganej wartości"
                        })
                    continue

                is_valid, reason = self.validate_single_field(field, val, rule)
                if not is_valid:
                    invalid_counts[field] += 1
                    rejection_details.append({
                        "product_id": clean_item.get("id", p_idx),
                        "field": field,
                        "value": val,
                        "reason": reason
                    })
                    # Oczyszczenie błędnej wartości na None bez przerywania działania
                    clean_item[field] = None

            validated_products.append(clean_item)

        report = {
            "total_records": len(products),
            "columns_checked": len(self.SCHEMA),
            "total_rejected_values": sum(invalid_counts.values()),
            "invalid_counts_by_column": {k: v for k, v in invalid_counts.items() if v > 0},
            "missing_counts_by_column": missing_counts,
            "rejection_details": rejection_details[:50]  # podgląd pierwszych 50 błędów
        }

        return validated_products, report
