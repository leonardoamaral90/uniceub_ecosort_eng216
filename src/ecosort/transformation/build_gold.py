from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import duckdb

from ecosort.config import Settings, get_settings
from ecosort.storage import ensure_buckets, upload_directory

GOLD_MODELS = [
    "fct_residuos_por_classe",
    "fct_taxa_reciclabilidade",
    "fct_volume_por_turno",
    "fct_serie_temporal",
]


def run_dbt_gold(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    ensure_buckets(settings)
    settings.duckdb_path.parent.mkdir(parents=True, exist_ok=True)

    if settings.duckdb_path.exists():
        settings.duckdb_path.unlink()

    print("[dbt] Executando dbt build...")
    subprocess.run(
        ["dbt", "build", "--project-dir", "/app/dbt", "--profiles-dir", "/app/dbt"],
        check=True,
    )

    export_dir = settings.gold_dir / "parquet"
    if export_dir.exists():
        shutil.rmtree(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(settings.duckdb_path))
    try:
        for model in GOLD_MODELS:
            out_path = export_dir / f"{model}.parquet"
            con.execute(f"COPY (SELECT * FROM {model}) TO '{out_path.as_posix()}' (FORMAT PARQUET)")
    finally:
        con.close()

    upload_directory(settings.minio_bucket_gold, "parquet", export_dir, settings)
    print(f"[dbt] Gold exportada para {export_dir} e DuckDB em {settings.duckdb_path}")
    return {"duckdb_path": str(settings.duckdb_path), "gold_parquet_dir": str(export_dir), "models": GOLD_MODELS}


if __name__ == "__main__":
    print(run_dbt_gold())
