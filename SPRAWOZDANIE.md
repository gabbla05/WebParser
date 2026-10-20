# Sprawozdanie - Laboratorium nr 1: Web Scraper oraz Serwis WWW

**Przedmiot:** Przetwarzanie Języka Naturalnego 

**Prowadzący:** mgr inż. Łukasz Gaża 

**Autorzy projektu:** Gabriela Błaut, Michał Brzeziński 

**Temat projektu:** Budowa serwisu e-commerce (ElectroMarket) oraz asynchronicznego parsera opartego o Selenium  

**Uzyskany poziom trudności:** 5.0 

**Data realizacji:** 20.10.2026  

---

## 1. Użyte technologie i uzasadnienie wyboru

Projekt uruchomiono w środowisku **Python 3.12.3**:

* **Python + Selenium WebDriver (Google Chrome)** - Serwis internetowy na poziomie 5.0 w całości wstrzykuje produkty przez JavaScript po wykonaniu zapytań `fetch()`. Wykorzystanie Selenium z prawdziwym silnikiem przeglądarki Chrome było konieczne, aby wykonać skrypty JS, zasymulować klikanie przycisku „Wczytaj więcej” i odczekać na wyrenderowanie drzewa DOM.
* **Wielowątkowy serwer Python (`socketserver.ThreadingTCPServer`) z własnym limiterem** - Odpowiedź po przekroczeniu limitu zawiera kod HTTP 429, nagłówek `Retry-After` oraz tę samą wartość w treści odpowiedzi, którą może odczytać Selenium.
* **Pandas & NumPy** - Wykorzystane do czyszczenia danych, weryfikacji braków, wykrywania duplikatów i obliczenia statystyk opisowych. Cena analizowana jest w PLN, a kwota i waluta źródłowa pozostają zachowane w osobnych kolumnach.
* **Matplotlib** - Do wygenerowania wymaganych wykresów (histogram, box-plot, korelacja).
* **OpenPyXL** - Do natywnego eksportu do pliku `.xlsx`, aby arkusze kalkulacyjne nie przekłamywały typów danych.
* **Pytest** - Do napisania i uruchomienia 22 testów jednostkowych weryfikujących czyszczenie, walidację, deduplikację i obsługę odpowiedzi 429.

---

## 2. Opis zbudowanego serwisu (Rola: AUTOR)

W ramach tego zadania laboratoryjnego zbudowaliśmy fikcyjny sklep z elektroniką **ElectroMarket**, który serwuje bazę **420 produktów**. Każdy rekord źródłowy JSON ma 28 pól; po ekstrakcji i normalizacji powstaje 27 kolumn, w tym cena w PLN, kwota źródłowa i waluta.

```
Użytkownik / Przeglądarka
   │
   ├──> GET / (index.html) -> Pusty kontener HTML (0 produktów)
   │
   ├──> JS catalog.js -> fetch("data/products.json")
   │       └──> Kliknięcie "Wczytaj więcej" -> porcje po 35 sztuk (opóźnienie 400-1100 ms)
   │
   └──> GET /product.html?id=X
           └──> JS product.js -> dynamiczne wstrzyknięcie cech ogólnych oraz cech specyfikacji w interaktywnym elemencie <details>
```

### Wymagania i wybrane utrudnienia zgodnie z wytycznymi:
1. **Dynamiczne wstrzykiwanie przez JS (Wymóg 5.0):** Rekordy produktów nie istnieją w pliku HTML. W źródle strony (Ctrl+U) znajduje się tylko szkielet strony, a dane ładują się asynchronicznie z pliku JSON.
2. **Doładowywanie porcjami („Wczytaj więcej”) zamiast statycznej paginacji (Wymóg 5.0):** Produkty ładują się partiami po 35 sztuk po kliknięciu przycisku, ze sztucznym losowym opóźnieniem w przedziale 400–1100 ms. Na samym dole bazy pojawia się znacznik `#end-message`.
3. **Cechy widoczne dopiero po interakcji (`<details>`) (Utrudnienie 5.0):** Na podstronie produktu pełna specyfikacja techniczna jest ukryta w elemencie `<details>`. Parser musi kliknąć `<summary>`, aby odsłonić dane.
4. **Losowa kolejność atrybutów (Utrudnienie 5.0):** Skrypt `product.js` miesza kolejność cech w tabeli specyfikacji przy każdym wejściu na stronę (algorytm Fisher-Yates), więc parser nie może polegać na stałej pozycji indeksu w HTML, tylko na atrybutach semantycznych.
5. **Kontrola zasad dostępu (Utrudnienie 5.0):** Przed uruchomieniem przeglądarki parser pobiera `robots.txt` i regulamin, blokuje ścieżki niedozwolone przez robots.txt oraz respektuje większy z wymaganych odstępów: `Crawl-delay` lub minimum z regulaminu.
6. **Podstrony szczegółów (Wymaganie 4.0):** Każdy rekord ma własną stronę z minimum 8 dodatkowymi atrybutami
7. **Zduplikowane rekordy (Utrudnienia 4.0):** W bazie celowo umieszczono **10 duplikatów** z różnymi technicznymi ID, ale identycznymi danymi biznesowymi.
8. **Niespójne formaty i braki danych (Utrudnienia 4.0):** Daty zapisane jako `YYYY-MM-DD`, `DD.MM.YYYY`, `wczoraj` oraz `X dni temu`. Ceny w różnych walutach (PLN, EUR, USD) z twardymi spacjami i encjami HTML (`&nbsp;`). Braki w `liczba_opinii` i `gwarancja_miesiace` przekraczają 15%.

---

## 3. Opis parsera (Rola: PARSER)

Parser składa się ze zintegrowanego potoku modularnego:
* `CatalogScraper` - Zarządza doładowywaniem listy głównej i zbiera unikalne odnośniki do produktów.
* `ProductScraper` - Odwiedza każdą podstronę, rozwija specyfikację i pobiera cechy.
* `cleaners.py` - Czyści i standaryzuje surowe ciągi znaków.
* `validators.py` - Sprawdza poprawność typów i wartości brzegowych.
* `deduplicator.py` - Usuwa powtórzone rekordy.
* `exporter.py` - Zapisuje dane do CSV, JSON i XLSX.

### Zastosowane selektory i ocena ich odporności

| Element / Dana | Użyty selektor | Odporność na zmiany wyglądu (CSS/Layout) | Uzasadnienie |
| :--- | :--- | :---: | :--- |
| Przycisk doładowania | `By.ID, "btn-load-more"` | **Bardzo wysoka** | Identyfikator techniczny ID; zmiana stylów CSS, kolorów czy położenia przycisku nie psuje selektora. |
| Komunikat końca | `By.ID, "end-message"` | **Bardzo wysoka** | Prosty znacznik stanu ID. |
| Rozwijanie cech | `By.ID, "tech-specs-toggle"` | **Bardzo wysoka** | Celowy ID elementu interaktywnego. |
| Cechy specyfikacji | `.spec-item[data-spec-key]` | **Bardzo wysoka** | **Najbardziej odporny selektor w projekcie**. Zamiast brać np. `div:nth-child(3)`, czytamy klucz z `data-spec-key="ram_gb"`. Nawet jeśli kolejność cech jest losowa lub zmieni się układ tabeli, pobieramy właściwy parametr. |
| Nazwa, Kategoria, Cena | Klasy semantyczne: `.nazwa`, `.kategoria`, `.cena` | **Wysoka** | Klasy semantyczne przetrwają zmianę fontów, kolorów i układu siatki (Grid/Flexbox). Przetrwałyby dopóki programista nie zmieni nazewnictwa klas w szablonie. |
| Karty produktów | `By.CSS_SELECTOR, ".produkt"` | **Wysoka** | Zastosowano uniwersalną klasę wspólną zarówno dla kart `article`, jak i wierszy tabeli `tr`. |

---

## 4. Porównanie surowego HTML z drzewem DOM (Wymóg 5.0)

W ramach weryfikacji wymogu poziomu 5.0 przeprowadziliśmy test porównawczy:
1. Pobranie strony głównej standardowym zapytaniem HTTP bez przeglądarki (`urllib.request` / `requests.get`).
2. Pobranie strony głównej po pełnym wykonaniu skryptów w przeglądarce Selenium.

<!-- AUTO:HTML_COMPARISON:START -->
| Metoda pobrania strony | Liczba znalezionych rekordów produktów w HTML | Komentarz i wnioski |
| :---: | :---: | :---: |
| **Surowy HTML (bez JS / requests)** | 0 | Źródłowy `index.html` nie zawiera wyrenderowanych rekordów. |
| **Drzewo DOM w Selenium (po JS)** | 420 | Licznik pobrany z ostatniego przebiegu parsera. |
<!-- AUTO:HTML_COMPARISON:END -->

> **Wniosek:** Serwis w pełni wymusza stosowanie narzędzi potrafiących renderować silnik JavaScript oraz poprawnie implementuje asynchroniczne doładowywanie treści, co stanowi kluczowe kryterium zaliczenia poziomu 5.0.

---

## 5. Kontrola jakości danych (Data Quality Report)

Po zakończeniu scrapowania dane zostały poddane rygorystycznemu czyszczeniu i kontroli:
Statystyki i wykresy są liczone z `scraper/output/products_clean.xlsx`: to 410 rekordów po czyszczeniu i deduplikacji. Analizowana kolumna `cena` jest znormalizowana do PLN; nie liczymy średniej z prezentacyjnych kwot EUR/USD w surowym `products.json`.

### A. Liczba rekordów i deduplikacja
<!-- AUTO:QUALITY_SUMMARY:START -->
* **Pobrane rekordy z serwisu:** 420
* **Zidentyfikowane duplikaty:** **10**.
* **Rekordy końcowe po deduplikacji:** **410**
* **Liczba cech każdego rekordu:** 27
<!-- AUTO:QUALITY_SUMMARY:END -->

### B. Analiza braków danych
Zgodnie z wymogami projektu, w wybranych kolumnach celowo zasymulowano braki na poziomie co najmniej 15%:

<!-- AUTO:MISSING_TABLE:START -->
| Nazwa kolumny | Liczba braków (szt.) | Udział procentowy (%) | Spełnienie wymogu (min. 15%) |
| :---: | :---: | :---: | :---: |
| `liczba_opinii` | 79 | 19.27% | ✅ Spełniony |
| `gwarancja_miesiace` | 80 | 19.51% | ✅ Spełniony |
<!-- AUTO:MISSING_TABLE:END -->

<!-- AUTO:QUALITY_NOTE:START -->
Wszystkie braki zostały zapisane jako puste wartości (`None` w Pythonie / puste pole w CSV/Excelu). Walidator sprawdził 27 kolumn i odrzucił 0 wartości w ostatnim przebiegu.
<!-- AUTO:QUALITY_NOTE:END -->

### C. Weryfikacja typów kolumn i wartości odstających
* Kolumny numeryczne (`cena` w PLN, `cena_zrodlowa`, `ocena`, `liczba_opinii`, `waga_kg`, `ram_gb`, `dysk_ssd_gb`) zostały przekonwertowane na typy liczbowe (`float64` / `int64`). Cena bazowa PLN ze strony jest źródłem wartości do analizy; w jej braku kwota tekstowa jest przeliczana według kursów użytych przez generator (EUR: 4,30 PLN; USD: 3,95 PLN). Kwota źródłowa i waluta pozostają zachowane osobno.
<!-- AUTO:IQR:START -->
* Wartości odstające: Zakres cen: 3 115.00–29 062.00 zł; liczba wartości odstających: 0.
<!-- AUTO:IQR:END -->

---

## 6. Statystyki opisowe i analiza cech

<!-- AUTO:STATS_TABLE:START -->
Tabela podsumowująca parametry liczbowe oczyszczonej bazy produktów. Jeśli kilka wartości ma tę samą maksymalną częstość, w kolumnie mody podano wszystkie:
| Cecha | Średnia | Mediana | Moda | Min | Q1 (25%) | Q3 (75%) | Max | Odch. std. |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cena (PLN)** | 10 602.60 | 7 950.00 | 6 585.00; 7 924.00 | 3 115.00 | 5 735.50 | 15 685.25 | 29 062.00 | 6 130.12 |
| **Ocena (1–5)** | 4.05 | 4.10 | 4.10 | 3.10 | 3.60 | 4.50 | 5.00 | 0.55 |
| **Liczba opinii** | 174.50 | 176.00 | 83.00; 182.00; 186.00; 192.00; 331.00 | 2.00 | 87.00 | 259.50 | 350.00 | 99.08 |
| **Waga (kg)** | 1.68 | 1.46 | 0.18 | 0.17 | 1.02 | 2.67 | 3.78 | 1.08 |
| **Pamięć RAM (GB)** | 27.13 | 16.00 | 16.00 | 8.00 | 16.00 | 32.00 | 64.00 | 18.09 |
| **Dysk SSD (GB)** | 935.34 | 1 024.00 | 1 024.00 | 256.00 | 512.00 | 1 024.00 | 2 048.00 | 590.05 |
| **Ekran (cale)** | 14.81 | 14.00 | 13.30 | 13.30 | 13.30 | 16.00 | 17.30 | 1.48 |
| **Porty USB (szt.)** | 3.50 | 4.00 | 4.00 | 2.00 | 2.00 | 4.00 | 5.00 | 1.13 |
| **Bateria (Wh)** | 72.35 | 75.00 | 52.00 | 52.00 | 52.00 | 80.00 | 99.00 | 15.28 |
| **Gwarancja (mies.)** | 25.45 | 24.00 | 36.00 | 12.00 | 12.00 | 36.00 | 36.00 | 10.27 |
| **Stan magazynowy (szt.)** | 21.70 | 21.00 | 4.00 | 0.00 | 9.00 | 33.00 | 45.00 | 13.40 |
<!-- AUTO:STATS_TABLE:END -->

---

## 7. Wykresy i omówienie wyników

### Wykres 1: Histogram cen produktów
Poniższy histogram przedstawia rozkład cen produktów w ofercie sklepu:

![Histogram cen](1_histogram_cen.png)

<!-- AUTO:CHART1_COMMENT:START -->
* **Komentarz:** Histogram przedstawia ceny w PLN w zakresie 3 115.00–29 062.00 zł. Średnia wynosi 10 602.60 zł, mediana 7 950.00 zł;
<!-- AUTO:CHART1_COMMENT:END -->

---

### Wykres 2: Wykres pudełkowy (Box-plot) cen wg kategorii sprzętu
Porównanie cen w podziale na grupy asortymentowe:

![Box-plot cen](2_boxplot_cen_kategorie.png)

<!-- AUTO:CHART2_COMMENT:START -->
* **Komentarz:** Pudełka pokazują 50% środkowych cen, a wąsy ich zakres bez wartości odstających. Mediany kategorii mieszczą się w przedziale 5 224.00–19 341.00 zł. Najniższa mediana: TABLETY 2W1; najwyższa mediana: STACJE ROBOCZE.
<!-- AUTO:CHART2_COMMENT:END -->

---

### Wykres 3: Korelacja ceny z parametrami technicznymi (RAM & SSD)
Wykres punktowy zależności ceny od pamięci RAM i pojemności dysku SSD:

![Korelacja ceny](3_korelacja_cena_ram_ssd.png)

* **Komentarz do korelacji:**
<!-- AUTO:CHART3_COMMENT:START -->
  * Współczynnik korelacji Pearsona między ceną w PLN a RAM wynosi **r ≈ 0.642**, a między ceną a SSD **r ≈ 0.626**.
  * **Ocena merytoryczna:** Otrzymane wyniki oznaczają, że między ceną komputera w PLN a pojemnością pamięci RAM oraz dysku SSD istnieje umiarkowanie silna, dodatnia korelacja liniowa. Współczynniki r ≈ 0.642 (dla RAM) oraz r ≈ 0.626 (dla SSD) wskazują, że wyższym wartościom jednej zmiennej zazwyczaj towarzyszą wyższe wartości drugiej
<!-- AUTO:CHART3_COMMENT:END -->

---

## 8. Wnioski końcowe i podsumowanie

1. **Wynik przebiegu:** Parser pobrał 420 produktów, odrzucił 0 wartości walidacyjnych, usunął 10 duplikatów i wyeksportował 410 rekordów w 27 kolumnach.
2. **Odporność scrapera:** Scraper stabilnie obsłużył doładowywanie 420 rekordów, dynamiczne rozwijanie elementów `<details>` oraz losową kolejność pól dzięki zastosowaniu semantycznych selektorów `data-spec-key`.
3. **Jakość danych i formaty plików:** Po procesie deduplikacji baza liczy 410 w pełni zwalidowanych rekordów. Dzięki wygenerowaniu dedykowanego pliku `.xlsx` wyeliminowano problem błędnego interpretowania liczb z kropką jako dat przez program Microsoft Excel.
4. **Testy:** Wszystkie 22 testy jednostkowe w `pytest` przeszły pomyślnie.


## 8. Wnioski końcowe i podsumowanie

1. **Realizacja założeń projektu**

   Główny cel laboratorium został osiągnięty. Opracowano serwis internetowy generujący zawartość dynamicznie przy użyciu JavaScript oraz parser zdolny do pozyskiwania danych z tak przygotowanego źródła. Rozwiązanie spełnia wymagania poziomu 5.0, ponieważ dane nie są dostępne bez wcześniejszego wykonania skryptów po stronie przeglądarki.

2. **Skuteczność procesu scrapowania**

   Parser poprawnie pobrał wszystkie 420 rekordów dostępnych w serwisie. Zastosowane selektory oparte na identyfikatorach i atrybutach semantycznych okazały się odporne na zmiany układu strony oraz losową kolejność elementów specyfikacji technicznej. Dzięki temu możliwe było stabilne pozyskiwanie danych z wielu podstron produktów.

3. **Jakość i przetwarzanie danych**

   Zebrane dane zostały poddane procesowi czyszczenia, walidacji oraz deduplikacji. Wykryto i usunięto 10 celowo przygotowanych duplikatów, uzyskując końcowy zbiór 410 rekordów. Przeprowadzona normalizacja umożliwiła analizę danych pochodzących z różnych formatów zapisu dat oraz różnych walut przy zachowaniu spójnych wyników statystycznych.

4. **Analiza pozyskanych informacji**

   Wykonane statystyki oraz wizualizacje pozwoliły zaobserwować znaczne zróżnicowanie cen produktów. Analiza korelacji wykazała dodatnią zależność pomiędzy ceną urządzenia a parametrami technicznymi, takimi jak ilość pamięci RAM i pojemność dysku SSD. Wynik ten jest zgodny z oczekiwaniami i potwierdza poprawność wygenerowanego zbioru danych.

5. **Niezawodność rozwiązania**

   Implementacja mechanizmów walidacji danych, obsługi ograniczeń serwera oraz zestawu testów jednostkowych zwiększyła niezawodność całego rozwiązania. Wszystkie przygotowane testy zakończyły się powodzeniem, co potwierdziło poprawne działanie kluczowych elementów systemu.

6. **Podsumowanie praktyczne**

   Projekt pozwolił przećwiczyć pełny proces pozyskiwania danych ze źródeł internetowych – od zaprojektowania własnego serwisu WWW, przez implementację parsera i mechanizmów czyszczenia danych, aż po analizę statystyczną i przygotowanie raportu końcowego. Efektem pracy jest kompletny system umożliwiający automatyczne gromadzenie i przetwarzanie danych ze zbudowanego serwisu.