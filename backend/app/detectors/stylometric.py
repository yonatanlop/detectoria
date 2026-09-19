"""Source A: stylometric/linguistic heuristics, no ML model required.

Combines sentence-length burstiness, vocabulary richness (moving-average TTR),
punctuation regularity and n-gram repetition into a single 0-1 score. Each
sub-signal is a weak, noisy proxy on its own; averaging several independent
weak signals is the point of this detector within the larger ensemble.
"""

import re
import statistics

from . import DetectorOutput

_SENTENCE_SPLIT_RE = re.compile(r"[.!?…]+[\s\n]+")
_WORD_RE = re.compile(r"\b[^\W\d_]+\b", re.UNICODE)
_MATTR_WINDOW = 50


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


def _words(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


def _burstiness_score(sentence_word_counts: list[int]) -> tuple[float, float]:
    if len(sentence_word_counts) < 3:
        return 0.5, 0.0
    mean_len = statistics.mean(sentence_word_counts)
    std_len = statistics.pstdev(sentence_word_counts)
    if mean_len + std_len == 0:
        return 0.5, 0.0
    burstiness = (std_len - mean_len) / (std_len + mean_len)  # in [-1, 1]
    score = _clamp((1 - burstiness) / 2)
    return score, burstiness


def _mattr(words: list[str], window: int = _MATTR_WINDOW) -> float:
    if len(words) < window:
        if not words:
            return 1.0
        return len(set(words)) / len(words)
    ratios = []
    for i in range(0, len(words) - window + 1, window // 2 or 1):
        chunk = words[i : i + window]
        ratios.append(len(set(chunk)) / len(chunk))
    return statistics.mean(ratios) if ratios else 1.0


def _vocab_score(mattr: float) -> float:
    # mattr ~0.9 -> rich vocabulary (human-like), ~0.3 -> repetitive (AI-leaning)
    return _clamp(1 - (mattr - 0.3) / (0.9 - 0.3))


def _punctuation_score(sentences: list[str]) -> tuple[float, float]:
    counts = [len(re.findall(r"[,;:]", s)) for s in sentences]
    if len(counts) < 3:
        return 0.5, 0.0
    mean_c = statistics.mean(counts)
    if mean_c == 0:
        return 0.5, 0.0
    std_c = statistics.pstdev(counts)
    cv = std_c / mean_c
    score = _clamp(1 - min(cv, 1.0))
    return score, cv


def _repetition_score(words: list[str]) -> tuple[float, float]:
    if len(words) < 10:
        return 0.5, 1.0
    trigrams = [tuple(words[i : i + 3]) for i in range(len(words) - 2)]
    unique_ratio = len(set(trigrams)) / len(trigrams)
    score = _clamp(1 - unique_ratio)
    return score, unique_ratio


def analyze_stylometric(text: str) -> DetectorOutput:
    sentences = _sentences(text)
    words = _words(text)
    sentence_word_counts = [len(_words(s)) for s in sentences]

    burst_score, burstiness = _burstiness_score(sentence_word_counts)
    mattr = _mattr(words)
    vocab_score = _vocab_score(mattr)
    punct_score, punct_cv = _punctuation_score(sentences)
    repeat_score, unique_trigram_ratio = _repetition_score(words)

    final_score = (
        0.35 * burst_score
        + 0.25 * vocab_score
        + 0.15 * punct_score
        + 0.25 * repeat_score
    )

    details = (
        f"Burstiness de oraciones: {burstiness:.2f} (variación en longitud de oraciones). "
        f"Riqueza de vocabulario (MATTR): {mattr:.2f}. "
        f"Regularidad de puntuación (CV): {punct_cv:.2f}. "
        f"Trigramas únicos: {unique_trigram_ratio:.2f}."
    )

    return DetectorOutput(
        id="stylometric",
        name="Heurísticas estilométricas",
        score=_clamp(final_score),
        details=details,
    )
