from browser import create_driver
from logging_config import configure_logging

from scraper.catalog_scraper import CatalogScraper


def main():

    logger = configure_logging()

    driver = create_driver(headless=False)

    try:

        scraper = CatalogScraper(
            driver=driver,
            logger=logger
        )

        scraper.open_catalog(
            "http://localhost:8000"
        )

        scraper.load_all_products()

        products = driver.find_elements(
            "css selector",
            ".produkt"
        )

        logger.info(
            f"Znaleziono {len(products)} produktów"
        )

    finally:
        driver.quit()


if __name__ == "__main__":
    main()