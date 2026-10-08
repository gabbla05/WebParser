from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ProductScraper:

    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    def open_product(self, url: str) -> None:

        self.driver.get(url)

        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located(
                (By.ID, "product-details-container")
            )
        )

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