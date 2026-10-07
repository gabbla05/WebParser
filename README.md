# WebParser – Laboratorium 1 (Zadanie na ocenę 5.0)

Projekt serwisu internetowego oraz parsera danych (web scraper) przygotowany w ramach Laboratorium nr 1.

---

## 📁 Struktura Projektu

```text
WebParser/
├── site/                           # ROLA AUTOR (Serwis WWW)
│   ├── css/
│   │   └── style.css               # Nowoczesne style CSS
│   ├── data/
│   │   └── products.json           # Baza 420 produktów (25 atrybutów)
│   ├── js/
│   │   ├── catalog.js              # Fetch, ładowanie porcjami, opóźnienie 400-1100ms
│   │   └── product.js              # Podstrona produktu, interakcja, tasowanie cech
│   ├── scripts/
│   │   └── generate_data.py        # Generator bazy produktów z utrudnieniami
│   ├── index.html                  # Strona główna katalogu (brak danych w źródle HTML)
│   └── product.html                # Podstrona szczegółów pojedynczego produktu
├── scraper/                        # ROLA PARSER (Parser Selenium, czyszczenie, testy)
├── analysis/                       # ANALIZA DANYCH (Pandas, statystyki, wykresy)
├── report/                         # SPRAWOZDANIE (PDF)
├── run_server.py                   # Lokalny serwer deweloperski
├── Lab1.pdf                        # Treść zadania laboratoryjnego
└── README.md
```

---

## 🚀 Uruchomienie Serwisu (Rola AUTOR)

Aby uruchomić serwis lokalnie, wykonaj w terminalu polecenie:

```bash
python run_server.py
```

Serwis będzie dostępny pod adresem: **http://localhost:8000/**

---

## 📋 Zrealizowane wymagania roli AUTOR (Poziom 5.0)

### Wymagania obowiązkowe:
1. **Dynamiczne wstrzykiwanie przez JavaScript (`fetch`):**
   - W źródle HTML (`Ctrl+U` w przeglądarce lub w zapytaniu `requests.get()`) znajduje się dokładnie **0 rekordów**.
   - Wszystkie produkty są pobierane asynchronicznie z pliku `products.json` i renderowane dynamicznie w drzewie DOM.
2. **Doładowywanie porcjami:**
   - Przycisk *„Wczytaj więcej produktów”* ładuje dane partiami po 35 sztuk.
   - Sztuczne opóźnienie symulowane w JavaScript wynosi od **400 ms do 1100 ms** (wymóg: 300–2000 ms).
   - Wyświetla spinner ładowania oraz informację o wyczerpaniu bazy po doładowaniu wszystkich rekordów.
3. **Wolumen danych i cechy:**
   - **420 rekordów** w bazie (wymóg: min. 400).
   - **25 atrybutów** każdego rekordu (wymóg: min. 22).
4. **Dwie różne struktury zapisu rekordów na liście:**
   - 70% porcji renderowane jako powtarzalne karty `<article class="product-card produkt">`.
   - 30% porcji renderowane w tabeli `<table class="products-table">` z wierszami `<tr>`.
5. **Podstrony szczegółów:**
   - Każdy rekord posiada podstronę szczegółów pod adresem `product.html?id=...`, również wstrzykiwaną dynamicznie przez JS.
6. **Semantyczne nazewnictwo i atrybuty `data-*`:**
   - Zastosowano czytelne selektory semantyczne (`.cena`, `.nazwa`, `.producent`, `.kategoria`, `.ocena`, `.dostepnosc`).
   - W elementach zawarto atrybuty danych: `data-id`, `data-rating`, `data-in-stock`, `data-category`.

---

## 🎯 Zaimplementowane Utrudnienia

### Utrudnienia z poziomu 4.0:
1. **Zróżnicowane waluty i formaty cen:**
   - Większość w PLN (`1 299,00 zł`), część w EUR (`350,50 EUR`) i USD (`$450.00`).
   - Zastosowanie przecinków, spacji i encji `&nbsp;` jako separatorów tysięcy.
2. **Braki wartości w wybranych polach:**
   - Kolumny `liczba_opinii`, `gwarancja_miesiace` oraz `kod_producenta` zawierają braki danych u ok. 18% rekordów (oznaczone jako brak informacji).
3. **Zduplikowane rekordy:**
   - Do bazy celowo wstrzyknięto **10 zduplikowanych rekordów** (ta sama nazwa, specyfikacja i cena) rozrzuconych po różnych partiach (wymóg: min. 8).
4. **Niespójne formaty dat:**
   - Data dodania występuje w formatach: `YYYY-MM-DD`, `DD.MM.YYYY`, `wczoraj` oraz `X dni temu`.
5. **Encje HTML i znaki specjalne:**
   - W nazwach i cenach celowo użyto encji `&nbsp;`, `&oacute;`, `&quot;`, `&amp;`.

### Utrudnienia z poziomu 5.0:
1. **Atrybuty widoczne dopiero po interakcji:**
   - Na podstronie szczegółów specyfikacja techniczna (procesor, RAM, dysk, GPU, ekran, waga itp.) znajduje się w interaktywnym elemencie `<details id="tech-specs-toggle">`.
   - Parser partnera musi rozwinąć sekcję (kliknąć `<summary>`), aby odczytać dane.
2. **Losowa kolejność atrybutów w specyfikacji:**
   - Lista atrybutów w specyfikacji technicznej jest losowo tasowana przed wyrenderowaniem do DOM.
   - Parser nie może polegać na stałej pozycji w liście (np. `nth-child`), lecz musi mapować wartości po kluczu / etykiecie (`.spec-label` lub `[data-spec-key]`).
