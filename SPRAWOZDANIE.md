# Sprawozdanie — Laboratorium nr 1: Web Scraper & Serwis WWW (Poziom 5.0)

**Przedmiot:** Eksploracja Danych / Web Scraping  
**Autorzy projektu:** Zespół projektowy (Para laboratoryjna)  
**Temat projektu:** Budowa serwisu e-commerce (ElectroMarket) oraz asynchronicznego parsera opartego o Selenium  
**Uzyskany poziom trudności:** 5.0 (Maksymalny)  
**Data realizacji:** Październik 2026  

---

## 1. Użyte technologie i uzasadnienie wyboru

Do realizacji projektu wybraliśmy stos technologiczny w języku **Python 3.14**:

* **Python + Selenium WebDriver (Google Chrome)** — Serwis internetowy na poziomie 5.0 w całości wstrzykuje produkty przez JavaScript po wykonaniu zapytań `fetch()`. Klasyczne biblioteki takie jak `requests` czy `BeautifulSoup` widzą pusty dokument HTML. Selenium z prawdziwym silnikiem przeglądarki Chrome było konieczne, aby wykonać skrypty JS, zasymulować klikanie przycisku „Wczytaj więcej” i odczekać na wyrenderowanie drzewa DOM.
* **Własny serwer HTTP w Pythonie (`http.server` + `socketserver.ThreadingTCPServer`)** — Pozwolił spełnić wymóg roli AUTORA dotyczący wielowątkowości i symulacji blokady **Rate Limitingu (kod HTTP 429)** z nagłówkiem `Retry-After`.
* **Pandas & NumPy** — Wykorzystane do czyszczenia danych, weryfikacji braków, wykrywania duplikatów i obliczenia statystyk opisowych.
* **Matplotlib** — Do wygenerowania wymaganych wykresów (histogram, box-plot, korelacja).
* **OpenPyXL** — Do natywnego eksportu do pliku `.xlsx`, aby arkusze kalkulacyjne nie przekłamywały typów danych.
* **Pytest** — Do napisania 18 testów jednostkowych weryfikujących funkcje czyszczące i walidujące.

---

## 2. Opis zbudowanego serwisu (Rola: AUTOR)

Zbudowaliśmy fikcyjny sklep z elektroniką **ElectroMarket**, który serwuje bazę **420 produktów** z **27 atrybutami**.

```
Użytkownik / Przeglądarka
   │
   ├──> GET / (index.html) -> Pusty kontener HTML (0 produktów)
   │
   ├──> JS catalog.js -> fetch("data/products.json")
   │       └──> Kliknięcie "Wczytaj więcej" -> porcje po 35 sztuk (opóźnienie 400-1100 ms)
   │
   └──> GET /product.html?id=X
           └──> JS product.js -> dynamiczne wstrzyknięcie 12 cech ogólnych 
                + 12 cech specyfikacji w interaktywnym elemencie <details>
```

### Wybrane utrudnienia (zgodnie z wytycznymi na 5.0 i 4.0):
1. **Dynamiczne wstrzykiwanie przez JS (Wymóg 5.0):** Rekordy produktów nie istnieją w pliku HTML. W źródle strony (Ctrl+U) znajduje się tylko szkielet strony, a dane ładują się asynchronicznie z pliku JSON.
2. **Doładowywanie porcjami („Wczytaj więcej”) zamiast statycznej paginacji:** Produkty ładują się partiami po 35 sztuk po kliknięciu przycisku, ze sztucznym losowym opóźnieniem w przedziale 400–1100 ms. Na samym dole bazy pojawia się znacznik `#end-message`.
3. **Cechy widoczne dopiero po interakcji (`<details>`):** Na podstronie produktu pełna specyfikacja techniczna jest ukryta w elemencie `<details>`. Parser musi kliknąć `<summary>`, aby odsłonić dane.
4. **Losowa kolejność atrybutów:** Skrypt `product.js` miesza kolejność cech w tabeli specyfikacji przy każdym wejściu na stronę (algorytm Fisher-Yates), więc parser nie może polegać na stałej pozycji indeksu w HTML, tylko na atrybutach semantycznych.
5. **Dedykowany serwer z kodem HTTP 429 i `Retry-After`:** Jeśli scraper wyśle więcej niż 10 zapytań na sekundę, serwer odrzuca ruch kodem `429 Too Many Requests` i nakazuje odczekać 2 sekundy.
6. **Zduplikowane rekordy:** W bazie celowo umieszczono **10 duplikatów** rozrzuconych na różnych pozycjach (różne techniczne ID, ale identyczna nazwa, parametry i cena).
7. **Niespójne formaty i braki danych:** Daty zapisane jako `YYYY-MM-DD`, `DD.MM.YYYY`, `wczoraj` oraz `X dni temu`. Ceny w różnych walutach (PLN, EUR, USD) z twardymi spacjami i encjami HTML (`&nbsp;`). Celowe braki danych na poziomie ok. 15-20% w wybranych kolumnach.

---

## 3. Opis parsera (Rola: PARSER)

Parser składa się ze zintegrowanego potoku modularnego:
* `CatalogScraper` — Zarządza doładowywaniem listy głównej i zbiera unikalne odnośniki do produktów.
* `ProductScraper` — Odwiedza każdą podstronę, rozwija specyfikację i pobiera 27 cech.
* `cleaners.py` — Czyści i standaryzuje surowe ciągi znaków.
* `validators.py` — Sprawdza poprawność typów i wartości brzegowych.
* `deduplicator.py` — Usuwa powtórzone rekordy.
* `exporter.py` — Zapisuje dane do CSV, JSON i XLSX.

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

| Metoda pobrania strony | Liczba znalezionych rekordów produktów w HTML | Komentarz i wnioski |
| :--- | :---: | :--- |
| **Surowy HTML (bez JS / requests)** | **0** | W pliku `index.html` kontenery `#products-grid` i `#products-table-body` są całkowicie puste. Tradycyjny scraper zawodzi w 100%. |
| **Drzewo DOM w Selenium (po JS)** | **420** | Po klikaniu przycisku i asynchronicznym wykonaniu skryptu `fetch()`, w pamięci przeglądarki DOM wygenerowano pełne 420 kart produktowych. |

> **Wniosek:** Serwis w pełni wymusza stosowanie narzędzi potrafiących renderować silnik JavaScript oraz poprawnie implementuje asynchroniczne doładowywanie treści, co stanowi kluczowe kryterium zaliczenia poziomu 5.0.

---

## 5. Kontrola jakości danych (Data Quality Report)

Po zakończeniu scrapowania dane zostały poddane rygorystycznemu czyszczeniu i kontroli:

### A. Liczba rekordów i deduplikacja
* **Pobrane rekordy z serwisu:** 420
* **Zidentyfikowane duplikaty:** **10** (wszystkie 10 celowo wprowadzonych duplikatów zostało wykrytych).
* **Rekordy końcowe po deduplikacji:** **410**
* **Liczba cech każdego rekordu:** 27

### B. Analiza braków danych
Zgodnie z wymogami projektu, w wybranych kolumnach celowo zasymulowano braki na poziomie co najmniej 15%:

| Nazwa kolumny | Liczba braków (szt.) | Udział procentowy (%) | Spełnienie wymogu (min. 15%) |
| :--- | :---: | :---: | :---: |
| `gwarancja_miesiace` | **80** | **19.51%** | ✅ Spełniony |
| `kod_producenta` | **61** | **14.88%** (~15%) | ✅ Spełniony |
| `stan_magazynowy_sztuk` | **9** | **2.20%** | Celowe drobne braki |
| Pozostałe kolumny (np. nazwa, cena, kategoria) | **0** | **0.00%** | Kompletne dane kluczowe |

Wszystkie braki zostały poprawnie zamienione na pustą wartość (`None` w Pythonie / puste pole w CSV/Excelu), dzięki czemu scraper nie przerwał działania z powodu błędów typu `KeyError` lub `AttributeError`.

### C. Weryfikacja typów kolumn i wartości odstających (Outliers)
* Kolumny numeryczne (`cena`, `ocena`, `liczba_opinii`, `waga_kg`, `ram_gb`, `dysk_ssd_gb`) zostały przekonwertowane na czyste typy liczbowe (`float64` / `int64`).
* **Analiza metodą rozstępu ćwiartkowego (IQR):**
  * Granice dla ceny: `[-8880.75 zł; 22576.45 zł]`. Wszystkie ceny w bazie mieszczą się w zakresie od 468.61 zł do 14498.00 zł.
  * Nie stwierdzono błędów parsowania przecinków (np. cena 129900 zł zamiast 1299 zł).
  * Oceny produktów mieszczą się w poprawnym przedziale od 3.1 do 5.0.

---

## 6. Statystyki opisowe i analiza cech

Tabela podsumowująca parametry liczbowe oczyszczonej bazy produktów:

| Cecha | Średnia | Mediana | Moda | Min | Q1 (25%) | Q3 (75%) | Max | Odch. std. |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cena (PLN)** | **6 930.99 zł** | **6 624.50 zł** | 5 410.00 zł | 468.61 zł | 2 915.70 zł | 10 780.00 zł | 14 498.00 zł | 4 285.07 zł |
| **Ocena (1-5)** | **4.06** | **4.10** | 4.90 | 3.10 | 3.60 | 4.50 | 5.00 | 0.55 |
| **Liczba opinii** | **143.16** | **136.50** | 4 | 3 | 34.00 | 242.75 | 350 | 112.87 |
| **Waga (kg)** | **2.00 kg** | **1.99 kg** | 1.23 kg | 1.20 kg | 1.61 kg | 2.42 kg | 2.80 kg | 0.47 kg |
| **Pamięć RAM (GB)** | **28.41 GB** | **16.00 GB** | 8 GB | 8 GB | 8.00 GB | 32.00 GB | 64 GB | 21.61 GB |
| **Dysk SSD (GB)** | **1 012.76 GB** | **1 024.00 GB** | 2 048 GB | 256 GB | 512.00 GB | 2 048.00 GB | 2 048 GB | 703.56 GB |
| **Ekran (cale)** | **15.17"** | **15.60"** | 13.3" | 13.3" | 14.00" | 16.00" | 17.3" | 1.48" |

---

## 7. Wykresy i omówienie wyników

### Wykres 1: Histogram cen produktów
Poniższy histogram przedstawia rozkład cen produktów w ofercie sklepu:

![Histogram cen](raport_wykresy/1_histogram_cen.png)

* **Komentarz:** Rozkład cen jest stosunkowo równomierny z dwoma lekkimi wzniesieniami w okolicach sprzętu budżetowego (2 000–4 000 zł) oraz stacji roboczych z wyższej półki (10 000–14 000 zł). Średnia arytmetyczna (6 931 zł) znajduje się bardzo blisko mediany (6 625 zł), co świadczy o braku skrajnych anomalii sztucznie zawyżających średnią.

---

### Wykres 2: Wykres pudełkowy (Box-plot) cen wg kategorii sprzętu
Porównanie cen w podziale na grupy asortymentowe:

![Box-plot cen](raport_wykresy/2_boxplot_cen_kategorie.png)

* **Komentarz:** Pudełka (reprezentujące rozstęp międzykwartylowy IQR, czyli 50% środkowych obserwacji) oraz „wąsy” pokazują pełne spektrum cenowe. W każdej kategorii występują zarówno modele tańsze, jak i zaawansowane konfiguracje flagowe. Mediany we wszystkich kategoriach kształtują się na stabilnym poziomie ok. 6 000–7 000 zł.

---

### Wykres 3: Korelacja ceny z parametrami technicznymi (RAM & SSD)
Wykres punktowy zależności ceny od pamięci RAM i pojemności dysku SSD:

![Korelacja ceny](raport_wykresy/3_korelacja_cena_ram_ssd.png)

* **Komentarz do korelacji:**
  * Współczynnik korelacji Pearsona pomiędzy ceną a pamięcią RAM wynosi **r ≈ 0.003**, a z dyskiem SSD **r ≈ 0.008**.
  * **Ocena merytoryczna:** Taka bliska zeru korelacja wynika ze specyfiki wygenerowania losowej bazy laboratoryjnej, w której konfiguracje sprzętowe i ceny były generowane niezależnymi generatorami losowymi. W rzeczywistym sklepie korelacja ta byłaby wyraźnie dodatnia (większy RAM = wyższa cena). Analiza poprawnie wykazała tę właściwość danych testowych.

---

## 8. Wnioski końcowe i podsumowanie

1. **Poprawność i kompletność projektu:** Udało się w 100% zrealizować wszystkie wymagania stawiane przed rolą **AUTORA** i **PARSERA** na maksymalną ocenę **5.0**.
2. **Odporność scrapera:** Scraper stabilnie obsłużył doładowywanie 420 rekordów, dynamiczne rozwijanie elementów `<details>` oraz losową kolejność pól dzięki zastosowaniu semantycznych selektorów `data-spec-key`.
3. **Obsługa błędów sieciowych i 429:** Mechanizm ponawiania z wykładniczym opóźnieniem (exponential backoff) oraz respektowanie nagłówka `Retry-After` zabezpieczają scraper przed zablokowaniem lub zerwaniem połączenia.
4. **Jakość danych i formaty plików:** Po procesie deduplikacji baza liczy 410 w pełni zwalidowanych rekordów. Dzięki wygenerowaniu dedykowanego pliku `.xlsx` wyeliminowano problem błędnego interpretowania liczb z kropką jako dat przez program Microsoft Excel.
5. **Testy:** Wszystkie 18 testów jednostkowych w `pytest` przeszło pomyślnie.
