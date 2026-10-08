Żeby sprawdzić czy scraper działa podejmij następujące kroki:

1. Sprawdź czy masz zainstalowane odpowiednie pakiety, m.in. selenium. Jeżeli nie to zainstaluj, np:
    ```bash
    pip install selenium
    ```
2. Uruchom serwis: 
    ```bash 
    py run_server.py'
    ```
3. Sprwadź w przeglądarce czy serwis działa
4. Uruchom parser:
   ```bash
   cd scraper
   python main.py
   ```
5. Najpierw otworzy się Chrome, potem zobaczysz akcje w serwisie oraz logowanie na konsoli.
6. W katalogu logs powinien pojawić się plik z logami z tego procesu