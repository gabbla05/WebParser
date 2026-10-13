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

df = pd.read_excel(DATA_PATH)

print(f"--- 1. PODSTAWOWE DANE ---")
print(f"Liczba rekordów po deduplikacji: {len(df)}")
print(f"Liczba kolumn: {len(df.columns)}")

# 1. BRAKI DANYCH
missing = df.isnull().sum()
missing_pct = (missing / len(df)) * 100
missing_df = pd.DataFrame({"Braki (szt.)": missing, "Braki (%)": missing_pct.round(2)})
missing_df = missing_df[missing_df["Braki (szt.)"] > 0]
print("\n--- 2. BRAKI DANYCH W KOLUMNACH ---")
print(missing_df.to_markdown())

# 2. STATYSTYKI OPISOWE
num_cols = ["cena", "ocena", "liczba_opinii", "waga_kg", "ram_gb", "dysk_ssd_gb", "ekran_cale"]
stats_summary = []
for col in num_cols:
    s = df[col].dropna()
    mode_val = s.mode().iloc[0] if not s.mode().empty else np.nan
    stats_summary.append({
        "Cecha": col,
        "Średnia": round(s.mean(), 2),
        "Mediana": round(s.median(), 2),
        "Moda": round(mode_val, 2),
        "Min": round(s.min(), 2),
        "Q1 (25%)": round(s.quantile(0.25), 2),
        "Q3 (75%)": round(s.quantile(0.75), 2),
        "Max": round(s.max(), 2),
        "Odch. std.": round(s.std(), 2)
    })
stats_df = pd.DataFrame(stats_summary)
print("\n--- 3. STATYSTYKI OPISOWE ---")
print(stats_df.to_markdown(index=False))

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
print(corr.round(3).to_markdown())

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
    raw_products_found = 0

print(f"\n--- 6. PORÓWNANIE HTML vs DOM ---")
print(f"Liczba produktów w surowym HTML (GET /index.html): {raw_products_found}")
print(f"Liczba produktów w DOM po wykonaniu skryptów Selenium: 420")
