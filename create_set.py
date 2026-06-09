#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from PIL import Image

GAP_MIN = 10
GAP_MAX = 60
GAP_RATIO = 0.05


def _compute_gap(resized: list) -> int:
    avg_width = sum(img.width for img in resized) / len(resized)
    return max(GAP_MIN, min(GAP_MAX, round(avg_width * GAP_RATIO)))


def _build_set(pngs: list[Path], output_dir: Path) -> Path:
    if len(pngs) < 2:
        print(f"Erro: é necessário pelo menos 2 PNGs (encontrado: {len(pngs)})", file=sys.stderr)
        sys.exit(1)

    images = [Image.open(p).convert("RGBA") for p in pngs]

    min_height = min(img.height for img in images)

    resized = []
    for img in images:
        if img.height != min_height:
            new_width = round(img.width * min_height / img.height)
            img = img.resize((new_width, min_height), Image.LANCZOS)
        resized.append(img)

    gap = _compute_gap(resized)
    total_width = sum(img.width for img in resized) + gap * (len(resized) - 1)
    canvas = Image.new("RGBA", (total_width, min_height), (0, 0, 0, 0))

    x = 0
    for img in resized:
        canvas.paste(img, (x, 0))
        x += img.width + gap

    output = output_dir / "conjunto.png"
    canvas.save(output, format="PNG")
    print(f"Conjunto criado: {output} ({total_width}x{min_height}px, {len(resized)} imagens, gap={gap}px)")
    return output


def create_set(directory: Path) -> Path:
    pngs = sorted(p for p in directory.iterdir() if p.suffix.lower() == ".png" and p.stem != "conjunto")
    return _build_set(pngs, directory)


def create_set_from_files(files: list[Path]) -> Path:
    pngs = sorted(f for f in files if f.suffix.lower() == ".png")
    output_dir = pngs[0].parent if pngs else files[0].parent
    return _build_set(pngs, output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria um conjunto de imagens lado a lado com a mesma altura.")
    parser.add_argument("paths", nargs="+", type=Path, help="Diretório com PNGs ou lista de arquivos PNG.")
    args = parser.parse_args()

    if len(args.paths) == 1 and args.paths[0].is_dir():
        create_set(args.paths[0])
    else:
        create_set_from_files(args.paths)


if __name__ == "__main__":
    main()
