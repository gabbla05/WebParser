import time
from urllib.parse import urljoin
from typing import List, Dict, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException


class CatalogScraper:

    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    def open_catalog(self, url: str) -> None:
        self.driver.get(url)
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.ID, "btn-load-more"))
        )
        self.logger.info("Katalog został załadowany")

    def load_all_products(self) -> None:
        """
        Obsługuje doładowywanie rekordów aż do wyczerpania (wymóg 5.0).
        Zawiera ponawianie z opóźnieniem wykładniczym w razie problemów z kliknięciem.
        """
        retry_delay = 1.0
        max_retries = 3
        consecutive_errors = 0

        while True:
            # Sprawdzenie czy pojawił się komunikat końca
            try:
                end_message = self.driver.find_element(By.ID, "end-message")
                if end_message.is_displayed():
                    self.logger.info("Załadowano wszystkie rekordy (wykryto end-message)")
                    break
            except Exception:
                pass

            # Próba kliknięcia z mechanizmem retry i backoff
            try:
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btn-load-more"))
                )

                current_count = len(self.driver.find_elements(By.CSS_SELECTOR, ".produkt"))

                # Przewiń do przycisku i kliknij
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                button.click()

                # Czekamy na pojawienie się nowej partii
                WebDriverWait(self.driver, 15).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, ".produkt")) > current_count
                )
                consecutive_errors = 0
                retry_delay = 1.0

            except (TimeoutException, WebDriverException) as e:
                consecutive_errors += 1
                if consecutive_errors > max_retries:
                    self.logger.warning(
                        f"Osiągnięto limit prób kliknięcia 'Wczytaj więcej'. Kończenie ładowania: {e}"
                    )
                    break

                self.logger.warning(
                    f"Problem z doładowaniem partii. Ponawianie za {retry_delay}s (próba {consecutive_errors}/{max_retries})..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2

    def collect_catalog_items(self) -> List[Dict[str, Any]]:
        """
        Zbiera elementy z katalogu wraz z atrybutami ukrytymi w data-*
        (data-vat, data-energy-class, data-stock-count - utrudnienie 4.0).
        """
        items = []
        product_elements = self.driver.find_elements(By.CSS_SELECTOR, ".produkt")

        for el in product_elements:
            try:
                link_el = el.find_element(By.CSS_SELECTOR, ".odnosnik")
                href = link_el.get_attribute("href")
            except Exception:
                href = None

            item_data = {
                "href": href,
                "data_id": el.get_attribute("data-id"),
                "data_vat": el.get_attribute("data-vat"),
                "data_energy_class": el.get_attribute("data-energy-class"),
                "data_stock_count": el.get_attribute("data-stock-count")
            }
            items.append(item_data)

        self.logger.info(f"Zebrano {len(items)} elementów z listy katalogu")
        return items

    def collect_product_links(self) -> List[str]:
        """Zbiera same odnośniki do podstron szczegółów."""
        items = self.collect_catalog_items()
        links = [it["href"] for it in items if it["href"]]
        self.logger.info(f"Wszystkich linków: {len(links)}")
        self.logger.info(f"Po usunięciu duplikatów: {len(set(links))}")
        return links