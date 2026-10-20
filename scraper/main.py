import argparse
import os
import socket
import subprocess
import sys
import time
from urllib.parse import urlsplit
from datetime import datetime
from pathlib import Path
from pprint import pprint

# Konfiguracja UTF-8 dla konsoli Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8") # type: ignore
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8") # type: ignore

# Upewnienie się, że katalog scraper jest w sys.path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from browser import create_driver
from logging_config import configure_logging
from scraper.catalog_scraper import CatalogScraper
from scraper.product_scraper import ProductScraper
from processing.cleaners import clean_product_record
from processing.validators import ProductValidator
from processing.deduplicator import ProductDeduplicator
from export.exporter import DataExporter
from policy import inspect_site_policy


def ensure_server_running(url: str = "http://localhost:8000", logger = None):
    """Sprawdza lokalny serwer bez wysyłania żądania HTTP przed kontrolą polityki."""
    parsed_url = urlsplit(url)
    host = parsed_url.hostname or "localhost"
    port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
    is_local = host in {"localhost", "127.0.0.1", "::1"}

    if not is_local:
        return None

    try:
        with socket.create_connection((host, port), timeout=1.0):
            if logger:
                logger.info(f"Lokalny serwer {host}:{port} jest już aktywny")
            return None
    except Exception:
        pass

    server_script = ROOT_DIR / "run_server.py"
    if not server_script.exists():
        if logger:
            logger.warning(f"Nie znaleziono pliku serwera: {server_script}")
        return None

    if logger:
        logger.info(f"Uruchamianie serwera {server_script} w procesie potomnym...")

    proc = subprocess.Popen(
        [sys.executable, str(server_script)],
        cwd=str(ROOT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Sprawdzamy gotowość połączeniem TCP, bez pobierania treści serwisu.
    for _ in range(10):
        time.sleep(0.5)
        try:
            with socket.create_connection((host, port), timeout=1.0):
                if logger:
                    logger.info("Serwer pomyślnie wystartował!")
                return proc
        except Exception:
            continue

    if logger:
        logger.warning("Nie udało się potwierdzić startu serwera w wyznaczonym czasie.")
    return proc


def parse_args():
    """Parsuje adres katalogu, limit rekordów i wybór trybu przeglądarki."""
    parser = argparse.ArgumentParser(description="WebParser - Scraper ElectroMarket (Poziom 5.0)")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Adres URL katalogu głównego (domyślnie: http://localhost:8000)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Opcjonalny limit pobieranych produktów (domyślnie: None - pobiera wszystkie)"
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Uruchom przeglądarkę w widocznym oknie (domyślnie: headless dla szybkości)"
    )
    return parser.parse_args()


def main():
    """Uruchamia kontrolę polityki, scrapowanie, walidację, deduplikację i eksport."""
    args = parse_args()
    logger = configure_logging()

    start_time = time.time()
    logger.info("==========================================================")
    logger.info("Rozpoczynanie procesu parsowania serwisu ElectroMarket (5.0)")
    logger.info("==========================================================")

    # 1. Sprawdzenie / uruchomienie serwera
    server_proc = ensure_server_running(args.url, logger=logger)

    # 2. Odczyt robots.txt i regulaminu przed uruchomieniem przeglądarki.
    site_policy = inspect_site_policy(args.url, logger=logger)

    headless_mode = not args.visible
    logger.info(f"Inicjalizacja Chrome WebDriver (headless={headless_mode})...")
    driver = create_driver(headless=headless_mode)

    try:
        # 3. Katalog i doładowywanie rekordów
        catalog_scraper = CatalogScraper(driver=driver, logger=logger, policy=site_policy)
        catalog_scraper.open_catalog(args.url)

        logger.info("Doładowywanie wszystkich produktów przyciskiem 'Wczytaj więcej'...")
        catalog_scraper.load_all_products()

        catalog_items = catalog_scraper.collect_catalog_items()
        total_found = len(catalog_items)
        logger.info(f"Liczba załadowanych produktów w DOM: {total_found}")

        if args.limit and args.limit > 0:
            catalog_items = catalog_items[:args.limit]
            logger.info(f"Zastosowano limit do pierwszych {args.limit} produktów")

        # 3. Zbieranie szczegółów każdego produktu
        product_scraper = ProductScraper(driver=driver, logger=logger, max_retries=3, policy=site_policy)
        raw_products = []

        total_to_scrape = len(catalog_items)
        logger.info(f"Rozpoczynanie pobierania szczegółów {total_to_scrape} produktów...")

        for idx, item in enumerate(catalog_items, start=1):
            url = item.get("href")
            if not url:
                continue

            try:
                product_data = product_scraper.extract_product(url, catalog_meta=item)
                raw_products.append(product_data)

                # Logowanie postępu co 20 produktów lub dla pierwszych kilku
                if idx <= 5 or idx % 25 == 0 or idx == total_to_scrape:
                    pct = round((idx / total_to_scrape) * 100, 1)
                    logger.info(f"[{idx}/{total_to_scrape}] ({pct}%) Pobrano produkt ID={product_data.get('id')}: {product_data.get('nazwa')}")

            except Exception as e:
                logger.error(f"Pominięto produkt pod adresem {url} z powodu błędu: {e}")

        logger.info(f"Pomyślnie pobrano surowe dane dla {len(raw_products)} produktów.")

        # 4. Czyszczenie danych (Cleaners)
        logger.info("Czyszczenie i standaryzacja formatów (ceny, daty, brakujące wartości)...")
        cleaned_products = [clean_product_record(p) for p in raw_products]

        # 5. Walidacja typów i kontrola jakości (Validators)
        logger.info("Walidacja typów kolumn i sprawdzanie ograniczeń biznesowych...")
        validator = ProductValidator()
        validated_products, val_report = validator.validate(cleaned_products)

        logger.info(f"Raport walidacji: sprawdzono {val_report['columns_checked']} kolumn, odrzucono {val_report['total_rejected_values']} wartości.")
        if val_report['invalid_counts_by_column']:
            logger.info(f"Odrzucone wartości według kolumn: {val_report['invalid_counts_by_column']}")

        # 6. Deduplikacja (Deduplicator)
        logger.info("Deduplikacja rekordów...")
        deduplicator = ProductDeduplicator()
        unique_products, dedup_report = deduplicator.deduplicate(validated_products)

        logger.info(f"Deduplikacja zakończona: {dedup_report['total_before']} -> {dedup_report['unique_after']} (usunięto duplikatów: {dedup_report['duplicates_removed']})")

        # 7. Eksport do plików (CSV + JSON)
        logger.info("Eksport danych do formatów CSV i JSON...")
        exporter = DataExporter()
        
        # Zapis wersji oczyszczonej i zdeduplikowanej
        export_clean = exporter.export_all("products_clean", unique_products)
        logger.info(f"Zapisano czyste dane: {export_clean['csv_path']} ({export_clean['csv_size_kb']} KB)")
        logger.info(f"Zapisano czyste JSON: {export_clean['json_path']} ({export_clean['json_size_kb']} KB)")

        # Zapis wersji surowej (przed deduplikacją - do celów sprawozdania i porównania)
        exporter.export_all("products_raw_all", cleaned_products)

        elapsed = round(time.time() - start_time, 2)
        logger.info("==========================================================")
        logger.info("PODSUMOWANIE PROCESU:")
        logger.info(f"Czas działania: {elapsed} s")
        logger.info(f"Wszystkich pobranych rekordów: {len(raw_products)}")
        logger.info(f"Zidentyfikowanych duplikatów: {dedup_report['duplicates_removed']}")
        logger.info(f"Unikalnych rekordów końcowych: {len(unique_products)}")
        logger.info(f"Liczba kolumn w rekordzie: {len(unique_products[0]) if unique_products else 0}")
        logger.info(f"Pliki wyjściowe: {export_clean['csv_path']}, {export_clean['json_path']}")
        logger.info("==========================================================")

    finally:
        driver.quit()
        logger.info("Przeglądarka została zamknięta.")


if __name__ == "__main__":
    main()