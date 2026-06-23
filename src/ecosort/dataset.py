from __future__ import annotations

import os
import random
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable

from PIL import Image, ImageDraw

from ecosort.class_map import EXPECTED_CLASSES, display_class, normalize_class
from ecosort.config import Settings, get_settings

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _has_kaggle_credentials() -> bool:
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    return kaggle_json.exists() or bool(os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"))


def _count_images(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)


def _candidate_dataset_dirs(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    candidates = [root]
    candidates.extend([p for p in root.rglob("*") if p.is_dir()])
    return candidates


def find_class_directories(dataset_dir: Path) -> Dict[str, Path]:
    found: Dict[str, Path] = {}
    for candidate in _candidate_dataset_dirs(dataset_dir):
        normalized = normalize_class(candidate.name)
        if normalized in EXPECTED_CLASSES:
            if any(p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES for p in candidate.rglob("*")):
                found[normalized] = candidate
    return found


def create_sample_dataset(settings: Settings | None = None, images_per_class: int = 5) -> Path:
    settings = settings or get_settings()
    root = settings.kaggle_dataset_dir
    root.mkdir(parents=True, exist_ok=True)
    random.seed(216)
    for class_name in sorted(EXPECTED_CLASSES):
        class_dir = root / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        for idx in range(images_per_class):
            img_path = class_dir / f"sample_{class_name}_{idx:03d}.jpg"
            if img_path.exists():
                continue
            img = Image.new("RGB", (224, 224), color=(random.randint(40, 220), random.randint(40, 220), random.randint(40, 220)))
            draw = ImageDraw.Draw(img)
            draw.text((16, 96), display_class(class_name), fill=(255, 255, 255))
            img.save(img_path, format="JPEG", quality=85)
    return root


def download_kaggle_dataset(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    target = settings.kaggle_dataset_dir
    target.mkdir(parents=True, exist_ok=True)

    existing = _count_images(target)
    if existing > 0 and find_class_directories(target):
        print(f"[dataset] Dataset já encontrado em {target} com {existing} imagens.")
        return target

    if _has_kaggle_credentials():
        print(f"[dataset] Baixando dataset Kaggle: {settings.kaggle_dataset}")
        subprocess.run(
            [
                "kaggle",
                "datasets",
                "download",
                "-d",
                settings.kaggle_dataset,
                "-p",
                str(target),
                "--unzip",
            ],
            check=True,
        )
        found = _count_images(target)
        if found == 0:
            raise RuntimeError(f"Download Kaggle concluído, mas nenhuma imagem foi encontrada em {target}.")
        print(f"[dataset] Download concluído com {found} imagens.")
        return target

    if settings.allow_sample_data:
        print("[dataset] Credenciais Kaggle não encontradas. Gerando amostra sintética para validar a arquitetura.")
        return create_sample_dataset(settings)

    raise RuntimeError(
        "Dataset Kaggle não encontrado e credenciais Kaggle ausentes. "
        "Coloque kaggle/kaggle.json ou configure KAGGLE_USERNAME/KAGGLE_KEY."
    )


def reset_dataset(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    if settings.kaggle_dataset_dir.exists():
        shutil.rmtree(settings.kaggle_dataset_dir)
