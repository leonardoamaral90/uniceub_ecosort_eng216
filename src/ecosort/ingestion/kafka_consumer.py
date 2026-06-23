from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

import pandas as pd
from kafka import KafkaConsumer

from ecosort.config import Settings, get_settings
from ecosort.storage import ensure_buckets, upload_file


def consume_events(count: int | None = None, continuous: bool = False, timeout_seconds: int | None = None, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    ensure_buckets(settings)
    timeout_seconds = timeout_seconds or settings.stream_seconds
    consumer = KafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=f"ecosort-consumer-{int(time.time())}",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        consumer_timeout_ms=1000,
    )

    started = time.time()
    rows: list[dict] = []

    try:
        while continuous or len(rows) < (count or 0):
            for message in consumer:
                event = message.value
                event["kafka_topic"] = message.topic
                event["kafka_partition"] = message.partition
                event["kafka_offset"] = message.offset
                event["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()
                event["event_timestamp"] = event.get("timestamp")
                event["source_type"] = event.get("source_type") or "streaming"
                event["image_id"] = event.get("event_id")
                rows.append(event)
                if count and len(rows) >= count:
                    break
            if not continuous and count and len(rows) >= count:
                break
            if not continuous and time.time() - started > timeout_seconds:
                break
            if continuous and rows and len(rows) % 100 == 0:
                _flush(rows, settings)
                rows.clear()
    finally:
        consumer.close()

    output = _flush(rows, settings) if rows else None
    print(f"[consumer] {len(rows)} eventos consumidos.")
    return {"events": len(rows), "output": output}


def _flush(rows: list[dict], settings: Settings) -> str:
    run_id = datetime.now(timezone.utc).strftime("stream_%Y%m%dT%H%M%SZ")
    out_dir = settings.bronze_dir / "stream_events" / f"run_id={run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "events.parquet"
    pd.DataFrame(rows).to_parquet(out_path, index=False)
    upload_file(settings.minio_bucket_bronze, f"stream_events/run_id={run_id}/events.parquet", out_path, settings)
    return str(out_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=None)
    parser.add_argument("--continuous", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    count = args.count if args.count is not None else settings.stream_events_on_pipeline
    print(consume_events(count=count, continuous=args.continuous, settings=settings))


if __name__ == "__main__":
    main()
