from pprint import pprint

from browser import create_driver
from logging_config import configure_logging

from scraper.catalog_scraper import CatalogScraper
from scraper.product_scraper import ProductScraper


def main():

    logger = configure_logging()

    driver = create_driver(headless=False)

    try:

        catalog_scraper = CatalogScraper(
            driver=driver,
            logger=logger
        )

        catalog_scraper.open_catalog(
            "http://localhost:8000"
        )

        catalog_scraper.load_all_products()

        products = driver.find_elements(
            "css selector",
            ".produkt"
        )

        logger.info(
            f"Znaleziono {len(products)} produktów"
        )

        links = catalog_scraper.collect_product_links()

        logger.info(
            f"Zebrano {len(links)} linków"
        )

        product_scraper = ProductScraper(
            driver=driver,
            logger=logger
        )

        all_products = []

        # Celowo tylko 10 produktów na razie
        for url in links[:10]:

            product = product_scraper.extract_product(url)

            all_products.append(product)

            logger.info(
                f"Pobrano produkt ID={product['id']}"
            )

        logger.info(
            f"Pobrano łącznie: {len(all_products)}"
        )

        logger.info(
            f"Liczba kolumn: {len(all_products[0])}"
        )

        pprint(all_products[0])
    
    finally:
        driver.quit()


if __name__ == "__main__":
    main()