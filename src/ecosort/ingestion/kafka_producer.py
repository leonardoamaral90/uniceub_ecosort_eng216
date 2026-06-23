from __future__ import annotations

import argparse
import json
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer

from ecosort.class_map import display_class, is_recyclable, normalize_class
from ecosort.config import Settings, get_settings
from ecosort.dataset import IMAGE_SUFFIXES, download_kaggle_dataset, find_class_directories


def _build_inventory(settings: Settings) -> list[tuple[str, str]]:
    dataset_root = download_kaggle_dataset(settings)
    class_dirs = find_class_directories(dataset_root)
    inventory: list[tuple[str, str]] = []
    for class_name, class_dir in class_dirs.items():
        for image_path in class_dir.rglob("*"):
            if image_path.is_file() and image_path.suffix.lower() in IMAGE_SUFFIXES:
                inventory.append((class_name, image_path.relative_to(dataset_root).as_posix()))
    if not inventory:
        raise RuntimeError("Inventory de imagens vazio; execute a ingestão batch ou configure o dataset.")
    return inventory


def produce_events(count: int | None = None, continuous: bool = False, settings: Settings | None = None) -> int:
    settings = settings or get_settings()
    inventory = _build_inventory(settings)
    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda value: value.encode("utf-8"),
        retries=5,
    )

    sent = 0
    cameras = ["CAM-01", "CAM-02", "CAM-03"]
    try:
        while continuous or sent < (count or 0):
            class_name, image_path = random.choice(inventory)
            confidence = round(random.uniform(0.72, 0.99), 4)
            event = {
                "event_id": str(uuid.uuid4()),
                "camera_id": random.choice(cameras),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "image_path": image_path,
                "predicted_class": display_class(class_name),
                "class_label": display_class(class_name),
                "class_label_normalized": normalize_class(class_name),
                "recyclable": is_recyclable(class_name),
                "confidence": confidence,
                "route_id": f"ROTA-{random.randint(1, 5):02d}",
                "turno_simulado": random.choice(["MANHA", "TARDE", "NOITE"]),
                "source_type": "streaming",
            }
            producer.send(settings.kafka_topic, key=event["event_id"], value=event)
            sent += 1
            if sent % 10 == 0:
                print(f"[producer] {sent} eventos publicados em {settings.kafka_topic}")
            time.sleep(0.25 if continuous else 0.05)
    finally:
        producer.flush(timeout=10)
        producer.close(timeout=10)
    return sent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=None)
    parser.add_argument("--continuous", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    count = args.count if args.count is not None else settings.stream_events_on_pipeline
    sent = produce_events(count=count, continuous=args.continuous, settings=settings)
    print(f"[producer] finalizado com {sent} eventos.")


if __name__ == "__main__":
    main()
