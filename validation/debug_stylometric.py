"""Herramienta de diagnóstico: corre las sub-heurísticas de estilometría
localmente (sin red, sin ML) sobre el set de validación e imprime cada
valor intermedio, no solo el score final, para ver dónde se pierde la
separación entre humano e IA.
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.detectors.stylometric import (  # noqa: E402
    _burstiness_score,
    _connector_overuse_score,
    _mattr,
    _punctuation_score,
    _repetition_score,
    _sentences,
    _vocab_score,
    _words,
)

TEXTOS_DIR = Path(__file__).parent / "textos"

rows = []
for categoria in ("humano", "ia"):
    for path in sorted((TEXTOS_DIR / categoria).glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        sentences = _sentences(text)
        words = _words(text)
        sentence_word_counts = [len(_words(s)) for s in sentences]

        burst_score, burstiness = _burstiness_score(sentence_word_counts)
        mattr = _mattr(words)
        vocab_score = _vocab_score(mattr)
        punct_score, punct_cv = _punctuation_score(sentences)
        repeat_score, unique_trigram_ratio = _repetition_score(words)
        connector_score, connector_fraction = _connector_overuse_score(sentences)

        final = 0.75 * (0.35 * burst_score + 0.25 * vocab_score + 0.15 * punct_score + 0.25 * repeat_score) + 0.25 * connector_score

        rows.append({
            "categoria": categoria,
            "archivo": path.name,
            "n_sent": len(sentences),
            "n_words": len(words),
            "burstiness": burstiness,
            "burst_score": burst_score,
            "mattr": mattr,
            "vocab_score": vocab_score,
            "punct_cv": punct_cv,
            "punct_score": punct_score,
            "trigram_ratio": unique_trigram_ratio,
            "repeat_score": repeat_score,
            "connector_fraction": connector_fraction,
            "connector_score": connector_score,
            "final": final,
        })

cols = ["n_sent", "n_words", "burstiness", "burst_score", "mattr", "vocab_score",
        "punct_cv", "punct_score", "trigram_ratio", "repeat_score",
        "connector_fraction", "connector_score", "final"]

header = f"{'cat':8} {'archivo':42} " + " ".join(f"{c:>13}" for c in cols)
print(header)
for r in rows:
    vals = " ".join(f"{r[c]:>13.3f}" if isinstance(r[c], float) else f"{r[c]:>13}" for c in cols)
    print(f"{r['categoria']:8} {r['archivo']:42} {vals}")

print("\n=== Medias por categoría ===")
for categoria in ("humano", "ia"):
    subset = [r for r in rows if r["categoria"] == categoria]
    medias = {c: statistics.mean(r[c] for r in subset) for c in cols}
    print(f"{categoria:8} " + " ".join(f"{c}={medias[c]:.3f}" for c in cols))
