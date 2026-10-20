import re
import html
from datetime import datetime, timedelta
from typing import Any, Optional


MISSING_VALUES = {
    "brak danych",
    "brak informacji",
    "brak danych gwarancyjnych",
    "brak zarejestrowanych opinii",
    "brak opinii",
    "brak",
    "—",
    "-",
    "n/a",
    "none",
    "null",
    ""
}

# w przyszłości można by pobierać kursy z API NBP np. ale na potrzebe ćwiczenia przyjmujemy stałe kursy
CURRENCY_RATES_TO_PLN = {
    "PLN": 1.0,
    "EUR": 4.30,
    "USD": 3.95,
}


def normalize_missing(value: Any) -> Optional[str]:
    """Zwraca None jeśli wartość oznacza brak danych lub jest pusta."""
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    cleaned = value.strip()
    if cleaned.lower() in MISSING_VALUES:
        return None

    return cleaned


def decode_html_entities(text: Optional[str]) -> Optional[str]:
    """Dekoduje encje HTML (np. &oacute;, &nbsp;, &quot;) i usuwa twarde spacje."""
    if text is None:
        return None
    # Podwójne odkodowanie dla bezpieczeństwa encji zagnieżdżonych
    decoded = html.unescape(text)
    decoded = decoded.replace("\xa0", " ").strip()
    return decoded


def _price_currency(value: Any, currency: Optional[str] = None) -> Optional[str]:
    """Ustala obsługiwaną walutę z argumentu lub oznaczenia w tekście ceny."""
    if currency:
        normalized = currency.strip().upper()
        return normalized if normalized in CURRENCY_RATES_TO_PLN else None

    text = str(value).upper()
    if "EUR" in text:
        return "EUR"
    if "USD" in text or "$" in text:
        return "USD"
    if "PLN" in text or "ZŁ" in text:
        return "PLN"
    return "PLN"


def _parse_price_amount(value: Any, currency: Optional[str] = None) -> Optional[float]:
    """Parsuje samą kwotę źródłową bez przeliczania jej na PLN."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return round(float(value), 2)

    val_str = decode_html_entities(str(value))
    if not val_str or normalize_missing(val_str) is None:
        return None

    normalized_currency = _price_currency(val_str, currency)
    if normalized_currency is None:
        return None

    val_str = re.sub(r"(?i)PLN|EUR|USD|zł", "", val_str).replace("$", "").strip()
    val_str = re.sub(r"[^\d,\.]", "", val_str)
    if not val_str:
        return None

    if "," in val_str and "." in val_str:
        if val_str.rfind(",") > val_str.rfind("."):
            val_str = val_str.replace(".", "").replace(",", ".")
        else:
            val_str = val_str.replace(",", "")
    elif "," in val_str:
        trailing_digits = len(val_str.rsplit(",", 1)[-1])
        if normalized_currency == "USD" and trailing_digits == 3:
            val_str = val_str.replace(",", "")
        else:
            val_str = val_str.replace(",", ".")

    try:
        return round(float(val_str), 2)
    except ValueError:
        return None


def clean_price(value: Any, currency: Optional[str] = None) -> Optional[float]:
    """
    Czyści i konwertuje cenę (np. '1 299,00 zł', '$1 299.00', '1 299,00 EUR') na float.
    Obsługuje encje HTML (&nbsp;), twarde spacje, przecinki i kropki.
    """
    normalized_currency = _price_currency(value, currency)
    if normalized_currency is None:
        return None

    amount = _parse_price_amount(value, normalized_currency)
    if amount is None:
        return None

    return round(amount * CURRENCY_RATES_TO_PLN[normalized_currency], 2)


def clean_date(value: Any, reference_date: Optional[datetime] = None) -> Optional[str]:
    """
    Ujednolica niespójne formaty dat do ISO YYYY-MM-DD.
    Obsługuje:
    - YYYY-MM-DD (np. '2025-04-12')
    - DD.MM.YYYY (np. '12.04.2025')
    - 'wczoraj'
    - 'X dni temu' (np. '3 dni temu')
    - Prefiksy takie jak 'Dodano: ' lub 'Data wprowadzenia do oferty: '
    """
    if value is None:
        return None

    val_str = decode_html_entities(str(value))
    val_str = normalize_missing(val_str)
    if not val_str:
        return None

    # Usunięcie prefiksów
    val_str = re.sub(r"^(?:Data wprowadzenia do oferty|Dodano):\s*", "", val_str, flags=re.IGNORECASE).strip()

    if reference_date is None:
        reference_date = datetime.now()

    lower_val = val_str.lower()
    if lower_val == "wczoraj":
        target_date = reference_date - timedelta(days=1)
        return target_date.strftime("%Y-%m-%d")

    days_ago_match = re.match(r"^(\d+)\s+dni\s+temu$", lower_val)
    if days_ago_match:
        days = int(days_ago_match.group(1))
        target_date = reference_date - timedelta(days=days)
        return target_date.strftime("%Y-%m-%d")

    # Format YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", val_str):
        try:
            parsed = datetime.strptime(val_str, "%Y-%m-%d")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            return None

    # Format DD.MM.YYYY
    if re.match(r"^\d{2}\.\d{2}\.\d{4}$", val_str):
        try:
            parsed = datetime.strptime(val_str, "%d.%m.%Y")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


def clean_rating(value: Any) -> Optional[float]:
    """Wyciąga ocenę jako float (np. '⭐ 4.5 / 5.0' -> 4.5)."""
    if value is None:
        return None
    val_str = decode_html_entities(str(value))
    val_str = normalize_missing(val_str)
    if not val_str:
        return None

    match = re.search(r"(\d+(?:[.,]\d+)?)", val_str)
    if match:
        try:
            return round(float(match.group(1).replace(",", ".")), 2)
        except ValueError:
            return None
    return None


def clean_reviews_count(value: Any) -> Optional[int]:
    """Wyciąga liczbę opinii jako int (np. '(123 opinii klientów)' -> 123, lub bezpośrednio 123)."""
    if value is None:
        return None
    if isinstance(value, int):
        return value

    val_str = decode_html_entities(str(value))
    if not val_str or normalize_missing(val_str) is None:
        return None

    if "brak" in val_str.lower():
        return None

    # Szukamy liczby w nawiasie (np. "(123 opinii klientów)" lub "(123)")
    match_paren = re.search(r"\(\s*(\d+)", val_str)
    if match_paren:
        try:
            return int(match_paren.group(1))
        except ValueError:
            pass

    match = re.search(r"(\d+)", val_str)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def clean_warranty_months(value: Any) -> Optional[int]:
    """Wyciąga liczbę miesięcy gwarancji jako int (np. '24 miesięcy gwarancji producenta' -> 24)."""
    if value is None:
        return None
    if isinstance(value, int):
        return value

    val_str = decode_html_entities(str(value))
    if not val_str or normalize_missing(val_str) is None:
        return None

    if "brak" in val_str.lower():
        return None

    match = re.search(r"(\d+)", val_str)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def clean_numeric_spec(value: Any, target_type: type[int | float] = int) -> Optional[Any]:
    """Wyciąga wartość numeryczną ze specyfikacji (np. '16 GB' -> 16, '1.85 kg' -> 1.85)."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return target_type(value)

    val_str = decode_html_entities(str(value))
    if not val_str or normalize_missing(val_str) is None:
        return None

    # Dopasowanie liczby całkowitej lub zmiennoprzecinkowej
    pattern = r"(\d+(?:[.,]\d+)?)" if target_type is float else r"(\d+)"
    match = re.search(pattern, val_str)
    if match:
        try:
            num_str = match.group(1).replace(",", ".")
            return target_type(float(num_str)) if target_type is float else int(num_str)
        except ValueError:
            return None
    return None


def clean_product_record(raw_product: dict, reference_date: Optional[datetime] = None) -> dict:
    """
    Czyści i ujednolica cały surowy słownik produktu.
    """
    cleaned = {}

    # ID
    raw_id = raw_product.get("id")
    cleaned["id"] = int(raw_id) if raw_id is not None and str(raw_id).isdigit() else None

    # Pola tekstowe
    for text_key in ["nazwa", "kategoria", "system_operacyjny", "procesor", "karta_graficzna", "rozdzielczosc", "kolor"]:
        raw_val = raw_product.get(text_key)
        cleaned[text_key] = decode_html_entities(normalize_missing(raw_val))

    # Producent (usunięcie ewentualnego prefiksu 'Producent: ')
    prod_val = raw_product.get("producent")
    if prod_val:
        prod_val = re.sub(r"^Producent:\s*", "", str(prod_val), flags=re.IGNORECASE).strip()
        cleaned["producent"] = decode_html_entities(normalize_missing(prod_val))
    else:
        cleaned["producent"] = None

    # Dostępność
    cleaned["dostepnosc"] = decode_html_entities(normalize_missing(raw_product.get("dostepnosc")))

    # Waluta i ceny
    currency = (raw_product.get("waluta") or "PLN").upper()
    source_price = raw_product.get("cena") or raw_product.get("cena_tekst")
    cleaned["waluta"] = currency
    cleaned["cena_zrodlowa"] = _parse_price_amount(source_price, currency)
    base_pln = raw_product.get("cena_bazowa_pln")
    cleaned["cena"] = clean_price(base_pln, "PLN") if base_pln is not None else clean_price(source_price, currency)

    # Ocena i opinie
    cleaned["ocena"] = clean_rating(raw_product.get("ocena"))
    reviews_value = raw_product.get("liczba_opinii")
    if reviews_value is None and isinstance(raw_product.get("ocena"), str):
        reviews_value = raw_product["ocena"]
    cleaned["liczba_opinii"] = clean_reviews_count(reviews_value)

    # Data dodania
    cleaned["data_dodania"] = clean_date(raw_product.get("data_dodania"), reference_date=reference_date)

    # Gwarancja
    cleaned["gwarancja_miesiace"] = clean_warranty_months(
        raw_product.get("gwarancja") or raw_product.get("gwarancja_miesiace")
    )

    # Specyfikacja techniczna
    cleaned["ram_gb"] = clean_numeric_spec(raw_product.get("ram_gb"), int)
    cleaned["dysk_ssd_gb"] = clean_numeric_spec(raw_product.get("dysk_ssd_gb"), int)
    cleaned["waga_kg"] = clean_numeric_spec(raw_product.get("waga_kg"), float)
    cleaned["ekran_cale"] = clean_numeric_spec(raw_product.get("ekran_cale"), float)
    cleaned["porty_usb"] = clean_numeric_spec(raw_product.get("porty_usb"), int)
    cleaned["pojemnosc_baterii_wh"] = clean_numeric_spec(raw_product.get("pojemnosc_baterii_wh"), int)

    # Kod producenta
    mfg_code = raw_product.get("kod_producenta")
    cleaned["kod_producenta"] = decode_html_entities(normalize_missing(mfg_code))

    # Cechy z data-* (jeśli przekazane)
    cleaned["stawka_vat"] = raw_product.get("stawka_vat") or raw_product.get("data_vat")
    cleaned["klasa_energetyczna"] = raw_product.get("klasa_energetyczna") or raw_product.get("data_energy_class")
    stock = raw_product.get("stan_magazynowy_sztuk")
    if stock is None:
        stock = raw_product.get("data_stock_count")
    cleaned["stan_magazynowy_sztuk"] = clean_numeric_spec(stock, int) if stock is not None else None

    return cleaned