import asyncio
import logging
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from transformers import (
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from .config import get_settings
from .detectors.aggregator import DISCLAIMER, aggregate
from .detectors.perplexity import PerplexityDetector
from .detectors.stylometric import analyze_stylometric
from .detectors.translation_classifier import TranslationClassifierDetector
from .extraction import ExtractionError, UnsupportedFileTypeError, extract_text
from .schemas import AnalyzeResponse, HealthResponse
from .utils.concurrency import BoundedExecutor, BusyError

logger = logging.getLogger("detectoria")

_state: dict = {}


def _quantize(model):
    return torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    torch.set_num_threads(settings.torch_num_threads)

    logger.info("Cargando modelo de lenguaje en español: %s", settings.spanish_lm_model)
    lm_tokenizer = AutoTokenizer.from_pretrained(settings.spanish_lm_model)
    lm_model = AutoModelForCausalLM.from_pretrained(settings.spanish_lm_model)
    lm_model.eval()
    lm_model = _quantize(lm_model)
    _state["perplexity_detector"] = PerplexityDetector(lm_tokenizer, lm_model)

    if settings.enable_translation_classifier:
        logger.info("Cargando modelo de traducción: %s", settings.translation_model)
        translator_tokenizer = AutoTokenizer.from_pretrained(settings.translation_model)
        translator_model = AutoModelForSeq2SeqLM.from_pretrained(settings.translation_model)
        translator_model.eval()
        translator_model = _quantize(translator_model)

        logger.info("Cargando clasificador en inglés: %s", settings.english_classifier_model)
        classifier_tokenizer = AutoTokenizer.from_pretrained(settings.english_classifier_model)
        classifier_model = AutoModelForSequenceClassification.from_pretrained(
            settings.english_classifier_model
        )
        classifier_model.eval()
        classifier_model = _quantize(classifier_model)

        _state["translation_detector"] = TranslationClassifierDetector(
            translator_tokenizer, translator_model, classifier_tokenizer, classifier_model
        )

    _state["executor"] = BoundedExecutor(settings.max_concurrent_analyses)
    _state["models_loaded"] = True
    logger.info("Modelos cargados. Listo para analizar documentos.")

    yield

    _state.clear()


app = FastAPI(title="DetectorIA", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _run_analysis(text: str) -> AnalyzeResponse:
    settings = get_settings()
    outputs = [analyze_stylometric(text)]

    perplexity_detector: PerplexityDetector = _state["perplexity_detector"]
    source_b, source_c = perplexity_detector.analyze(text)
    outputs.extend([source_b, source_c])

    warnings: list[str] = []
    if settings.enable_translation_classifier:
        translation_detector = _state.get("translation_detector")
        if translation_detector is not None:
            outputs.append(translation_detector.analyze(text))
        else:
            warnings.append("La fuente de traducción/clasificador no está disponible en este momento.")

    overall_score, overall_label, sources = aggregate(outputs, settings)

    return AnalyzeResponse(
        overall_score=overall_score,
        label=overall_label,
        sources=sources,
        warnings=warnings,
        disclaimer=DISCLAIMER,
    )


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        models_loaded=bool(_state.get("models_loaded")),
        translation_classifier_enabled=settings.enable_translation_classifier,
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile = File(...)) -> AnalyzeResponse:
    settings = get_settings()

    data = await file.read()
    if len(data) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el tamaño máximo permitido ({settings.max_upload_size_bytes // (1024 * 1024)}MB).",
        )

    try:
        text = extract_text(file.filename or "", data, min_chars=settings.min_extractable_chars)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    executor: BoundedExecutor = _state["executor"]
    try:
        return await asyncio.wait_for(
            executor.run(_run_analysis, text), timeout=settings.analysis_timeout_seconds
        )
    except BusyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=504, detail="El análisis tardó demasiado. Probá con un documento más corto."
        ) from exc
