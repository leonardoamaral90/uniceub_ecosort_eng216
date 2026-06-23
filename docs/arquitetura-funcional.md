# EcoSort — Arquitetura Funcional Docker

## Objetivo

Entregar um protótipo executável de engenharia de dados para classificar resíduos domésticos em recicláveis e não recicláveis, armazenar dados em arquitetura Lakehouse com padrão Medalhão e disponibilizar indicadores para consumo analítico.

## Fontes

1. **Batch real**: dataset Kaggle `sumn2u/garbage-classification-v2`.
2. **Streaming simulado**: eventos JSON publicados no Kafka a partir de amostras do dataset.

## Camadas

### Bronze

Camada bruta, sem regra de negócio destrutiva.

Conteúdo:

- Metadados batch em Parquet.
- Imagens originais copiadas do dataset.
- Eventos Kafka consumidos como Parquet.

Destino:

- Sistema local: `data/lakehouse/bronze`
- Object storage: MinIO bucket `bronze`

### Silver

Camada limpa, deduplicada e validada.

Conteúdo:

- Classe normalizada.
- Campo `recyclable` calculado.
- Confiança padronizada.
- Origem batch/streaming.
- Particionamento por classe.

Destino:

- Delta Lake: `data/lakehouse/silver/delta/residuos`
- Export Parquet para dbt/DuckDB: `data/lakehouse/silver/parquet/residuos`
- MinIO bucket `silver`

### Gold

Camada de indicadores de negócio.

Modelos:

- `fct_residuos_por_classe`
- `fct_taxa_reciclabilidade`
- `fct_volume_por_turno`
- `fct_serie_temporal`

Destino:

- DuckDB: `data/duckdb/ecosort.duckdb`
- Parquet: `data/lakehouse/gold/parquet`
- MinIO bucket `gold`

## Serviços Docker

| Serviço | Papel |
|---|---|
| `zookeeper` | Coordenação do Kafka |
| `kafka` | Broker para eventos de streaming |
| `minio` | Object storage local S3-compatible |
| `minio-init` | Criação automática dos buckets |
| `prefect-server` | UI/API de orquestração |
| `pipeline` | Execução automática do fluxo principal |
| `ge-docs` | Servidor estático dos Data Docs |
| `metabase` | Dashboard BI com driver DuckDB |
| `kafka-producer` | Producer opcional contínuo |
| `kafka-consumer` | Consumer opcional contínuo |

## Regras de classificação

Recicláveis:

- Metal
- Glass
- Paper
- Cardboard
- Plastic

Não recicláveis no protótipo:

- Biological
- Battery
- Trash
- Shoes
- Clothes

> Baterias são tratadas como não recicláveis no fluxo simplificado, embora na prática exijam descarte especial.
