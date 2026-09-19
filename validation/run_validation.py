"""Corre el set de validación contra una instancia de DetectorIA y reporta
métricas reales (no una sola anécdota) para calibrar umbrales y pesos.

Uso:
    python validation/run_validation.py --url https://detectoria.duckdns.org
    python validation/run_validation.py --url http://localhost
"""

import argparse
import statistics
import sys
from pathlib import Path

import requests

TEXTOS_DIR = Path(__file__).parent / "textos"
CATEGORIAS = {"humano": 0, "ia": 100}  # score ideal de referencia para cada carpeta


def analizar_archivo(base_url: str, path: Path) -> dict:
    with open(path, "rb") as f:
        response = requests.post(
            f"{base_url}/api/analyze",
            files={"file": (path.name, f, "text/plain")},
            timeout=90,
        )
    response.raise_for_status()
    return response.json()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Base URL de DetectorIA, ej. https://detectoria.duckdns.org")
    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    resultados = []
    for categoria in CATEGORIAS:
        carpeta = TEXTOS_DIR / categoria
        for path in sorted(carpeta.glob("*.txt")):
            print(f"Analizando [{categoria}] {path.name}...", file=sys.stderr)
            try:
                data = analizar_archivo(base_url, path)
            except Exception as exc:
                print(f"  ERROR: {exc}", file=sys.stderr)
                continue
            resultados.append({
                "categoria": categoria,
                "archivo": path.name,
                "overall_score": data["overall_score"],
                "overall_label": data["label"],
                "sources": {s["id"]: s["score"] for s in data["sources"]},
            })

    if not resultados:
        print("No se pudo analizar ningún archivo.", file=sys.stderr)
        return 1

    # --- Reporte detallado ---
    print("\n=== Resultado por archivo ===")
    fuente_ids = sorted({sid for r in resultados for sid in r["sources"]})
    header = f"{'categoria':10} {'score':>6} {'label':16} " + " ".join(f"{s:>12}" for s in fuente_ids) + "  archivo"
    print(header)
    for r in resultados:
        fuentes = " ".join(f"{r['sources'].get(s, '-'):>12}" for s in fuente_ids)
        print(f"{r['categoria']:10} {r['overall_score']:>6} {r['overall_label']:16} {fuentes}  {r['archivo']}")

    # --- Métricas agregadas ---
    print("\n=== Métricas agregadas ===")
    umbral_decision = 50  # score >= 50 se interpreta como "predicho IA"
    aciertos = 0
    for categoria in CATEGORIAS:
        subset = [r for r in resultados if r["categoria"] == categoria]
        if not subset:
            continue
        scores = [r["overall_score"] for r in subset]
        predicho_ia = sum(1 for s in scores if s >= umbral_decision)
        correcto = predicho_ia if categoria == "ia" else (len(subset) - predicho_ia)
        aciertos += correcto
        print(
            f"{categoria:10} n={len(subset):2}  score medio={statistics.mean(scores):5.1f}  "
            f"min={min(scores):3}  max={max(scores):3}  "
            f"clasificados como IA (score>={umbral_decision}): {predicho_ia}/{len(subset)}"
        )

    total = len(resultados)
    print(f"\nExactitud global (umbral {umbral_decision}): {aciertos}/{total} = {100 * aciertos / total:.1f}%")

    print("\n=== Score medio por fuente y categoría ===")
    for categoria in CATEGORIAS:
        subset = [r for r in resultados if r["categoria"] == categoria]
        if not subset:
            continue
        medias = {sid: statistics.mean(r["sources"].get(sid, 0) for r in subset) for sid in fuente_ids}
        print(f"{categoria:10} " + "  ".join(f"{sid}={v:.1f}" for sid, v in medias.items()))

    return 0


if __name__ == "__main__":
    sys.exit(main())
