import logging
from pathlib import Path


def configure_logging() -> logging.Logger:
    """
    Konfiguracja logowania do pliku oraz konsoli.
    Logi zapisywane są w katalogu logs w scraperze.
    """
    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "scraper.log"

    # Reset handlerów jeśli logger już istniał
    logger = logging.getLogger("scraper")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger