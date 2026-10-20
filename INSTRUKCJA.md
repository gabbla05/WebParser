# 📘 Poradnik Projektu: WebParser (ElectroMarket) — Poziom 5.0

Kompletny przewodnik po architekturze projektu, sposobie działania poszczególnych modułów oraz instrukcja uruchamiania i testowania bez użycia asystenta AI.

---

## 1. O co chodzi w tym projekcie? (Architektura)

Projekt realizuje wymagania laboratoryjne na ocenę **5.0** i składa się z dwóch ról:

### A. Rola AUTOR (Serwis WWW + Serwer)
* **Katalog (`site/`)**:
  * Dane produktów trzymane są w pliku JSON (`site/data/products.json`) i dynamicznie wstrzykiwane do drzewa DOM za pomocą JavaScriptu (`fetch`).
  * **W kodzie źródłowym HTML (Ctrl+U) jest 0 rekordów** — tradycyjny scraper `requests + BeautifulSoup` nic tam nie znajdzie.
  * Zaimplementowano **doładowywanie porcjami** (przycisk *„Wczytaj więcej”* po 35 sztuk ze sztucznym opóźnieniem 400–1100 ms).
   * **420 rekordów** i **28 pól źródłowych** każdego produktu; po normalizacji parser eksportuje 27 kolumn.
  * Podstrony szczegółów (`product.html?id=...`) z elementem `<details>` (atrybuty widoczne dopiero po kliknięciu/rozwinięciu).
* **Własny serwer HTTP (`run_server.py`)**:
  * Wielowątkowy serwer w Pythonie (`ThreadingTCPServer`).
  * Posiada wbudowany **Rate Limiter**, który po przekroczeniu 10 zapytań/s zwraca kod błędu **HTTP 429 Too Many Requests** wraz z nagłówkiem `Retry-After: 2`.

### B. Rola PARSER (Web Scraper w Selenium)
* Steruje przeglądarką Google Chrome w trybie headless (lub w oknie).
* Używa **jawnego oczekiwania (`WebDriverWait`)** zamiast sztywnych `sleep`.
* Klika przycisk *„Wczytaj więcej”* aż do załadowania wszystkich 420 produktów w DOM.
* Wchodzi na każdą podstronę, rozwija `<details>` i wyciąga specyfikację.
* Posiada mechanizm **ponawiania z opóźnieniem wykładniczym (1s, 2s, 4s...)**, obsługuje kod 429 i nagłówek `Retry-After`.
* Przy błędach automatycznie zapisuje zrzut ekranu (`.png`) i kod strony (`.html`) do katalogu `scraper/logs/`.
* Czyści dane, waliduje typy, usuwa zduplikowane rekordy i eksportuje wyniki do wielu formatów.

---

## 2. Struktura katalogów i plików

```text
WebParser/
├── run_server.py                  # Dedykowany serwer HTTP z Rate Limitingiem (429)
├── site/                          # Serwis e-commerce ElectroMarket
│   ├── index.html                 # Główna strona katalogu
│   ├── product.html               # Szablon podstrony szczegółów produktu
│   ├── js/catalog.js              # Logika "Wczytaj więcej" i renderowania
│   ├── js/product.js              # Logika ładowania szczegółów i losowej kolejności cech
│   └── data/products.json         # Baza 420 produktów (w tym 10 celowych duplikatów)
├── scraper/                       # Kod parsera i przetwarzania danych
│   ├── browser.py                 # Konfiguracja Chrome WebDriver (flagi stabilizujące)
│   ├── logging_config.py          # Logowanie do pliku i konsoli
│   ├── main.py                    # Główny skrypt uruchomieniowy parsera
│   ├── policy.py                  # Kontrola robots.txt, regulaminu i odstępów
│   ├── scraper/
│   │   ├── catalog_scraper.py     # Doładowywanie katalogu i zbieranie linków
│   │   └── product_scraper.py     # Rozwijanie <details> i pobieranie cech
│   ├── processing/
│   │   ├── cleaners.py            # Czyszczenie cen, ujednolicanie dat i braków danych
│   │   ├── validators.py          # Walidacja typów 27 kolumn i raport odrzuceń
│   │   └── deduplicator.py        # Wykrywanie i usuwanie 10 duplikatów
│   ├── export/
│   │   └── exporter.py            # Eksport do CSV, XLSX (Excel) oraz JSON
│   ├── tests/                     # Testy jednostkowe w pytest (22 testy)
│   │   ├── test_prices.py
│   │   ├── test_dates.py
│   │   ├── test_missing_values.py
│   │   ├── test_deduplicator.py
│   │   ├── test_validators.py
│   │   └── test_product_scraper.py # Testy odpowiedzi 429 i Retry-After
│   └── output/                    # Wygenerowane pliki z wynikami
│       ├── products_clean.xlsx    # Arkusz Excela (prawidłowe typy liczb i dopasowane kolumny)
│       ├── products_clean.csv     # Plik CSV (standardowy)
│       ├── products_clean_excel_pl.csv # CSV z polskim przecinkiem
│       └── products_clean.json    # Pełne dane w formacie JSON
└── INSTRUKCJA.md                  # Ten poradnik
```

---

## 3. Jak to uruchomić krok po kroku (w terminalu)

Wszystko uruchamiasz w zwykłym terminalu (np. PowerShell lub CMD) w folderze `WebParser`.

### Krok 1: Instalacja wymaganych bibliotek
Jeśli uruchamiasz projekt na nowym komputerze, zainstaluj zależności jednym poleceniem:
```powershell
pip install selenium pandas openpyxl matplotlib pytest
```

Lub po prostu 
```powershell
pip install -r requirements.txt  
```

### Krok 2: Uruchomienie serwisu (Terminal 1)
Otwórz terminal w folderze projektu i wpisz:
```powershell
py run_server.py
```
* Serwer wystartuje pod adresem: `http://localhost:8000/`.
* Możesz wejść w przeglądarce i sprawdzić, jak działa strona oraz przycisk *„Wczytaj więcej”*.
* Pozostaw ten terminal otwarty w tle.

### Krok 3: Uruchomienie scrapera (Terminal 2)
Otwórz drugie okno terminala w folderze projektu:

* **Szybki test (np. pierwsze 10 produktów, z widocznym oknem Chrome)**:
  ```powershell
  py scraper/main.py --limit 10 --visible
  ```
* **Pełny bieg (wszystkie 420 produktów w tle / headless)**:
  ```powershell
  py scraper/main.py
  ```

Przed uruchomieniem Chrome parser automatycznie odczytuje `robots.txt` i regulamin. Niedozwolone ścieżki są blokowane, a między nawigacjami zachowywany jest największy odstęp wymagany przez `Crawl-delay` lub regulamin. `cena` w wynikach jest zawsze w PLN; `cena_zrodlowa` i `waluta` zachowują kwotę wyświetlaną w serwisie.

Podczas działania scraper na bieżąco raportuje postęp w konsoli:
```text
[1/420] (0.2%) Pobrano produkt ID=1...
[25/420] (6.0%) Pobrano produkt ID=25...
...
Deduplikacja zakończona: 420 -> 410 (usunięto duplikatów: 10)
Eksport danych: zapisano products_clean.xlsx, products_clean.csv, products_clean.json
```

### Krok 4: Uruchomienie testów jednostkowych
Aby sprawdzić funkcje czyszczące, walidujące i obsługę retry:
```powershell
py -m pytest scraper/tests -v
```
Powinnaś/powinieneś zobaczyć `22 passed` (wszystkie 22 testy zielone).

---

## 4. Gdzie są wyniki i jak je oglądać?

Pliki wyjściowe znajdują się w folderze `scraper/output/`:

1. **`products_clean.xlsx` (Najlepszy do oglądania w Excelu)**:
   * Prawdziwy plik Excela z dopasowanymi szerokościami kolumn.
   * Liczby wag i ocen są zapisane jako liczby (Excel nie zamienia ich na daty typu `2.sty`).
   * Brak znaków `########`.
2. **`products_clean.csv`**: Standardowy plik CSV rozdzielany średnikami `;`.
3. **`products_clean_excel_pl.csv`**: Wersja CSV z przecinkiem dziesiętnym dostosowana pod polskiego Excela.
4. **`products_clean.json`**: Czysta struktura obiektowa JSON.
5. **`scraper/logs/scraper.log`**: Pełny log ze znacznikami czasu.

---

## 5. Przykładowe uruchomienie

```bash
PS C:\Users\...\WebParser> (Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& c:\Users\...\WebParser\.venv\Scripts\Activate.ps1)
(.venv) PS C:\Users\...\WebParser> py scraper/main.py
2026-10-20 16:17:01,998 | INFO    | ==========================================================
2026-10-20 16:17:02,007 | INFO    | Rozpoczynanie procesu parsowania serwisu ElectroMarket (5.0)
2026-10-20 16:17:02,007 | INFO    | ==========================================================
2026-10-20 16:17:03,043 | INFO    | Lokalny serwer localhost:8000 jest już aktywny
2026-10-20 16:17:08,372 | INFO    | Polityka dostępu zaakceptowana: robots.txt dozwala katalog, regulamin wymaga co najmniej 1s między żądaniami
2026-10-20 16:17:08,372 | INFO    | Inicjalizacja Chrome WebDriver (headless=True)...
2026-10-20 16:17:14,563 | INFO    | Katalog został załadowany
2026-10-20 16:17:14,563 | INFO    | Doładowywanie wszystkich produktów przyciskiem 'Wczytaj więcej'...
2026-10-20 16:17:27,829 | INFO    | Załadowano wszystkie rekordy (wykryto end-message)
2026-10-20 16:17:48,997 | INFO    | Zebrano 420 elementów z listy katalogu
2026-10-20 16:17:48,997 | INFO    | Liczba załadowanych produktów w DOM: 420
2026-10-20 16:17:48,997 | INFO    | Rozpoczynanie pobierania szczegółów 420 produktów...
2026-10-20 16:17:50,552 | INFO    | [1/420] (0.2%) Pobrano produkt ID=1: Dell Laptopy Series-859
2026-10-20 16:17:53,364 | INFO    | [2/420] (0.5%) Pobrano produkt ID=2: Apple Stacje Series-204
2026-10-20 16:17:56,188 | INFO    | [3/420] (0.7%) Pobrano produkt ID=3: Samsung Stacje Series-266
2026-10-20 16:17:58,550 | INFO    | [4/420] (1.0%) Pobrano produkt ID=4: Acer Ultrabooki Series-771
2026-10-20 16:18:00,828 | INFO    | [5/420] (1.2%) Pobrano produkt ID=5: MSI Tablety Series-710
2026-10-20 16:18:52,969 | INFO    | [25/420] (6.0%) Pobrano produkt ID=25: Samsung Stacje Series-286
2026-10-20 16:19:57,810 | INFO    | [50/420] (11.9%) Pobrano produkt ID=60: Asus Stacje Series-982
2026-10-20 16:21:02,485 | INFO    | [75/420] (17.9%) Pobrano produkt ID=95: Asus Tablety Series-187
2026-10-20 16:22:10,065 | INFO    | [100/420] (23.8%) Pobrano produkt ID=130: Samsung Stacje Series-323
2026-10-20 16:23:15,229 | INFO    | [125/420] (29.8%) Pobrano produkt ID=165: Apple Laptopy Series-261
2026-10-20 16:24:18,361 | INFO    | [150/420] (35.7%) Pobrano produkt ID=200: Apple Laptopy Series-289
2026-10-20 16:25:23,652 | INFO    | [175/420] (41.7%) Pobrano produkt ID=235: Acer Laptopy Series-292
2026-10-20 16:26:27,154 | INFO    | [200/420] (47.6%) Pobrano produkt ID=270: MSI Stacje Series-801
2026-10-20 16:27:33,231 | INFO    | [225/420] (53.6%) Pobrano produkt ID=305: Acer Laptopy Series-401
2026-10-20 16:28:38,490 | INFO    | [250/420] (59.5%) Pobrano produkt ID=340: Asus Laptopy Series-842
2026-10-20 16:29:42,410 | INFO    | [275/420] (65.5%) Pobrano produkt ID=375: HP Smartfony Series-221
2026-10-20 16:30:47,382 | INFO    | [300/420] (71.4%) Pobrano produkt ID=410: MSI Ultrabooki Series-775
2026-10-20 16:31:53,976 | INFO    | [325/420] (77.4%) Pobrano produkt ID=100: Asus Laptopy Series-560
2026-10-20 16:32:59,270 | INFO    | [350/420] (83.3%) Pobrano produkt ID=175: Gigabyte Smartfony Series-417
2026-10-20 16:34:05,857 | INFO    | [375/420] (89.3%) Pobrano produkt ID=275: MSI Tablety Series-625
2026-10-20 16:35:10,465 | INFO    | [400/420] (95.2%) Pobrano produkt ID=350: Dell Tablety Series-169
2026-10-20 16:36:00,631 | INFO    | [420/420] (100.0%) Pobrano produkt ID=32: Acer Smartfony Series-874
2026-10-20 16:36:00,631 | INFO    | Pomyślnie pobrano surowe dane dla 420 produktów.
2026-10-20 16:36:00,631 | INFO    | Czyszczenie i standaryzacja formatów (ceny, daty, brakujące wartości)...
2026-10-20 16:36:00,702 | INFO    | Walidacja typów kolumn i sprawdzanie ograniczeń biznesowych...
2026-10-20 16:36:00,709 | INFO    | Raport walidacji: sprawdzono 27 kolumn, odrzucono 0 wartości.
2026-10-20 16:36:00,709 | INFO    | Deduplikacja rekordów...
2026-10-20 16:36:00,716 | INFO    | Deduplikacja zakończona: 420 -> 410 (usunięto duplikatów: 10)
2026-10-20 16:36:00,716 | INFO    | Eksport danych do formatów CSV i JSON...
2026-10-20 16:36:01,170 | INFO    | Zapisano czyste dane: C:\Users\...\WebParser\scraper\output\products_clean.csv (93.69 KB)
2026-10-20 16:36:01,170 | INFO    | Zapisano czyste JSON: C:\Users\...\WebParser\scraper\output\products_clean.json (333.14 KB)
2026-10-20 16:36:01,669 | INFO    | ==========================================================
2026-10-20 16:36:01,669 | INFO    | PODSUMOWANIE PROCESU:
2026-10-20 16:36:01,672 | INFO    | Czas działania: 1139.67 s
2026-10-20 16:36:01,672 | INFO    | Wszystkich pobranych rekordów: 420
2026-10-20 16:36:01,672 | INFO    | Zidentyfikowanych duplikatów: 10
2026-10-20 16:36:01,672 | INFO    | Unikalnych rekordów końcowych: 410
2026-10-20 16:36:01,674 | INFO    | Liczba kolumn w rekordzie: 27
2026-10-20 16:36:01,674 | INFO    | Pliki wyjściowe: C:\Users\...\WebParser\scraper\output\products_clean.csv, C:\Users\...\WebParser\scraper\output\products_clean.json
2026-10-20 16:36:01,674 | INFO    | ==========================================================
2026-10-20 16:36:04,291 | INFO    | Przeglądarka została zamknięta.
(.venv) PS C:\Users\...\WebParser> 
```