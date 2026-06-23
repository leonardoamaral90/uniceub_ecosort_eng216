from __future__ import annotations

import argparse

from ecosort.ingestion.batch_ingestion import run_batch_ingestion
from ecosort.ingestion.kafka_consumer import consume_events
from ecosort.ingestion.kafka_producer import produce_events
from ecosort.orchestration.flows import ecosort_pipeline
from ecosort.processing.spark_jobs import build_silver_candidate, promote_candidate_to_silver
from ecosort.quality.validate_silver import validate_silver_candidate
from ecosort.transformation.build_gold import run_dbt_gold


def main() -> None:
    parser = argparse.ArgumentParser(prog="ecosort")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("pipeline")
    sub.add_parser("batch")
    sub.add_parser("produce")
    sub.add_parser("consume")
    sub.add_parser("spark-candidate")
    sub.add_parser("validate")
    sub.add_parser("promote-silver")
    sub.add_parser("dbt-gold")
    args = parser.parse_args()

    if args.command == "pipeline":
        ecosort_pipeline()
    elif args.command == "batch":
        print(run_batch_ingestion())
    elif args.command == "produce":
        print(produce_events(count=25))
    elif args.command == "consume":
        print(consume_events(count=25))
    elif args.command == "spark-candidate":
        print(build_silver_candidate())
    elif args.command == "validate":
        print(validate_silver_candidate())
    elif args.command == "promote-silver":
        print(promote_candidate_to_silver())
    elif args.command == "dbt-gold":
        print(run_dbt_gold())


if __name__ == "__main__":
    main()
