from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "sim"}


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv("ECOSORT_DATA_DIR", "/data"))
    lakehouse_dir: Path = Path(os.getenv("ECOSORT_LAKEHOUSE_DIR", "/data/lakehouse"))
    duckdb_path: Path = Path(os.getenv("ECOSORT_DUCKDB_PATH", "/data/duckdb/ecosort.duckdb"))

    kaggle_dataset: str = os.getenv("KAGGLE_DATASET", "sumn2u/garbage-classification-v2")
    kaggle_dataset_dir: Path = Path(os.getenv("KAGGLE_DATASET_DIR", "/data/raw/garbage-classification-v2"))
    allow_sample_data: bool = _bool("ECOSORT_ALLOW_SAMPLE_DATA", True)
    max_images_per_class: int = _int("ECOSORT_MAX_IMAGES_PER_CLASS", 0)
    upload_images_to_minio: bool = _bool("ECOSORT_UPLOAD_IMAGES_TO_MINIO", True)

    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    minio_external_endpoint: str = os.getenv("MINIO_EXTERNAL_ENDPOINT", "http://localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "ecosort")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "ecosort123")
    minio_bucket_bronze: str = os.getenv("MINIO_BUCKET_BRONZE", "bronze")
    minio_bucket_silver: str = os.getenv("MINIO_BUCKET_SILVER", "silver")
    minio_bucket_gold: str = os.getenv("MINIO_BUCKET_GOLD", "gold")

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    kafka_topic: str = os.getenv("KAFKA_TOPIC", "residuos-eventos")
    stream_events_on_pipeline: int = _int("ECOSORT_STREAM_EVENTS_ON_PIPELINE", 25)
    stream_seconds: int = _int("ECOSORT_STREAM_SECONDS", 20)

    spark_master: str = os.getenv("SPARK_MASTER", "local[*]")
    spark_driver_memory: str = os.getenv("SPARK_DRIVER_MEMORY", "2g")

    @property
    def bronze_dir(self) -> Path:
        return self.lakehouse_dir / "bronze"

    @property
    def silver_dir(self) -> Path:
        return self.lakehouse_dir / "silver"

    @property
    def gold_dir(self) -> Path:
        return self.lakehouse_dir / "gold"

    @property
    def ge_docs_dir(self) -> Path:
        return self.lakehouse_dir / "great_expectations" / "data_docs"


def get_settings() -> Settings:
    settings = Settings()
    for path in [
        settings.data_dir,
        settings.kaggle_dataset_dir,
        settings.bronze_dir,
        settings.silver_dir,
        settings.gold_dir,
        settings.ge_docs_dir,
        settings.duckdb_path.parent,
    ]:
        path.mkdir(parents=True, exist_ok=True)
    return settings
