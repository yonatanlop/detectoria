from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Feature flags
    enable_translation_classifier: bool = False

    # Model identifiers (Hugging Face hub ids)
    spanish_lm_model: str = "mrm8488/spanish-gpt2"
    translation_model: str = "Helsinki-NLP/opus-mt-es-en"
    english_classifier_model: str = "openai-community/roberta-base-openai-detector"

    # Runtime / concurrency
    torch_num_threads: int = 2
    max_concurrent_analyses: int = 2
    analysis_timeout_seconds: int = 45

    # Upload limits
    max_upload_size_bytes: int = 8 * 1024 * 1024  # 8 MB
    min_extractable_chars: int = 200

    # Chunking (overridden at runtime from each model's real context window)
    max_chunk_chars_fallback: int = 3000

    # Aggregation weights: source_id -> weight
    weight_stylometric: float = 0.15
    weight_perplexity: float = 0.35
    weight_token_rank: float = 0.35
    weight_translation_classifier: float = 0.15

    # Verdict thresholds (score 0-100)
    threshold_human_max: int = 34
    threshold_ai_hints_max: int = 64

    def source_weights(self) -> dict[str, float]:
        if self.enable_translation_classifier:
            return {
                "stylometric": self.weight_stylometric,
                "perplexity": self.weight_perplexity,
                "token_rank": self.weight_token_rank,
                "translation_classifier": self.weight_translation_classifier,
            }
        # Redistribute source D's weight proportionally when disabled
        return {
            "stylometric": 0.20,
            "perplexity": 0.45,
            "token_rank": 0.35,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
