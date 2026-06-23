-- Helper model: lê a exportação Parquet da Silver produzida pelo PySpark.
-- Materializado como view para os modelos Gold.

select *
from read_parquet('/data/lakehouse/silver/parquet/residuos/**/*.parquet', hive_partitioning = true)
