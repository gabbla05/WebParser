from typing import List, Dict, Any, Tuple, Optional


class ProductDeduplicator:
    """
    Moduł odpowiedzialny za identyfikację i usuwanie zduplikowanych rekordów.
    Zgodnie z wymaganiami projektu (min. 8 zduplikowanych rekordów),
    rekordy mogą mieć różne identyfikatory techniczne (id), ale reprezentować
    ten sam produkt (ta sama nazwa, producent, parametry i cena).
    """

    DEFAULT_KEY_FIELDS = ("nazwa", "producent", "cena", "procesor", "ram_gb")

    def __init__(self, key_fields: Optional[Tuple[str, ...]] = None):
        self.key_fields = key_fields or self.DEFAULT_KEY_FIELDS

    def build_dedup_key(self, product: Dict[str, Any]) -> tuple:
        """Tworzy krotkę unikalności na podstawie zdefiniowanych pól kluczowych."""
        key_parts = []
        for field in self.key_fields:
            val = product.get(field)
            if isinstance(val, str):
                key_parts.append(val.strip().lower())
            else:
                key_parts.append(val)
        return tuple(key_parts)

    def deduplicate(self, products: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Usuwa duplikaty z listy produktów.
        Zwraca:
            (unikalne_produkty, raport_deduplikacji)
        """
        seen_keys = {}
        unique_products = []
        duplicate_records = []

        for idx, product in enumerate(products):
            key = self.build_dedup_key(product)
            
            # Jeśli brak kluczowych wartości (np. pusta nazwa), sprawdzamy po id
            if all(v is None for v in key):
                key = (product.get("id", idx),)

            if key in seen_keys:
                primary_product = seen_keys[key]
                duplicate_records.append({
                    "duplicate_id": product.get("id"),
                    "duplicate_name": product.get("nazwa"),
                    "matched_primary_id": primary_product.get("id"),
                    "matched_primary_name": primary_product.get("nazwa")
                })
            else:
                seen_keys[key] = product
                unique_products.append(product)

        report = {
            "total_before": len(products),
            "unique_after": len(unique_products),
            "duplicates_removed": len(duplicate_records),
            "duplicates_details": duplicate_records
        }

        return unique_products, report
