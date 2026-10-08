from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class CatalogScraper:

    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    def open_catalog(self, url: str) -> None:

        self.driver.get(url)

        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(
                (By.ID, "btn-load-more")
            )
        )

        self.logger.info("Katalog został załadowany")

    def load_all_products(self) -> None:

        while True:

            try:
                end_message = self.driver.find_element(
                    By.ID,
                    "end-message"
                )

                if end_message.is_displayed():

                    self.logger.info(
                        "Załadowano wszystkie rekordy"
                    )

                    break

            except Exception:
                pass

            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.ID, "btn-load-more")
                )
            )

            current_count = len(
                self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".produkt"
                )
            )

            button.click()

            WebDriverWait(self.driver, 15).until(
                lambda d: len(
                    d.find_elements(
                        By.CSS_SELECTOR,
                        ".produkt"
                    )
                ) > current_count
            )