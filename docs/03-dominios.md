# 03 — Domínios e Serviços

## Domínios de Negócio

O projeto é organizado em três domínios principais, refletindo o fluxo ponta a ponta do pipeline:

---

### 1. Domínio de Ingestão

Responsabilidade: Capturar e registrar todos os dados de entrada — acervo histórico de imagens (batch) e eventos simulados das câmeras (streaming).

| Serviço | Responsabilidade |
|---|---|
| `batch-ingestion-service` | Lê as imagens do Garbage Dataset, gera metadados sintéticos e persiste na camada Bronze |
| `stream-producer-service` | Simula câmeras de esteira publicando eventos JSON no Kafka |
| `kafka-consumer-service` | Consome o tópico `residuos-eventos` e persiste os eventos na camada Bronze |

---

### 2. Domínio de Classificação e Qualidade

Responsabilidade: Processar os dados brutos, garantir qualidade, aplicar as regras de negócio e transformar os dados para Silver e Gold.

| Serviço | Responsabilidade |
|---|---|
| `spark-processing-service` | Lê a Bronze, executa limpeza e deduplicação via PySpark |
| `classification-service` | Aplica a regra de negócio: `class_label` → `recyclable` (booleano) |
| `quality-service` | Valida os dados com Great Expectations antes de promover para Silver |
| `dbt-transformation-service` | Gera os modelos analíticos na camada Gold (agregações de negócio) |

---

### 3. Domínio de Consumo

Responsabilidade: Disponibilizar os dados processados para usuários finais e sistemas externos.

| Serviço | Responsabilidade |
|---|---|
| `dashboard-service` | Conecta a camada Gold ao Metabase para visualização pelos gestores |
| `api-service` | Expõe os indicadores Gold via API REST para integração com sistemas externos |
| `monitoring-service` | Monitora a saúde do pipeline (Prefect UI + logs) |

---

### Serviços Compartilhados

| Serviço | Usado por |
|---|---|
| `storage-service` (MinIO) | Todos os domínios — armazena Bronze, Silver e Gold |
| `orchestration-service` (Prefect) | Ingestão e Classificação — agenda e monitora os jobs |

---

## Diagrama de Domínios e Serviços

```mermaid
graph TD
    subgraph Ingestão
        A1[batch-ingestion-service]
        A2[stream-producer-service]
        A3[kafka-consumer-service]
    end

    subgraph Classificação e Qualidade
        B1[spark-processing-service]
        B2[classification-service]
        B3[quality-service\nGreat Expectations]
        B4[dbt-transformation-service]
    end

    subgraph Consumo
        C1[dashboard-service\nMetabase]
        C2[api-service\nAPI REST]
        C3[monitoring-service]
    end

    subgraph Compartilhados
        S1[(MinIO\nBronze · Silver · Gold)]
        S2[Prefect\norquestração]
    end

    A1 -->|Bronze| S1
    A2 --> A3
    A3 -->|Bronze| S1
    S1 --> B1
    B1 --> B2
    B2 --> B3
    B3 -->|Silver| S1
    S1 --> B4
    B4 -->|Gold| S1
    S1 --> C1
    S1 --> C2
    S2 -.->|agenda| A1
    S2 -.->|agenda| B1
    S2 -.->|agenda| B4
    C3 -.->|monitora| S2
```

---

## Fluxo entre Domínios

```mermaid
flowchart LR
    subgraph Fontes Externas
        F1[Garbage Dataset]
        F2[Câmera Simulada]
    end

    subgraph Ingestão
        D1[Batch Ingestion]
        D2[Stream Producer → Kafka]
    end

    subgraph Classificação e Qualidade
        E1[PySpark\nProcessamento]
        E2[Great Expectations\nQualidade]
        E3[dbt\nAgregações Gold]
    end

    subgraph Consumo
        G1[Metabase\nDashboard]
        G2[API REST]
    end

    F1 --> D1
    F2 --> D2
    D1 -->|Bronze| E1
    D2 -->|Bronze| E1
    E1 --> E2
    E2 -->|Silver| E3
    E3 -->|Gold| G1
    E3 -->|Gold| G2
```