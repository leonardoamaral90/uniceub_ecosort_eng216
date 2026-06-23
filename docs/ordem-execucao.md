# EcoSort — Ordem Correta de Execução

A ordem abaixo é a sequência real executada pelo Prefect em `ecosort_pipeline`.

## 1. Subida da infraestrutura

```bash
docker compose up --build
```

O Compose inicia:

1. Zookeeper
2. Kafka
3. MinIO
4. MinIO Init
5. Prefect Server
6. Pipeline Runner
7. GE Data Docs
8. Metabase

## 2. Pipeline de dados

### 2.1 `prepare_storage_task`

Cria os buckets:

- `bronze`
- `silver`
- `gold`

### 2.2 `batch_ingestion_task`

Executa:

```python
run_batch_ingestion()
```

Responsabilidades:

- Baixar dataset Kaggle se necessário.
- Mapear subpastas por classe.
- Gerar metadados.
- Gravar Parquet na Bronze.
- Copiar imagens para Bronze.
- Subir arquivos para MinIO.

### 2.3 `kafka_simulation_task`

Executa:

```python
produce_events()
consume_events()
```

Responsabilidades:

- Simular câmeras de esteira.
- Publicar JSON no tópico `residuos-eventos`.
- Consumir eventos e gravar Parquet na Bronze.

### 2.4 `spark_candidate_task`

Executa:

```python
build_silver_candidate()
```

Responsabilidades:

- Ler Parquets Bronze.
- Unificar batch e streaming.
- Normalizar classes.
- Calcular `recyclable`.
- Deduplicar.
- Gerar Silver Candidate.

### 2.5 `quality_gate_task`

Executa:

```python
validate_silver_candidate()
```

Responsabilidades:

- Validar colunas obrigatórias.
- Validar classes aceitas.
- Validar booleano reciclável.
- Validar confiança entre 0 e 1.
- Gerar Data Docs.

### 2.6 `promote_silver_task`

Executa:

```python
promote_candidate_to_silver()
```

Responsabilidades:

- Promover candidate para Silver Delta.
- Exportar Parquet para dbt/DuckDB.
- Publicar Silver no MinIO.

### 2.7 `dbt_gold_task`

Executa:

```python
run_dbt_gold()
```

Responsabilidades:

- Rodar `dbt build`.
- Criar tabelas Gold em DuckDB.
- Exportar Parquets Gold.
- Publicar Gold no MinIO.

## 3. Consumo

Após o pipeline:

- MinIO contém Bronze/Silver/Gold.
- Prefect UI mostra o histórico do flow.
- Great Expectations mostra a qualidade dos dados.
- Metabase pode conectar ao DuckDB em `/data/duckdb/ecosort.duckdb`.
