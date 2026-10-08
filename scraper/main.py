from browser import create_driver
from logging_config import configure_logging

from scraper.catalog_scraper import CatalogScraper
from scraper.product_scraper import ProductScraper

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

        links = scraper.collect_product_links()

        product_scraper = ProductScraper(
            driver=driver,
            logger=logger
        )

        first_product = links[0]

        logger.info(
            f"Test produktu: {first_product}"
        )

        product_scraper.open_product(
            first_product
        )

        product_scraper.expand_specification()

        specs = product_scraper.get_specification()

        logger.info(
            f"Znaleziono {len(specs)} parametrów"
        )

        for key, value in specs.items():

            logger.info(
                f"{key} = {value}"
            )

        logger.info(
            f"Unikalnych linków: {len(links)}"
        )

        logger.info(
            f"Przykładowy link: {links[0]}"
        )

    finally:
        driver.quit()


if __name__ == "__main__":
    main()