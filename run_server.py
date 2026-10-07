"""
Dedykowany serwer HTTP w Pythonie dla serwisu e-commerce (Rola AUTOR - Poziom 5.0).
Spełnia utrudnienie 5.0:
"prosty serwer (Python lub Node) zamiast http.server, zwracający kod 429 po przekroczeniu limitu żądań, wraz z nagłówkiem Retry-After"

Uruchomienie:
    python run_server.py
    python run_server.py --port 8000 --max-rps 12
    python run_server.py --no-rate-limit
"""

import argparse
import collections
import http.server
import socketserver
import sys
import time
from pathlib import Path

# Słownik śledzący czasy żądań dla każdego adresu IP
IP_REQUEST_TIMESTAMPS = collections.defaultdict(list)

class RateLimitedHandler(http.server.SimpleHTTPRequestHandler):
    """Niestandardowy handler HTTP z mechanizmem Rate Limitingu zwracającym HTTP 429."""

    def __init__(self, *args, rate_limit_enabled=True, max_rps=10, retry_after=2, **kwargs):
        self.rate_limit_enabled = rate_limit_enabled
        self.max_rps = max_rps
        self.retry_after = retry_after
        super().__init__(*args, **kwargs)

    def is_rate_limited(self) -> bool:
        if not self.rate_limit_enabled:
            return False

        client_ip = self.client_address[0]
        now = time.time()
        timestamps = IP_REQUEST_TIMESTAMPS[client_ip]

        # Usuwamy znaczniki starsze niż 1 sekunda
        IP_REQUEST_TIMESTAMPS[client_ip] = [t for t in timestamps if now - t < 1.0]
        timestamps = IP_REQUEST_TIMESTAMPS[client_ip]

        if len(timestamps) >= self.max_rps:
            return True

        timestamps.append(now)
        return False

    def do_GET(self):
        if self.is_rate_limited():
            self.send_response(429)
            self.send_header("Retry-After", str(self.retry_after))
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            msg = f"429 Too Many Requests: Przekroczono limit {self.max_rps} żądań/sek. Odczekaj {self.retry_after}s zgodnie z Retry-After.\n"
            self.wfile.write(msg.encode("utf-8"))
            print(f"⚠️ [RATE LIMIT] Zwrócono HTTP 429 dla {self.client_address[0]} (Retry-After: {self.retry_after}s)")
            return

        return super().do_GET()


def run(port=8000, max_rps=10, retry_after=2, rate_limit_enabled=True):
    site_dir = Path(__file__).resolve().parent / "site"
    if not site_dir.exists():
        print(f"BŁĄD: Katalog serwisu {site_dir} nie istnieje!")
        sys.exit(1)

    def handler_factory(*args, **kwargs):
        return RateLimitedHandler(
            *args,
            directory=str(site_dir),
            rate_limit_enabled=rate_limit_enabled,
            max_rps=max_rps,
            retry_after=retry_after,
            **kwargs
        )

    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(("", port), handler_factory) as httpd:
            print("=" * 70)
            print("🚀 Niestandardowy Serwer HTTP ElectroMarket (Zgodny z wymogami 5.0)")
            print(f"👉 Adres serwisu: http://localhost:{port}/")
            print(f"📁 Serwowane pliki z: {site_dir}")
            if rate_limit_enabled:
                print(f"🛡️ Rate Limiting: AKTYWNY (max {max_rps} żądań/sekundę, Retry-After: {retry_after}s)")
            else:
                print("🛡️ Rate Limiting: WYŁĄCZONY")
            print("Naciśnij Ctrl+C, aby zatrzymać serwer.")
            print("=" * 70)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymano serwer.")
    except OSError as e:
        print(f"\nBŁĄD: Port {port} jest zajęty ({e}). Wybierz inny port, np. --port 8080")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uruchom dedykowany serwer HTTP na ocenę 5.0.")
    parser.add_argument("--port", type=int, default=8000, help="Numer portu (domyślnie 8000)")
    parser.add_argument("--max-rps", type=int, default=10, help="Maksymalna liczba żądań/sekundę przed kodem 429 (domyślnie 10)")
    parser.add_argument("--retry-after", type=int, default=2, help="Wartość nagłówka Retry-After w sekundach (domyślnie 2)")
    parser.add_argument("--no-rate-limit", action="store_true", help="Wyłącza zwracanie kodu 429")
    args = parser.parse_args()

    run(
        port=args.port,
        max_rps=args.max_rps,
        retry_after=args.retry_after,
        rate_limit_enabled=not args.no_rate_limit
    )
