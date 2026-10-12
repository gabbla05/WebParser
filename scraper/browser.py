from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def create_driver(headless: bool = False) -> webdriver.Chrome:
    """
    Tworzy i konfiguruje instancję Chrome WebDriver.
    """

    options = Options()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-allow-origins=*")
    options.page_load_strategy = "eager"

    return webdriver.Chrome(options=options)