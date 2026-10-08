# skrypt do wyszukiwania duplikatów obecnych w pliku products.json, aby udowodnić istnienie dupikatów wymaganych w projekcie

import json
from collections import Counter

sciezka_do_pliku = "site/data/products.json"
klucz = "nazwa"  # Zmień na pole, które sprawdzasz

wystapienia = Counter()

# Zakładamy, że JSON to duża lista obiektów
with open(sciezka_do_pliku, "r", encoding="utf-8") as f:
    # Jeśli plik to jedna wielka lista, biblioteka ijson byłaby idealna,
    # ale dla standardowego json.load():
    dane = json.load(f)
    for element in dane:
        if klucz in element:
            wystapienia[element[klucz]] += 1

# Wyświetl tylko duplikaty
duplikaty = {k: v for k, v in wystapienia.items() if v > 1}
print("Znalezione duplikaty (wartość: liczba wystąpień):")
print(json.dumps(duplikaty, indent=2))
