import csv
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from openpyxl.utils import get_column_letter

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import openpyxl
    from openpyxl.utils import get_column_letter
except ImportError:
    openpyxl = None


class DataExporter:
    """
    Moduł eksportu oczyszczonych i zwalidowanych danych.
    Spełnia wymóg: eksport do wielu formatów (CSV, XLSX, JSON),
    jeden wiersz = jeden rekord, jedna kolumna = jeden atrybut,
    poprawne polskie znaki (UTF-8) oraz natywna obsługa formatów Excela.
    """

    COLUMN_ORDER = [
        "id", "nazwa", "kategoria", "producent", "cena", "cena_zrodlowa", "waluta",
        "dostepnosc", "ocena", "liczba_opinii", "data_dodania", "gwarancja_miesiace",
        "procesor", "ram_gb", "dysk_ssd_gb", "karta_graficzna", "ekran_cale",
        "rozdzielczosc", "system_operacyjny", "waga_kg", "kolor", "kod_producenta",
        "porty_usb", "pojemnosc_baterii_wh", "stawka_vat", "klasa_energetyczna",
        "stan_magazynowy_sztuk"
    ]

    def __init__(self, output_dir: Optional[str] = None):
        """Przygotowuje katalog docelowy eksportu."""
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).resolve().parent.parent / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_fieldnames(self, products: List[Dict[str, Any]]) -> List[str]:
        """Łączy znane kolumny w ustalonej kolejności z dodatkowymi polami."""
        all_keys = set()
        for p in products:
            all_keys.update(p.keys())

        fieldnames = [col for col in self.COLUMN_ORDER if col in all_keys]
        for extra in sorted(all_keys - set(fieldnames)):
            fieldnames.append(extra)
        return fieldnames

    def export_to_csv(self, filename: str, products: List[Dict[str, Any]], decimal_comma: bool = False) -> str:
        """
        Zapisuje dane do pliku CSV z kodowaniem UTF-8-sig.
        Jeśli decimal_comma=True, liczby zmiennoprzecinkowe są formatowane z przecinkiem (np. 2,1 zamiast 2.1),
        dzięki czemu polski Excel nie myli ich z datami.
        """
        filepath = self.output_dir / filename
        if not products:
            filepath.write_text("", encoding="utf-8")
            return str(filepath)

        fieldnames = self._get_fieldnames(products)

        try:
            with open(filepath, "w", encoding="utf-8-sig", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";", extrasaction="ignore")
                writer.writeheader()
                for prod in products:
                    row = dict(prod)
                    if decimal_comma:
                        for k, v in row.items():
                            if isinstance(v, float):
                                row[k] = str(v).replace(".", ",")
                    writer.writerow(row)
            return str(filepath)
        except PermissionError:
            # Plik jest zablokowany (np. otwarty w programie Excel przez użytkownika)
            alt_path = self.output_dir / f"zaktualizowany_{filename}"
            with open(alt_path, "w", encoding="utf-8-sig", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";", extrasaction="ignore")
                writer.writeheader()
                for prod in products:
                    row = dict(prod)
                    if decimal_comma:
                        for k, v in row.items():
                            if isinstance(v, float):
                                row[k] = str(v).replace(".", ",")
                    writer.writerow(row)
            return str(alt_path)

    def export_to_json(self, filename: str, products: List[Dict[str, Any]]) -> str:
        """
        Zapisuje dane do pliku JSON w formacie UTF-8 z wcięciami.
        """
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as jsonfile:
            json.dump(products, jsonfile, ensure_ascii=False, indent=2)

        return str(filepath)

    def export_to_excel(self, filename: str, products: List[Dict[str, Any]]) -> Optional[str]:
        """
        Zapisuje dane do natywnego pliku Excela (.xlsx) z dopasowaną szerokością kolumn
        i natywnymi typami numerycznymi (Excel nie zamienia liczb na daty, brak '########').
        """
        if pd is None or openpyxl is None:
            return None

        filepath = self.output_dir / filename
        fieldnames = self._get_fieldnames(products)

        df = pd.DataFrame(products)
        # Uporządkowanie kolumn
        cols = [c for c in fieldnames if c in df.columns]
        df = df[cols]

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Produkty")
            worksheet = writer.sheets["Produkty"]

            # Automatyczne dopasowanie szerokości kolumn (zapobiega ######## dla dat)
            for col_idx, col_name in enumerate(cols, start=1):
                max_len = len(str(col_name))
                for val in df[col_name]:
                    if val is not None and not pd.isna(val):
                        max_len = max(max_len, len(str(val)))
                col_letter = get_column_letter(col_idx)
                worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

        return str(filepath)

    def export_all(self, base_name: str, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Eksportuje dane jednocześnie do CSV (standard i polski Excel), JSON oraz XLSX.
        """
        csv_path = self.export_to_csv(f"{base_name}.csv", products, decimal_comma=False)
        csv_pl_path = self.export_to_csv(f"{base_name}_excel_pl.csv", products, decimal_comma=True)
        json_path = self.export_to_json(f"{base_name}.json", products)
        xlsx_path = self.export_to_excel(f"{base_name}.xlsx", products)

        res = {
            "record_count": len(products),
            "column_count": len(self.COLUMN_ORDER),
            "csv_path": csv_path,
            "csv_size_kb": round(os.path.getsize(csv_path) / 1024, 2),
            "csv_pl_path": csv_pl_path,
            "json_path": json_path,
            "json_size_kb": round(os.path.getsize(json_path) / 1024, 2)
        }
        if xlsx_path and os.path.exists(xlsx_path):
            res["xlsx_path"] = xlsx_path
            res["xlsx_size_kb"] = round(os.path.getsize(xlsx_path) / 1024, 2)

        return res
