import re


MISSING_VALUES = {
    "Brak danych",
    "brak danych",
    "brak informacji",
    "Brak informacji",
    "Brak danych gwarancyjnych"
}


def normalize_missing(value):

    if value is None:
        return None

    value = value.strip()

    if value in MISSING_VALUES:
        return None

    return value


def clean_price(value: str) -> float:

    value = value.replace("\xa0", " ")

    value = re.sub(
        r"[^\d,\.]",
        "",
        value
    )

    if "," in value:
        value = value.replace(".", "")
        value = value.replace(",", ".")

    return float(value)