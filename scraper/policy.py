import re
import time
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit


class _TextExtractor(HTMLParser):
    def __init__(self):
        """Inicjalizuje kolektor tekstu z elementów HTML."""
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        """Zachowuje tekstowy fragment parsowanej strony regulaminu."""
        self.parts.append(data)


class SitePolicy:
    def __init__(self, robots: urllib.robotparser.RobotFileParser, min_interval: float):
        """Przechowuje reguły robots.txt i minimalny odstęp między nawigacjami."""
        self.robots = robots
        self.min_interval = min_interval
        self.last_request_at = time.monotonic()

    def before_request(self, url: str) -> None:
        """Blokuje zabronione URL-e i czeka do upłynięcia wymaganego odstępu."""
        if not self.robots.can_fetch("*", url):
            raise PermissionError(f"robots.txt zabrania pobierania: {url}")

        remaining = self.min_interval - (time.monotonic() - self.last_request_at)
        if remaining > 0:
            time.sleep(remaining)
        self.last_request_at = time.monotonic()

        ''' Ta funkcja sprawdza, czy URL jest dozwolony, i odczekuje wymagany czas przed nawigacją. 
            Wartość wynika z regulaminu i robots.txt; tutaj to 1 sekunda, bo regulamin
            wymaga 0,5 s, a robots.txt 1 s (regulamin.html:27, robots.txt:3). 
            Ograniczenie obejmuje wejścia Selenium na strony katalogu i produktów, nie kontroluje 
            osobno każdego żądania zasobu wysłanego przez samą przeglądarkę.'''

    def mark_request_complete(self) -> None:
        """Zapamiętuje zakończenie nawigacji jako początek kolejnego odstępu."""
        self.last_request_at = time.monotonic()


def _read_text(url: str) -> str:
    """Pobiera tekst strony z identyfikatorem klienta parsera."""
    request = urllib.request.Request(url, headers={"User-Agent": "ElectroMarketLabParser/1.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8", errors="replace")


def inspect_site_policy(catalog_url: str, logger=None) -> SitePolicy:
    """Sprawdza robots.txt i regulamin, po czym zwraca egzekwowalną politykę dostępu."""
    parsed = urlsplit(catalog_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Niepoprawny adres katalogu: {catalog_url}")

    origin = f"{parsed.scheme}://{parsed.netloc}/"
    robots_url = urljoin(origin, "robots.txt")
    terms_url = urljoin(origin, "regulamin.html")

    robots = urllib.robotparser.RobotFileParser()
    robots.set_url(robots_url)
    robots.parse(_read_text(robots_url).splitlines())

    if not robots.can_fetch("*", catalog_url):
        raise PermissionError(f"robots.txt zabrania pobierania: {catalog_url}")
    if not robots.can_fetch("*", terms_url):
        raise PermissionError(f"robots.txt zabrania odczytu regulaminu: {terms_url}")

    crawl_delay = float(robots.crawl_delay("*") or 0)
    if crawl_delay > 0:
        time.sleep(crawl_delay)

    terms_html = _read_text(terms_url)
    text_extractor = _TextExtractor()
    text_extractor.feed(terms_html)
    terms_text = " ".join(" ".join(text_extractor.parts).split()).casefold()

    permission = "zezwala się na automatyczne odczytywanie danych katalogowych wyłącznie w celach dydaktycznych"
    if permission not in terms_text:
        raise PermissionError("Regulamin nie potwierdza zgody na scraping w celach dydaktycznych")

    delay_match = re.search(r"minimum\s+(\d+(?:[.,]\d+)?)\s+sekund(?:y|ę|a)", terms_text)
    if not delay_match:
        raise RuntimeError("Nie udało się odczytać wymaganego odstępu z regulaminu")

    terms_delay = float(delay_match.group(1).replace(",", "."))
    min_interval = max(crawl_delay, terms_delay)
    if logger:
        logger.info(
            f"Polityka dostępu zaakceptowana: robots.txt dozwala katalog, "
            f"regulamin wymaga co najmniej {min_interval:g}s między żądaniami"
        )

    return SitePolicy(robots, min_interval)