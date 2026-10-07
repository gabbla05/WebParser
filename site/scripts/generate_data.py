"""
Skrypt generatora danych do serwisu e-commerce (Rola: AUTOR).
Generuje bazę 420 produktów (minimum 400 na ocenę 5.0) z 24 atrybutami (minimum 22).

Zawiera celowe utrudnienia:
1. Różne waluty i formaty cen (PLN, EUR, USD, twarde spacje, przecinki, encje &nbsp;).
2. Braki wartości w wybranych polach u 15-20% rekordów.
3. Dokładnie 10 zduplikowanych rekordów (różne id, ta sama treść lub identyczne rekordy).
4. Niespójne formaty dat (YYYY-MM-DD, DD.MM.YYYY, 'wczoraj', '3 dni temu').
5. Encje HTML i znaki specjalne (&oacute;, &quot;, &amp;, &nbsp;).
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

PRODUCERS = ["Lenovo", "Dell", "HP", "Apple", "Asus", "Acer", "MSI", "Samsung", "Gigabyte"]
CATEGORIES = [
    "Laptopy gamingowe",
    "Ultrabooki biznesowe",
    "Stacje robocze",
    "Tablety 2w1",
    "Smartfony flagowe"
]

PROCESSORS = [
    "Intel Core i5-13500H", "Intel Core i7-13700H", "Intel Core i9-13900HX",
    "AMD Ryzen 5 7600X", "AMD Ryzen 7 7840HS", "AMD Ryzen 9 7945HX",
    "Apple M2 Pro", "Apple M3 Max", "Qualcomm Snapdragon X Elite"
]

GRAPHICS = [
    "NVIDIA GeForce RTX 4060", "NVIDIA GeForce RTX 4070", "NVIDIA GeForce RTX 4080",
    "AMD Radeon 780M", "Intel Iris Xe Graphics", "Apple Integrated GPU 16-core"
]

SCREENS = ["13.3", "14.0", "15.6", "16.0", "17.3"]
RESOLUTIONS = ["1920x1080", "2560x1440", "2880x1800", "3840x2160"]
OS_LIST = ["Windows 11 Home", "Windows 11 Pro", "macOS Sonoma", "Brak systemu (NoOS)", "Ubuntu Linux 24.04"]
COLORS = ["Gwiezdna szarość", "Czarny mat", "Srebrny metalik", "Biel polarna", "Granatowy"]
AVAILABILITY_LIST = ["W magazynie", "Ostatnie sztuki", "Brak w magazynie", "Wysyłka w 48h"]

HTML_ENTITIES = [
    ("&oacute;", "ó"),
    ("&quot;", '"'),
    ("&amp;", "&"),
    ("&nbsp;", " ")
]

def format_price(base_price_pln, currency):
    """Formatuje cenę z twardymi spacjami, przecinkami i ewentualnymi encjami."""
    if currency == "PLN":
        val = base_price_pln
        # 1 299,00 zł lub 1&nbsp;299,00 zł
        parts = f"{val:,.2f}".replace(",", " ").replace(".", ",")
        if random.random() < 0.3:
            parts = parts.replace(" ", "&nbsp;")
        return f"{parts} zł"
    elif currency == "EUR":
        val = round(base_price_pln / 4.30, 2)
        parts = f"{val:,.2f}".replace(",", " ").replace(".", ",")
        return f"{parts} EUR"
    else:  # USD
        val = round(base_price_pln / 3.95, 2)
        parts = f"{val:,.2f}".replace(",", " ")
        return f"${parts}"

def generate_date(idx):
    """Zwraca niespójne formaty dat zgodnie z wytycznymi."""
    r = random.random()
    base_date = datetime(2025, 1, 1) + timedelta(days=idx % 400)
    if r < 0.5:
        return base_date.strftime("%Y-%m-%d")
    elif r < 0.8:
        return base_date.strftime("%d.%m.%Y")
    elif r < 0.9:
        return "wczoraj"
    else:
        return f"{random.randint(2, 6)} dni temu"

def create_raw_product(p_id):
    producer = random.choice(PRODUCERS)
    category = random.choice(CATEGORIES)
    model_num = random.randint(100, 999)
    name = f"{producer} {category.split()[0]} Series-{model_num}"
    
    # Dodanie encji HTML w wybranych nazwach
    if random.random() < 0.2:
        name = name.replace(" ", "&nbsp;")
    
    base_price = random.randint(1800, 14500)
    curr_rand = random.random()
    if curr_rand < 0.75:
        currency = "PLN"
    elif curr_rand < 0.90:
        currency = "EUR"
    else:
        currency = "USD"
        
    formatted_price = format_price(base_price, currency)
    rating = round(random.uniform(3.1, 5.0), 1)
    
    # Braki danych u 15-20% rekordów
    reviews_count = None if random.random() < 0.18 else random.randint(1, 350)
    warranty_months = None if random.random() < 0.18 else random.choice([12, 24, 36])
    mfg_code = None if random.random() < 0.15 else f"{producer[:2].upper()}-{model_num}-{random.randint(1000, 9999)}"

    ram = random.choice([8, 16, 32, 64])
    ssd = random.choice([256, 512, 1024, 2048])
    weight = round(random.uniform(1.2, 2.8), 2)
    ports = random.choice([2, 3, 4, 5])
    battery = random.choice([52, 65, 75, 80, 90, 99])
    
    # Atrybuty celowo dostępne WYŁĄCZNIE w data-* (utrudnienie 4.0)
    vat_rate = "23%"
    stock_exact = random.randint(0, 45)
    energy_class = random.choice(["A+++", "A++", "A+", "B", "C"])

    return {
        "id": p_id,
        "nazwa": name,
        "kategoria": category,
        "producent": producer,
        "cena_tekst": formatted_price,
        "cena_bazowa_pln": base_price,
        "waluta": currency,
        "dostepnosc": random.choice(AVAILABILITY_LIST),
        "ocena": rating,
        "liczba_opinii": reviews_count,
        "data_dodania": generate_date(p_id),
        "gwarancja_miesiace": warranty_months,
        "link_szczegoly": f"product.html?id={p_id}",
        # Atrybuty ukryte w data-*
        "stawka_vat": vat_rate,
        "stan_magazynowy_sztuk": stock_exact,
        "klasa_energetyczna": energy_class,
        # Dodatkowe cechy do podstrony szczegółów (łącznie > 25 atrybutów)
        "procesor": random.choice(PROCESSORS),
        "ram_gb": ram,
        "dysk_ssd_gb": ssd,
        "karta_graficzna": random.choice(GRAPHICS),
        "ekran_cale": float(random.choice(SCREENS)),
        "rozdzielczosc": random.choice(RESOLUTIONS),
        "system_operacyjny": random.choice(OS_LIST),
        "waga_kg": weight,
        "kolor": random.choice(COLORS),
        "kod_producenta": mfg_code,
        "porty_usb": ports,
        "pojemnosc_baterii_wh": battery
    }

def main():
    total_unique = 410
    products = [create_raw_product(i + 1) for i in range(total_unique)]
    
    # Wstrzyknięcie 10 zduplikowanych rekordów (utrudnienie 4.0: min. 8 duplikatów)
    # Kopiujemy losowe rekordy z wcześniejszych indeksów i wstawiamy na koniec
    duplicates_to_add = 10
    for j in range(duplicates_to_add):
        source_record = products[random.randint(0, 100)].copy()
        # Zduplikowany rekord ma nowe ID lub identyczne ID (część scraperów wykrywa id, część treść)
        # Zgodnie z wytycznymi zduplikowany rekord to duplikat w danych
        dup = source_record.copy()
        dup["id"] = total_unique + j + 1
        dup["nazwa"] = source_record["nazwa"] # ta sama nazwa, parametry i cena
        products.append(dup)
        
    output_dir = Path(__file__).resolve().parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "products.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
        
    print(f"Pomyślnie wygenerowano {len(products)} rekordów do pliku {output_file}")
    print(f"- Liczba unikalnych rekordów źródłowych: {total_unique}")
    print(f"- Liczba zduplikowanych rekordów: {duplicates_to_add}")
    print(f"- Liczba atrybutów każdego rekordu: {len(products[0])}")

if __name__ == "__main__":
    main()
