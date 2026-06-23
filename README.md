# EcoSort — Lakehouse Docker Ready

Implementação funcional do protótipo EcoSort, seguindo os documentos do repositório `leonardoamaral90/uniceub_ecosort_eng216` e usando a base Kaggle `sumn2u/garbage-classification-v2`.

A proposta implementada é um pipeline local em Docker Compose com:

- **Python** para ingestão batch do dataset Kaggle.
- **Apache Kafka + Zookeeper** para simulação de streaming de câmeras.
- **MinIO** como object storage local compatível com S3.
- **PySpark + Delta Lake** para processamento Bronze → Silver.
- **Great Expectations** para validação de qualidade.
- **dbt + DuckDB** para transformação analítica Silver → Gold.
- **Prefect** para orquestração do pipeline.
- **Metabase + DuckDB driver** para consumo BI.

> O dataset do Kaggle não é incluído no ZIP. O projeto baixa automaticamente a base se você colocar suas credenciais Kaggle em `kaggle/kaggle.json` ou informar `KAGGLE_USERNAME` e `KAGGLE_KEY` no `.env`.

---

## 1. Pré-requisitos

Instale:

- Docker Desktop
- Docker Compose v2
- Conta Kaggle com API Token

No Kaggle, gere o token em:

`Account → Settings → API → Create New Token`

Será baixado um arquivo chamado `kaggle.json`.

---

## 2. Como executar

### Passo 1 — configurar ambiente

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### Passo 2 — colocar credencial Kaggle

Crie a pasta `kaggle` e coloque o arquivo `kaggle.json` dentro dela:

```text
ecosort_docker_ready/
└── kaggle/
    └── kaggle.json
```

Também é possível usar variáveis no `.env`:

```env
KAGGLE_USERNAME=seu_usuario
KAGGLE_KEY=sua_chave
```

### Passo 3 — subir tudo

```bash
docker compose up --build
```

Esse comando inicia toda a stack e executa automaticamente o fluxo principal do Prefect uma vez.

---

## 3. URLs locais

| Serviço | URL | Usuário/Senha padrão |
|---|---|---|
| MinIO Console | http://localhost:9001 | `ecosort` / `ecosort123` |
| Prefect UI | http://localhost:4200 | não exige login local |
| Great Expectations Data Docs | http://localhost:8088 | não exige login |
| Metabase | http://localhost:3000 | configurar no primeiro acesso |

No Metabase, crie uma conexão DuckDB usando o caminho:

```text
/data/duckdb/ecosort.duckdb
```

Se o driver DuckDB não aparecer, aguarde o container `metabase` finalizar o download do plugin e reinicie o serviço:

```bash
docker compose restart metabase
```

---

## 4. Ordem correta de execução da arquitetura

A orquestração principal fica em `src/ecosort/orchestration/flows.py` e executa:

1. **Preparação MinIO**  
   Cria buckets `bronze`, `silver` e `gold`.

2. **Dataset Kaggle**  
   Verifica se o dataset já está em `data/raw/garbage-classification-v2`; se não estiver, baixa pelo Kaggle API.

3. **Ingestão Batch Python → Bronze**  
   Lê as subpastas por classe, gera metadados e grava Parquet na Bronze.

4. **Simulação Streaming Kafka**  
   Publica alguns eventos JSON no tópico `residuos-eventos` e consome para a Bronze.

5. **PySpark Bronze → Silver Candidate**  
   Lê metadados/eventos Bronze, normaliza, deduplica e aplica a regra reciclável/não reciclável.

6. **Great Expectations**  
   Valida colunas obrigatórias, classes esperadas, booleanos e faixa de confiança.

7. **Promoção para Silver**  
   Escreve a Silver em Delta Lake e também uma exportação Parquet para dbt/DuckDB.

8. **dbt Silver → Gold**  
   Cria modelos analíticos: totais por classe, taxa de reciclabilidade, volume por turno e série temporal.

9. **DuckDB para Metabase**  
   Consolida as tabelas Gold em `data/duckdb/ecosort.duckdb`.

10. **Upload Gold para MinIO**  
    Publica os Parquets Gold no bucket `gold`.

---

## 5. Estrutura principal

```text
.
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/gold/
├── docs/
│   ├── arquitetura-funcional.md
│   └── ordem-execucao.md
├── metabase/
│   └── Dockerfile
├── scripts/
│   ├── run_pipeline.sh
│   └── wait_for_tcp.py
└── src/ecosort/
    ├── config.py
    ├── class_map.py
    ├── storage.py
    ├── dataset.py
    ├── ingestion/
    ├── processing/
    ├── quality/
    ├── transformation/
    ├── dashboard/
    └── orchestration/
```

---

## 6. Modo amostra

Por padrão, `ECOSORT_ALLOW_SAMPLE_DATA=true` no `.env.example`. Isso permite que a stack suba mesmo sem credenciais Kaggle, gerando uma pequena amostra sintética somente para validar Docker, MinIO, Prefect, Spark, GE, dbt, DuckDB e Metabase.

Para executar obrigatoriamente com a base real do Kaggle, altere:

```env
ECOSORT_ALLOW_SAMPLE_DATA=false
```

---

## 7. Comandos úteis

Executar apenas o pipeline novamente:

```bash
docker compose run --rm pipeline
```

Executar producer contínuo de Kafka:

```bash
docker compose --profile streaming up kafka-producer
```

Executar consumer contínuo de Kafka:

```bash
docker compose --profile streaming up kafka-consumer
```

Parar e remover containers:

```bash
docker compose down
```

Limpar volumes locais de dados gerados:

```bash
rm -rf data
```

No Windows PowerShell:

```powershell
Remove-Item -Recurse -Force data
```

---

## 8. Observações importantes

- O projeto foi preparado para ser didático e executável em ambiente local.
- O Spark roda em modo `local[*]`, como previsto nos documentos do projeto.
- A camada Silver é gravada em Delta Lake e exportada também como Parquet para viabilizar dbt/DuckDB local.
- O Metabase exige o plugin comunitário DuckDB, baixado no build do container `metabase`.
- O ZIP não contém imagens do Kaggle, credenciais ou dados sensíveis.
