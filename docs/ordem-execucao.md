# EcoSort — Ordem Correta de Execução

A ordem abaixo é a sequência real executada pelo Prefect em `ecosort_pipeline`.

## 1. Subida da infraestrutura

```bash
docker compose up --build
```

O Compose inicia os serviços na seguinte ordem, respeitando as dependências de saúde (`healthcheck`):

1. Zookeeper (`confluentinc/cp-zookeeper:7.6.0`)
2. Kafka (`confluentinc/cp-kafka:7.6.0`)
3. MinIO
4. MinIO Init (cria os buckets automaticamente)
5. Prefect Server
6. Pipeline Runner (aguarda Prefect estar saudável antes de iniciar)
7. GE Data Docs (aguarda Pipeline finalizar com sucesso)
8. Metabase (aguarda Pipeline finalizar com sucesso)

> Na primeira execução o build pode demorar 5–10 minutos por causa do download das imagens e da compilação do Java Temurin 17.

## 2. Pipeline de dados

### 2.1 `prepare_storage_task`

Cria os buckets no MinIO:
- `bronze`
- `silver`
- `gold`

### 2.2 `batch_ingestion_task`

Executa:
```python
run_batch_ingestion()
```

Responsabilidades:
- Baixar dataset Kaggle se necessário (ou gerar amostra sintética se `ECOSORT_ALLOW_SAMPLE_DATA=true`).
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

Após o pipeline concluir com sucesso (`Exited (0)`), todos os serviços de consumo estão disponíveis:

| Serviço | URL | O que mostra |
|---|---|---|
| Prefect UI | http://localhost:4200 | Histórico e status do flow |
| Great Expectations | http://localhost:8088 | Qualidade dos dados validada |
| MinIO Console | http://localhost:9001 | Arquivos Bronze, Silver e Gold |
| Metabase | http://localhost:3000 | Dashboard **EcoSort — Gestão de Resíduos** |

> O Metabase requer configuração manual no primeiro acesso. Consulte a seção 4 do README para instruções de conexão com o DuckDB e acesso ao dashboard.
