import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException


class ProductScraper:

    def __init__(self, driver, logger, max_retries: int = 3):
        self.driver = driver
        self.logger = logger
        self.max_retries = max_retries

        # Katalogi na diagnostykę błędów (rozszerzenie 5.0)
        self.logs_dir = Path(__file__).resolve().parent.parent / "logs"
        self.screenshots_dir = self.logs_dir / "screenshots"
        self.dumps_dir = self.logs_dir / "dumps"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.dumps_dir.mkdir(parents=True, exist_ok=True)

    def _save_error_diagnostics(self, url: str, attempt: int, error_msg: str):
        """Zapisuje zrzut ekranu oraz źródło HTML przy błędzie (rozszerzenie 5.0)."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_slug = re.sub(r"[^a-zA-Z0-9]", "_", url)[-25:]
        file_prefix = f"err_{timestamp}_att{attempt}_{url_slug}"

        try:
            screenshot_path = self.screenshots_dir / f"{file_prefix}.png"
            self.driver.save_screenshot(str(screenshot_path))
            
            dump_path = self.dumps_dir / f"{file_prefix}.html"
            dump_path.write_text(self.driver.page_source, encoding="utf-8")

            self.logger.warning(
                f"[DIAGNOSTYKA] Zapisano zrzut błędu: {screenshot_path.name} oraz {dump_path.name}"
            )
        except Exception as diag_err:
            self.logger.error(f"Nie udało się zapisać zrzutu diagnostycznego: {diag_err}")

    def _check_for_429(self) -> Optional[float]:
        """
        Sprawdza czy strona zwróciła odpowiedź 429 Too Many Requests
        i odczytuje zalecany czas oczekiwania z nagłówka lub tekstu.
        """
        try:
            page_text = self.driver.page_source
            if "429 Too Many Requests" in page_text:
                match = re.search(r"Retry-After:\s*(\d+)", page_text)
                if match:
                    return float(match.group(1))
                return 2.0
        except Exception:
            pass
        return None

    def open_product(self, url: str) -> None:
        """Nawiguje do podstrony i czeka na wyrenderowanie dynamicznego kontenera."""
        self.driver.get(url)

        # Sprawdzenie 429
        wait_429 = self._check_for_429()
        if wait_429:
            raise RuntimeError(f"Otrzymano HTTP 429 (Retry-After: {wait_429}s)")

        WebDriverWait(self.driver, 15).until(
            lambda d: (
                element
                if (element := d.find_element(By.ID, "product-details-container")).text.strip()
                else False
            )
        )

    def expand_specification(self) -> None:
        """Rozwija element <details> ze specyfikacją techniczną (utrudnienie 5.0)."""
        details = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "tech-specs-toggle"))
        )

        if not details.get_attribute("open"):
            summary = details.find_element(By.TAG_NAME, "summary")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", summary)
            summary.click()

    def get_specification(self) -> Dict[str, str]:
        """Pobiera wszystkie cechy ze specyfikacji technicznej z uwzględnieniem losowej kolejności."""
        specs = {}
        rows = self.driver.find_elements(By.CSS_SELECTOR, ".spec-item")

        for row in rows:
            key = row.get_attribute("data-spec-key")
            try:
                value = row.find_element(By.CSS_SELECTOR, ".spec-value").text.strip()
            except Exception:
                value = ""
            if key:
                specs[key] = value

        return specs

    def get_general_data(self) -> Dict[str, Any]:
        """Pobiera dane nagłówkowe i atrybuty z kontenera produktu."""
        container = self.driver.find_element(By.ID, "product-details-container")

        return {
            "id": container.get_attribute("data-id"),
            "waluta": container.get_attribute("data-currency"),
            "cena_bazowa_pln": container.get_attribute("data-base-price"),
            "nazwa": self.driver.find_element(By.CSS_SELECTOR, ".nazwa").text.strip(),
            "kategoria": self.driver.find_element(By.CSS_SELECTOR, ".kategoria").text.strip(),
            "producent": self.driver.find_element(By.CSS_SELECTOR, ".producent").text.strip(),
            "ocena": self.driver.find_element(By.CSS_SELECTOR, ".ocena").text.strip(),
            "liczba_opinii": self.driver.find_element(By.CSS_SELECTOR, ".ocena").text.strip(),
            "data_dodania": self.driver.find_element(By.CSS_SELECTOR, ".data-dodania").text.strip(),
            "gwarancja": self.driver.find_element(By.CSS_SELECTOR, ".gwarancja").text.strip(),
            "cena": self.driver.find_element(By.CSS_SELECTOR, ".cena").text.strip(),
            "dostepnosc": self.driver.find_element(By.CSS_SELECTOR, ".dostepnosc").text.strip()
        }

    def extract_product(self, url: str, catalog_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Pobiera i łączy dane produktu z obsługą ponawiania z opóźnieniem wykładniczym (1s, 2s, 4s...)
        oraz diagnostyką błędów.
        """
        last_exception = None
        backoff_delay = 1.0

        for attempt in range(1, self.max_retries + 1):
            try:
                self.open_product(url)
                general_data = self.get_general_data()
                self.expand_specification()
                specs = self.get_specification()

                product = {
                    **general_data,
                    **specs
                }

                # Połączenie z danymi zebranymi z katalogu (np. atrybuty data-*)
                if catalog_meta:
                    if "data_vat" in catalog_meta:
                        product["stawka_vat"] = catalog_meta["data_vat"]
                    if "data_energy_class" in catalog_meta:
                        product["klasa_energetyczna"] = catalog_meta["data_energy_class"]
                    if "data_stock_count" in catalog_meta:
                        product["stan_magazynowy_sztuk"] = catalog_meta["data_stock_count"]

                return product

            except Exception as e:
                last_exception = e
                self._save_error_diagnostics(url, attempt, str(e))

                # Jeśli to kod 429 z Retry-After
                if "429" in str(e):
                    sleep_time = 2.0
                    self.logger.warning(
                        f"Wykryto kod 429 dla {url}. Czekam {sleep_time}s zgodnie z Retry-After..."
                    )
                else:
                    sleep_time = backoff_delay
                    self.logger.warning(
                        f"Błąd pobierania {url} ({e}). Ponawianie za {sleep_time}s (próba {attempt}/{self.max_retries})..."
                    )
                    backoff_delay *= 2

                if attempt < self.max_retries:
                    time.sleep(sleep_time)

        self.logger.error(
            f"Nie udało się pobrać produktu {url} po {self.max_retries} próbach: {last_exception}"
        )
        raise last_exception