from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ProductScraper:

    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    def open_product(self, url: str) -> None:
        self.driver.get(url)

        # Poczekaj, aż kontener będzie zawierał tekst
        container = WebDriverWait(self.driver, 15).until(
            lambda d: (
                element
                if (element := d.find_element(
                    By.ID, "product-details-container"
                )).text.strip()
                else False
            )
        )

        # Zapisz HTML kontenera
        with open(
            "product_rendered.html",
            "w",
            encoding="utf-8"
        ) as f:
            f.write(container.get_attribute("innerHTML"))

    def expand_specification(self) -> None:

        details = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located(
                (By.ID, "tech-specs-toggle")
            )
        )

        if not details.get_attribute("open"):

            summary = details.find_element(
                By.TAG_NAME,
                "summary"
            )

            summary.click()

    def get_specification(self) -> dict:

        specs = {}

        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            ".spec-item"
        )

        for row in rows:

            key = row.get_attribute(
                "data-spec-key"
            )

            value = row.find_element(
                By.CSS_SELECTOR,
                ".spec-value"
            ).text.strip()

            specs[key] = value

        return specs


    def get_general_data(self) -> dict:

        container = self.driver.find_element(
            By.ID,
            "product-details-container"
        )

        return {
            "id": container.get_attribute("data-id"),
            "waluta": container.get_attribute("data-currency"),
            "cena_bazowa_pln": container.get_attribute(
                "data-base-price"
            ),

            "nazwa": self.driver.find_element(
                By.CSS_SELECTOR,
                ".nazwa"
            ).text,

            "kategoria": self.driver.find_element(
                By.CSS_SELECTOR,
                ".kategoria"
            ).text,

            "producent": self.driver.find_element(
                By.CSS_SELECTOR,
                ".producent"
            ).text,

            "ocena": self.driver.find_element(
                By.CSS_SELECTOR,
                ".ocena"
            ).text,

            "data_dodania": self.driver.find_element(
                By.CSS_SELECTOR,
                ".data-dodania"
            ).text,

            "gwarancja": self.driver.find_element(
                By.CSS_SELECTOR,
                ".gwarancja"
            ).text,

            "cena": self.driver.find_element(
                By.CSS_SELECTOR,
                ".cena"
            ).text,

            "dostepnosc": self.driver.find_element(
                By.CSS_SELECTOR,
                ".dostepnosc"
            ).text
        }

    def extract_product(self, url: str) -> dict:

        self.open_product(url)

        general_data = self.get_general_data()

        self.expand_specification()

        specs = self.get_specification()

        product = {
            **general_data,
            **specs
        }

        return product