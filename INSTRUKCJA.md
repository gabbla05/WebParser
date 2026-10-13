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
  * **420 rekordów** i **27 atrybutów** każdego produktu.
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
│   ├── scraper/
│   │   ├── catalog_scraper.py     # Doładowywanie katalogu i zbieranie linków
│   │   └── product_scraper.py     # Rozwijanie <details> i pobieranie cech
│   ├── processing/
│   │   ├── cleaners.py            # Czyszczenie cen, ujednolicanie dat i braków danych
│   │   ├── validators.py          # Walidacja typów 27 kolumn i raport odrzuceń
│   │   └── deduplicator.py        # Wykrywanie i usuwanie 10 duplikatów
│   ├── export/
│   │   └── exporter.py            # Eksport do CSV, XLSX (Excel) oraz JSON
│   ├── tests/                     # Testy jednostkowe w pytest (18 testów)
│   │   ├── test_prices.py
│   │   ├── test_dates.py
│   │   ├── test_missing_values.py
│   │   ├── test_deduplicator.py
│   │   └── test_validators.py
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

Podczas działania scraper na bieżąco raportuje postęp w konsoli:
```text
[1/420] (0.2%) Pobrano produkt ID=1...
[25/420] (6.0%) Pobrano produkt ID=25...
...
Deduplikacja zakończona: 420 -> 410 (usunięto duplikatów: 10)
Eksport danych: zapisano products_clean.xlsx, products_clean.csv, products_clean.json
```

### Krok 4: Uruchomienie testów jednostkowych
Aby sprawdzić, czy funkcje czyszczące i walidujące działają w 100% poprawnie:
```powershell
py -m pytest scraper/tests -v
```
Powinnaś zobaczyć `18 passed in 0.08s` (wszystkie 18 testów zielonych).

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

## 5. Ściągawka na obronę projektu (Odpowiedzi na pytania prowadzącego)

1. **Pytanie: Dlaczego w katalogu głównym jest przycisk „Wczytaj więcej”, a nie 5 tradycyjnych podstron?**
   * **Odpowiedź:** W zadaniu na poziom 5.0 wprost jest wymagane: *„doładowywanie porcjami — przycisk «Wczytaj więcej» lub doładowanie przy przewijaniu”* oraz dla parsera: *„obsługa doładowywania aż do wyczerpania rekordów”*. Dynamiczny infinite scroll/button na poziomie 5.0 zastępuje statyczną paginację numeryczną z 4.0. Podstronami są natomiast dedykowane karty szczegółów produktów (`product.html?id=...`), których jest 420.
2. **Pytanie: Dlaczego zwykły parser `requests` nie zadziała na Waszym serwisie?**
   * **Odpowiedź:** Ponieważ w źródle HTML (`index.html`) jest 0 produktów (Ctrl+U pokazuje pusty kontener). Wszystkie dane są dociągane asynchronicznie przez JavaScript (`fetch`) ze sztucznym opóźnieniem. Scraper musi wykonywać JavaScript w silniku przeglądarki (Selenium).
3. **Pytanie: Jak zrealizowano obsługę błędu 429 i Retry-After?**
   * **Odpowiedź:** Serwer w `run_server.py` liczy żądania na sekundę. Przy przekroczeniu 10 RPS zwraca kod 429 z nagłówkiem `Retry-After: 2`. Scraper w `product_scraper.py` wykrywa tę odpowiedź i usypia wątek dokładnie na czas wskazany w nagłówku, po czym ponawia próbę (exponential backoff).
4. **Pytanie: Ile było duplikatów i jak zostały usunięte?**
   * **Odpowiedź:** W bazie wygenerowano 10 celowych duplikatów (rekordy o identycznej nazwie, specyfikacji i cenie, lecz innym technicznym ID). Moduł `deduplicator.py` porównuje krotki cech biznesowych i odrzucił dokładnie te 10 powtórzeń (z 420 zostało 410 unikalnych rekordów).
