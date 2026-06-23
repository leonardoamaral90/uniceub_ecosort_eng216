from __future__ import annotations

import time

from prefect import flow, get_run_logger, task

from ecosort.config import get_settings
from ecosort.ingestion.batch_ingestion import run_batch_ingestion
from ecosort.ingestion.kafka_consumer import consume_events
from ecosort.ingestion.kafka_producer import produce_events
from ecosort.processing.spark_jobs import build_silver_candidate, promote_candidate_to_silver
from ecosort.quality.validate_silver import validate_silver_candidate
from ecosort.storage import ensure_buckets
from ecosort.transformation.build_gold import run_dbt_gold


@task(retries=3, retry_delay_seconds=5)
def prepare_storage_task() -> None:
    ensure_buckets(get_settings())


@task(retries=2, retry_delay_seconds=10)
def batch_ingestion_task() -> dict:
    return run_batch_ingestion(get_settings())


@task(retries=1, retry_delay_seconds=5)
def kafka_simulation_task() -> dict:
    settings = get_settings()
    logger = get_run_logger()
    if settings.stream_events_on_pipeline <= 0:
        logger.info("Simulação Kafka desabilitada por ECOSORT_STREAM_EVENTS_ON_PIPELINE=0")
        return {"sent": 0, "consumed": 0}

    # Producer primeiro, consumer em seguida usando grupo novo e auto_offset_reset=earliest.
    sent = produce_events(count=settings.stream_events_on_pipeline, continuous=False, settings=settings)
    time.sleep(2)
    consumed = consume_events(count=settings.stream_events_on_pipeline, continuous=False, settings=settings)
    return {"sent": sent, "consumed": consumed}


@task(retries=1, retry_delay_seconds=5)
def spark_candidate_task() -> dict:
    return build_silver_candidate(get_settings())


@task(retries=1, retry_delay_seconds=5)
def quality_gate_task() -> dict:
    return validate_silver_candidate(get_settings())


@task(retries=1, retry_delay_seconds=5)
def promote_silver_task() -> dict:
    return promote_candidate_to_silver(get_settings())


@task(retries=1, retry_delay_seconds=5)
def dbt_gold_task() -> dict:
    return run_dbt_gold(get_settings())


@flow(name="ecosort_pipeline", log_prints=True)
def ecosort_pipeline() -> dict:
    logger = get_run_logger()
    logger.info("Iniciando pipeline EcoSort...")

    prepare_storage_task()
    batch_info = batch_ingestion_task()
    stream_info = kafka_simulation_task()
    candidate_info = spark_candidate_task()
    quality_info = quality_gate_task()
    silver_info = promote_silver_task()
    gold_info = dbt_gold_task()

    result = {
        "batch": batch_info,
        "streaming": stream_info,
        "candidate": candidate_info,
        "quality": quality_info,
        "silver": silver_info,
        "gold": gold_info,
    }
    logger.info("Pipeline EcoSort concluído com sucesso.")
    return result


if __name__ == "__main__":
    ecosort_pipeline()
