#!/usr/bin/env python3
"""
Reads a promotional CSV and outputs a JSON payload for the Figma plugin.

CSV format (no header, semicolon-separated):
  image_filename;product_name;previous_price;new_price

Usage:
  python generate_figma_metadata.py promocoes/promocoes.csv --data 2026-06-14
"""

import argparse
import base64
import csv
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

MONTHS_PT_NAME = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def parse_date(raw: str) -> date:
    raw = raw.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", raw)
    if not m:
        sys.exit(f"Formato de data inválido: '{raw}'\nUse: 2026-06-14")
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def frame_name(target: date) -> str:
    return f"{target.day} de {MONTHS_PT_NAME[target.month]}"


def validity_text(target: date) -> str:
    start = target + timedelta(days=1)
    end = target + timedelta(days=7)
    return (
        f"Ofertas válidas de {start.strftime('%d/%m')} até "
        f"{end.strftime('%d/%m')} ou enquanto durarem os estoques."
    )


def encode_image(path: Path) -> str:
    ext = path.suffix.lstrip(".").lower()
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/{mime};base64,{data}"


def main():
    parser = argparse.ArgumentParser(description="Gera metadata JSON para o plugin Figma de promoções.")
    parser.add_argument("csv", help="Caminho para o arquivo CSV")
    parser.add_argument("--data", required=True, metavar="DATA", help="Data alvo no formato ISO (ex: 2026-06-14)")
    args = parser.parse_args()

    csv_path = Path(args.csv).resolve()
    if not csv_path.exists():
        sys.exit(f"CSV não encontrado: {csv_path}")

    base_dir = csv_path.parent

    target = parse_date(args.data)

    products = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        for i, row in enumerate(reader, start=1):
            if len(row) < 4:
                sys.exit(f"Linha {i} inválida (esperado 4 colunas): {row}")
            img_file, name, prev_price, new_price = (c.strip() for c in row[:4])
            img_path = base_dir / img_file
            if not img_path.exists():
                sys.exit(f"Imagem não encontrada: {img_path}")
            products.append({
                "name": name,
                "prev_price": prev_price,
                "new_price": new_price,
                "image_b64": encode_image(img_path),
            })

    payload = {
        "frame_name": frame_name(target),
        "validity_text": validity_text(target),
        "products": products,
    }

    output_path = csv_path.with_suffix(".json")
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ {len(products)} produto(s) exportado(s) → {output_path}")
    print(f"  Frame: \"{payload['frame_name']}\"")
    print(f"  Validade: {payload['validity_text']}")


if __name__ == "__main__":
    main()
