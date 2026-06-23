from __future__ import annotations

from pathlib import Path

from delta import configure_spark_with_delta_pip
from pyspark.sql import DataFrame, SparkSession, functions as F
from pyspark.sql.types import BooleanType, StringType

from ecosort.class_map import is_recyclable, normalize_class
from ecosort.config import Settings, get_settings
from ecosort.storage import ensure_buckets, upload_directory


def create_spark(settings: Settings | None = None, app_name: str = "EcoSort") -> SparkSession:
    settings = settings or get_settings()
    builder = (
        SparkSession.builder.appName(app_name)
        .master(settings.spark_master)
        .config("spark.driver.memory", settings.spark_driver_memory)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()


def _read_if_exists(spark: SparkSession, path: Path) -> DataFrame | None:
    if path.exists() and any(path.rglob("*.parquet")):
        return spark.read.parquet(str(path))
    return None


def _normalize_df(df: DataFrame, source_type: str) -> DataFrame:
    normalize_udf = F.udf(normalize_class, StringType())
    recyclable_udf = F.udf(is_recyclable, BooleanType())

    # Garante colunas esperadas mesmo que venham apenas do batch ou do streaming.
    required_cols = {
        "image_id": None,
        "event_id": None,
        "camera_id": None,
        "class_label": None,
        "predicted_class": None,
        "class_label_normalized": None,
        "recyclable": None,
        "file_name": None,
        "source_relative_path": None,
        "image_path": None,
        "bronze_image_path": None,
        "file_size_kb": None,
        "ingestion_timestamp": None,
        "event_timestamp": None,
        "timestamp": None,
        "batch_id": None,
        "route_id": None,
        "turno_simulado": None,
        "confidence": None,
        "source_type": source_type,
    }

    for col_name, default_value in required_cols.items():
        if col_name not in df.columns:
            df = df.withColumn(col_name, F.lit(default_value))

    df = df.withColumn("source_type", F.coalesce(F.col("source_type"), F.lit(source_type)))
    df = df.withColumn("class_label", F.coalesce(F.col("class_label"), F.col("predicted_class")))
    df = df.withColumn("class_label_normalized", normalize_udf(F.col("class_label")))
    df = df.withColumn("recyclable", recyclable_udf(F.col("class_label_normalized")))
    df = df.withColumn("confidence", F.coalesce(F.col("confidence").cast("double"), F.lit(1.0)))
    df = df.withColumn("event_timestamp", F.coalesce(F.col("event_timestamp"), F.col("timestamp"), F.col("ingestion_timestamp")))
    df = df.withColumn("processed_at", F.current_timestamp())
    return df.select(
        "image_id",
        "event_id",
        "camera_id",
        "source_type",
        "class_label",
        "class_label_normalized",
        "recyclable",
        "file_name",
        "source_relative_path",
        "image_path",
        "bronze_image_path",
        "file_size_kb",
        "ingestion_timestamp",
        "event_timestamp",
        "batch_id",
        "route_id",
        "turno_simulado",
        "confidence",
        "processed_at",
    )


def build_silver_candidate(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    spark = create_spark(settings, "EcoSort Bronze to Candidate")
    try:
        batch_df = _read_if_exists(spark, settings.bronze_dir / "batch_metadata")
        stream_df = _read_if_exists(spark, settings.bronze_dir / "stream_events")

        dataframes = []
        if batch_df is not None:
            dataframes.append(_normalize_df(batch_df, "batch"))
        if stream_df is not None:
            dataframes.append(_normalize_df(stream_df, "streaming"))
        if not dataframes:
            raise RuntimeError("Nenhum Parquet Bronze encontrado para processamento.")

        result = dataframes[0]
        for df in dataframes[1:]:
            result = result.unionByName(df, allowMissingColumns=True)

        result = result.dropDuplicates(["image_id", "event_id", "class_label", "event_timestamp"])

        candidate_dir = settings.silver_dir / "_candidate" / "residuos"
        if candidate_dir.exists():
            import shutil
            shutil.rmtree(candidate_dir)
        result.write.mode("overwrite").partitionBy("class_label_normalized").parquet(str(candidate_dir))

        count = result.count()
        print(f"[spark] Silver candidate gerada com {count} registros em {candidate_dir}")
        return {"candidate_dir": str(candidate_dir), "records": count}
    finally:
        spark.stop()


def promote_candidate_to_silver(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    ensure_buckets(settings)
    spark = create_spark(settings, "EcoSort Promote Silver")
    try:
        candidate_dir = settings.silver_dir / "_candidate" / "residuos"
        if not candidate_dir.exists():
            raise RuntimeError("Silver candidate não encontrada. Execute build_silver_candidate antes.")

        df = spark.read.parquet(str(candidate_dir))
        delta_dir = settings.silver_dir / "delta" / "residuos"
        parquet_dir = settings.silver_dir / "parquet" / "residuos"

        import shutil
        for path in [delta_dir, parquet_dir]:
            if path.exists():
                shutil.rmtree(path)

        df.write.format("delta").mode("overwrite").partitionBy("class_label_normalized").save(str(delta_dir))
        df.write.mode("overwrite").partitionBy("class_label_normalized").parquet(str(parquet_dir))

        upload_directory(settings.minio_bucket_silver, "delta/residuos", delta_dir, settings)
        upload_directory(settings.minio_bucket_silver, "parquet/residuos", parquet_dir, settings)

        count = df.count()
        print(f"[spark] Silver Delta/Parquet promovida com {count} registros.")
        return {"delta_dir": str(delta_dir), "parquet_dir": str(parquet_dir), "records": count}
    finally:
        spark.stop()


if __name__ == "__main__":
    settings = get_settings()
    print(build_silver_candidate(settings))
    print(promote_candidate_to_silver(settings))
