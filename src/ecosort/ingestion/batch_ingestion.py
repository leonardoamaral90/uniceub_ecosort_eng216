from __future__ import annotations

import hashlib
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ecosort.class_map import display_class, is_recyclable, normalize_class
from ecosort.config import Settings, get_settings
from ecosort.dataset import IMAGE_SUFFIXES, download_kaggle_dataset, find_class_directories
from ecosort.storage import ensure_buckets, upload_directory, upload_file


def _stable_image_id(path: Path) -> str:
    digest = hashlib.sha1(path.as_posix().encode("utf-8")).hexdigest()
    return str(uuid.UUID(digest[:32]))


def _turno(index: int) -> str:
    return ["MANHA", "TARDE", "NOITE"][index % 3]


def run_batch_ingestion(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    ensure_buckets(settings)
    dataset_root = download_kaggle_dataset(settings)
    class_dirs = find_class_directories(dataset_root)
    if not class_dirs:
        raise RuntimeError(f"Nenhuma pasta de classe esperada foi encontrada em {dataset_root}.")

    batch_id = datetime.now(timezone.utc).strftime("batch_%Y%m%dT%H%M%SZ")
    bronze_batch_dir = settings.bronze_dir / "batch_metadata" / f"batch_id={batch_id}"
    bronze_image_dir = settings.bronze_dir / "images" / f"batch_id={batch_id}"
    bronze_batch_dir.mkdir(parents=True, exist_ok=True)
    bronze_image_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    total_images = 0

    for class_name, class_dir in sorted(class_dirs.items()):
        images = [p for p in class_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
        images = sorted(images)
        if settings.max_images_per_class > 0:
            images = images[: settings.max_images_per_class]

        for idx, image_path in enumerate(images):
            total_images += 1
            rel_path = image_path.relative_to(dataset_root).as_posix()
            image_id = _stable_image_id(image_path.relative_to(dataset_root))
            local_copy = bronze_image_dir / normalize_class(class_name) / image_path.name
            local_copy.parent.mkdir(parents=True, exist_ok=True)
            if not local_copy.exists():
                shutil.copy2(image_path, local_copy)

            rows.append(
                {
                    "image_id": image_id,
                    "class_label": display_class(class_name),
                    "class_label_normalized": normalize_class(class_name),
                    "recyclable": is_recyclable(class_name),
                    "file_name": image_path.name,
                    "source_relative_path": rel_path,
                    "bronze_image_path": local_copy.as_posix(),
                    "file_size_kb": round(image_path.stat().st_size / 1024, 3),
                    "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_timestamp": datetime.now(timezone.utc).isoformat(),
                    "batch_id": batch_id,
                    "source_type": "batch",
                    "camera_id": None,
                    "route_id": f"ROTA-{(idx % 5) + 1:02d}",
                    "turno_simulado": _turno(idx),
                    "confidence": 1.0,
                }
            )

    if not rows:
        raise RuntimeError("Nenhuma imagem foi localizada para ingestão batch.")

    df = pd.DataFrame(rows)
    parquet_path = bronze_batch_dir / "metadata.parquet"
    df.to_parquet(parquet_path, index=False)

    upload_file(settings.minio_bucket_bronze, f"batch_metadata/batch_id={batch_id}/metadata.parquet", parquet_path, settings)
    uploaded_images = 0
    if settings.upload_images_to_minio:
        uploaded_images = upload_directory(settings.minio_bucket_bronze, f"images/batch_id={batch_id}", bronze_image_dir, settings)

    print(f"[batch] {len(df)} registros gravados em {parquet_path}")
    return {
        "batch_id": batch_id,
        "records": len(df),
        "classes": sorted(df["class_label"].unique().tolist()),
        "parquet_path": str(parquet_path),
        "uploaded_images": uploaded_images,
        "dataset_root": str(dataset_root),
        "total_images_seen": total_images,
    }


if __name__ == "__main__":
    print(run_batch_ingestion())
