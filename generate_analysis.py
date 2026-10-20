import json
import re
import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Konfiguracja stylu wykresów
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

OUTPUT_IMG_DIR = Path(__file__).resolve().parent / "raport_wykresy"
OUTPUT_IMG_DIR.mkdir(parents=True, exist_ok=True)

DATA_PATH = Path(__file__).resolve().parent / "scraper" / "output" / "products_clean.xlsx"
RAW_DATA_PATH = Path(__file__).resolve().parent / "scraper" / "output" / "products_raw_all.json"
REPORT_PATH = Path(__file__).resolve().parent / "SPRAWOZDANIE.md"


def format_report_number(value):
    """Formatuje liczbę do polskiej tabeli raportowej z kropką dziesiętną."""
    return f"{float(value):,.2f}".replace(",", " ")


def render_markdown_table(headers, rows):
    """Buduje prostą tabelę Markdown bez opcjonalnych bibliotek formatowania."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(":---:" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def replace_report_block(report, block_name, content):
    """Zastępuje zawartość dokładnie jednego oznaczonego bloku w Markdownie."""
    start_marker = f"<!-- AUTO:{block_name}:START -->"
    end_marker = f"<!-- AUTO:{block_name}:END -->"
    pattern = re.compile(
        rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
        flags=re.DOTALL,
    )
    replacement = f"{start_marker}\n{content.rstrip()}\n{end_marker}"
    updated, replacements = pattern.subn(lambda _: replacement, report)
    if replacements != 1:
        raise ValueError(f"Oczekiwano jednego bloku AUTO:{block_name}, znaleziono {replacements}")
    return updated


def update_report(df, stats_summary, raw_record_count, raw_html_count, dom_count, log_text):
    """Aktualizuje generowane tabele i komentarze w sprawozdaniu Markdown."""
    report = REPORT_PATH.read_text(encoding="utf-8")
    unique_count = len(df)
    duplicate_count = raw_record_count - unique_count
    column_count = len(df.columns)

    report = replace_report_block(
        report,
        "QUALITY_SUMMARY",
        "\n".join([
            f"* **Pobrane rekordy z serwisu:** {raw_record_count}",
            f"* **Zidentyfikowane duplikaty:** **{duplicate_count}**.",
            f"* **Rekordy końcowe po deduplikacji:** **{unique_count}**",
            f"* **Liczba cech każdego rekordu:** {column_count}",
        ]),
    )

    missing_rows = []
    for column in df.columns:
        missing_count = int(df[column].isna().sum())
        missing_percent = missing_count / unique_count * 100 if unique_count else 0
        if missing_percent < 15:
            continue
        missing_rows.append([
            f"`{column}`",
            missing_count,
            f"{missing_percent:.2f}%",
            "✅ Spełniony",
        ])
    report = replace_report_block(
        report,
        "MISSING_TABLE",
        render_markdown_table(
            ["Nazwa kolumny", "Liczba braków (szt.)", "Udział procentowy (%)", "Spełnienie wymogu (min. 15%)"],
            missing_rows,
        ),
    )

    validation_matches = re.findall(
        r"Raport walidacji: sprawdzono (\d+) kolumn, odrzucono (\d+) wartości\.",
        log_text,
    )
    if validation_matches:
        checked_columns, rejected_values = validation_matches[-1]
        quality_note = (
            "Wszystkie braki zostały zapisane jako puste wartości (`None` w Pythonie / puste pole w CSV/Excelu). "
            f"Walidator sprawdził {checked_columns} kolumn i odrzucił {rejected_values} wartości w ostatnim przebiegu."
        )
    else:
        quality_note = (
            "Wszystkie braki są eksportowane jako puste wartości (`None` w Pythonie / puste pole w CSV/Excelu). "
            "Brak wpisu walidacji dla ostatniego przebiegu w pliku logu."
        )
    report = replace_report_block(report, "QUALITY_NOTE", quality_note)

    price = df["cena"].dropna()
    price_q1 = price.quantile(0.25)
    price_q3 = price.quantile(0.75)
    price_iqr = price_q3 - price_q1
    lower_bound = price_q1 - 1.5 * price_iqr
    upper_bound = price_q3 + 1.5 * price_iqr
    price_outliers = int(((price < lower_bound) | (price > upper_bound)).sum())
    iqr_text = (
        f"* **Analiza metodą rozstępu ćwiartkowego (IQR):** Granice dla ceny wynoszą "
        f"`[{format_report_number(lower_bound)} zł; {format_report_number(upper_bound)} zł]`. "
        f"Zakres cen: {format_report_number(price.min())}–{format_report_number(price.max())} zł; "
        f"liczba wartości odstających: {price_outliers}."
    )
    report = replace_report_block(report, "IQR", iqr_text)

    label_map = {
        "cena": "Cena (PLN)",
        "ocena": "Ocena (1–5)",
        "liczba_opinii": "Liczba opinii",
        "waga_kg": "Waga (kg)",
        "ram_gb": "Pamięć RAM (GB)",
        "dysk_ssd_gb": "Dysk SSD (GB)",
        "ekran_cale": "Ekran (cale)",
        "porty_usb": "Porty USB (szt.)",
        "pojemnosc_baterii_wh": "Bateria (Wh)",
        "gwarancja_miesiace": "Gwarancja (mies.)",
        "stan_magazynowy_sztuk": "Stan magazynowy (szt.)",
    }
    stats_rows = []
    for stats in stats_summary:
        mode = stats["Moda"]
        modes = mode if isinstance(mode, list) else [mode]
        stats_rows.append([
            f"**{label_map[stats['Cecha']]}**",
            format_report_number(stats["Średnia"]),
            format_report_number(stats["Mediana"]),
            "; ".join(format_report_number(value) for value in modes),
            format_report_number(stats["Min"]),
            format_report_number(stats["Q1 (25%)"]),
            format_report_number(stats["Q3 (75%)"]),
            format_report_number(stats["Max"]),
            format_report_number(stats["Odch. std."]),
        ])
    stats_table = "\n".join([
        "Tabela podsumowująca parametry liczbowe oczyszczonej bazy produktów. Jeśli kilka wartości ma tę samą maksymalną częstość, w kolumnie mody podano wszystkie:",
        render_markdown_table(
            ["Cecha", "Średnia", "Mediana", "Moda", "Min", "Q1 (25%)", "Q3 (75%)", "Max", "Odch. std."],
            stats_rows,
        ),
    ])
    report = replace_report_block(report, "STATS_TABLE", stats_table)

    mean_price = price.mean()
    median_price = price.median()
    report = replace_report_block(
        report,
        "CHART1_COMMENT",
        f"* **Komentarz:** Histogram przedstawia ceny w PLN w zakresie {format_report_number(price.min())}–{format_report_number(price.max())} zł. "
        f"Średnia wynosi {format_report_number(mean_price)} zł, mediana {format_report_number(median_price)} zł; "
        f"IQR wykrył {price_outliers} wartości odstających.",
    )

    category_medians = df.groupby("kategoria")["cena"].median().dropna()
    lowest_category = category_medians.idxmin()
    highest_category = category_medians.idxmax()
    report = replace_report_block(
        report,
        "CHART2_COMMENT",
        f"* **Komentarz:** Pudełka pokazują 50% środkowych cen, a wąsy ich zakres bez wartości odstających. "
        f"Mediany kategorii mieszczą się w przedziale {format_report_number(category_medians.min())}–"
        f"{format_report_number(category_medians.max())} zł. Najniższa mediana: {lowest_category}; "
        f"najwyższa mediana: {highest_category}.",
    )

    correlations = df[["cena", "ram_gb", "dysk_ssd_gb"]].corr()["cena"]
    report = replace_report_block(
        report,
        "CHART3_COMMENT",
        "\n".join([
            f"  * Współczynnik korelacji Pearsona między ceną w PLN a RAM wynosi **r ≈ {correlations['ram_gb']:.3f}**, "
            f"a między ceną a SSD **r ≈ {correlations['dysk_ssd_gb']:.3f}**.",
            "  * **Ocena merytoryczna:** Wartości bliskie zeru oznaczają słabą liniową zależność w tym zbiorze; nie należy interpretować ich jako silnej zależności rynkowej.",
        ]),
    )

    html_rows = [
        ["**Surowy HTML (bez JS / requests)**", raw_html_count, "Źródłowy `index.html` nie zawiera wyrenderowanych rekordów."],
        ["**Drzewo DOM w Selenium (po JS)**", dom_count if dom_count is not None else "brak danych", "Licznik pobrany z ostatniego przebiegu parsera."],
    ]
    report = replace_report_block(
        report,
        "HTML_COMPARISON",
        render_markdown_table(
            ["Metoda pobrania strony", "Liczba znalezionych rekordów produktów w HTML", "Komentarz i wnioski"],
            html_rows,
        ),
    )

    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Zaktualizowano sprawozdanie: {REPORT_PATH}")

df = pd.read_excel(DATA_PATH)
raw_products = json.loads(RAW_DATA_PATH.read_text(encoding="utf-8"))

print(f"--- 1. PODSTAWOWE DANE ---")
print(f"Liczba rekordów po deduplikacji: {len(df)}")
print(f"Liczba kolumn: {len(df.columns)}")

# 1. BRAKI DANYCH
missing = df.isnull().sum()
missing_pct = (missing / len(df)) * 100
missing_df = pd.DataFrame({"Braki (szt.)": missing, "Braki (%)": missing_pct.round(2)})
missing_df = missing_df[missing_df["Braki (szt.)"] > 0]
print("\n--- 2. BRAKI DANYCH W KOLUMNACH ---")
print(missing_df.to_string())

# 2. STATYSTYKI OPISOWE
num_cols = [
    "cena", "ocena", "liczba_opinii", "waga_kg", "ram_gb", "dysk_ssd_gb",
    "ekran_cale", "porty_usb", "pojemnosc_baterii_wh", "gwarancja_miesiace",
    "stan_magazynowy_sztuk"
]
stats_summary = []
for col in num_cols:
    s = df[col].dropna()
    modes = s.mode().tolist()
    mode_val = [round(value, 2) for value in modes] if len(modes) > 1 else (round(modes[0], 2) if modes else np.nan)
    stats_summary.append({
        "Cecha": col,
        "Średnia": round(s.mean(), 2),
        "Mediana": round(s.median(), 2),
        "Moda": mode_val,
        "Min": round(s.min(), 2),
        "Q1 (25%)": round(s.quantile(0.25), 2),
        "Q3 (75%)": round(s.quantile(0.75), 2),
        "Max": round(s.max(), 2),
        "Odch. std.": round(s.std(), 2)
    })
stats_df = pd.DataFrame(stats_summary)
print("\n--- 3. STATYSTYKI OPISOWE ---")
print(stats_df.to_string(index=False))

# 3. ANALIZA WARTOŚCI ODSTAJĄCYCH (IQR)
print("\n--- 4. WARTOŚCI ODSTAJĄCE (IQR) ---")
for col in ["cena", "ocena", "waga_kg"]:
    s = df[col].dropna()
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = s[(s < lower_bound) | (s > upper_bound)]
    print(f"{col}: granice [{round(lower_bound, 2)}, {round(upper_bound, 2)}], liczba outlierów: {len(outliers)}")

# 4. KORELACJE
print("\n--- 5. KORELACJA Z CENĄ ---")
corr = df[["cena", "ram_gb", "dysk_ssd_gb", "waga_kg", "ocena"]].corr()["cena"]
print(corr.round(3).to_string())

# --- GENEROWANIE WYKRESÓW ---

# Wykres 1: Histogram cen
plt.figure(figsize=(9, 5))
plt.hist(df['cena'], bins=25, color='#2563eb', edgecolor='white', alpha=0.85)
mean_cena = df['cena'].mean()
median_cena = df['cena'].median()
plt.axvline(mean_cena, color='#dc2626', linestyle='--', linewidth=2, label=f'Średnia: {mean_cena:.0f} zł')
plt.axvline(median_cena, color='#16a34a', linestyle='-', linewidth=2, label=f'Mediana: {median_cena:.0f} zł')
plt.title("Rozkład cen produktów w serwisie ElectroMarket", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Cena (PLN)", fontsize=11)
plt.ylabel("Liczba produktów", fontsize=11)
plt.legend(frameon=True, facecolor='white', framealpha=0.9)
plt.tight_layout()
chart1_path = OUTPUT_IMG_DIR / "1_histogram_cen.png"
plt.savefig(chart1_path, dpi=200)
plt.close()
print(f"Zapisano wykres 1: {chart1_path}")

# Wykres 2: Box-plot cen wg kategorii
plt.figure(figsize=(10, 6))
categories = df['kategoria'].unique()
data_by_cat = [df[df['kategoria'] == cat]['cena'].dropna() for cat in categories]
box = plt.boxplot(data_by_cat, tick_labels=[c.replace(' ', '\n') for c in categories], patch_artist=True, notch=True)
colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']
for patch, color in zip(box['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
for median in box['medians']:
    median.set(color='#111827', linewidth=2)
plt.title("Wykres pudełkowy (Box-plot) cen wg kategorii sprzętu", fontsize=14, fontweight='bold', pad=12)
plt.ylabel("Cena (PLN)", fontsize=11)
plt.tight_layout()
chart2_path = OUTPUT_IMG_DIR / "2_boxplot_cen_kategorie.png"
plt.savefig(chart2_path, dpi=200)
plt.close()
print(f"Zapisano wykres 2: {chart2_path}")

# Wykres 3: Korelacja Cena vs RAM z podziałem na kategorie
plt.figure(figsize=(9, 5))
scatter = plt.scatter(df['ram_gb'], df['cena'], c=df['dysk_ssd_gb'], cmap='viridis', s=60, alpha=0.75, edgecolors='none')
cbar = plt.colorbar(scatter)
cbar.set_label('Dysk SSD (GB)', fontsize=10)
# Linia trendu
z = np.polyfit(df['ram_gb'].dropna(), df['cena'].dropna(), 1)
p = np.poly1d(z)
x_vals = np.linspace(df['ram_gb'].min(), df['ram_gb'].max(), 50)
plt.plot(x_vals, p(x_vals), color='#ef4444', linestyle='--', linewidth=2, label='Linia trendu')
plt.title("Zależność ceny od pamięci RAM i dysku SSD", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Pamięć RAM (GB)", fontsize=11)
plt.ylabel("Cena (PLN)", fontsize=11)
plt.legend()
plt.tight_layout()
chart3_path = OUTPUT_IMG_DIR / "3_korelacja_cena_ram_ssd.png"
plt.savefig(chart3_path, dpi=200)
plt.close()
print(f"Zapisano wykres 3: {chart3_path}")

# 5. PORÓWNANIE SUROWEGO HTML vs DOM (WYMÓG 5.0)
try:
    with urllib.request.urlopen("http://localhost:8000/", timeout=2) as resp:
        raw_html = resp.read().decode('utf-8')
    raw_products_found = len(re.findall(r'class="[^"]*produkt[^"]*"', raw_html))
except Exception as e:
    raw_products_found = None

print(f"\n--- 6. PORÓWNANIE HTML vs DOM ---")
print(f"Liczba produktów w surowym HTML (GET /index.html): {raw_products_found if raw_products_found is not None else 'brak danych'}")
log_path = Path(__file__).resolve().parent / "scraper" / "logs" / "scraper.log"
log_text = ""
try:
    log_text = log_path.read_text(encoding="utf-8")
    dom_count_matches = re.findall(r"Liczba załadowanych produktów w DOM:\s*(\d+)", log_text)
    dom_products_found = int(dom_count_matches[-1]) if dom_count_matches else None
except OSError:
    dom_products_found = None

print(f"Liczba produktów w DOM po wykonaniu skryptów Selenium: {dom_products_found or 'brak danych w logu'}")

update_report(
    df,
    stats_summary,
    raw_record_count=len(raw_products),
    raw_html_count=raw_products_found if raw_products_found is not None else "brak danych",
    dom_count=dom_products_found,
    log_text=log_text,
)
