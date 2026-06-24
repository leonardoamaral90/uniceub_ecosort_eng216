# EcoSort — Lakehouse Docker Ready

Implementação funcional do protótipo EcoSort, seguindo os documentos do repositório `leonardoamaral90/uniceub_ecosort_eng216` e usando a base Kaggle `sumn2u/garbage-classification-v2`.

A proposta implementada é um pipeline local em Docker Compose com:

- **Python** para ingestão batch do dataset Kaggle.
- **Apache Kafka + Zookeeper** (Confluent Platform 7.6.0) para simulação de streaming de câmeras.
- **MinIO** como object storage local compatível com S3.
- **PySpark + Delta Lake** para processamento Bronze → Silver.
- **Great Expectations** para validação de qualidade.
- **dbt + DuckDB** para transformação analítica Silver → Gold.
- **Prefect** para orquestração do pipeline.
- **Metabase v0.50.36 + DuckDB driver** para consumo BI.

> O dataset do Kaggle não é incluído no repositório. O projeto baixa automaticamente a base se você colocar suas credenciais Kaggle em `kaggle/kaggle.json` ou informar `KAGGLE_USERNAME` e `KAGGLE_KEY` no `.env`.

---

## 1. Pré-requisitos

Instale:

- Docker Desktop (versão 24+)
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
uniceub_ecosort_eng216/
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

> Na primeira execução o build pode demorar 5–10 minutos, pois baixa as imagens do Kafka, MinIO, Metabase e compila o Java (Temurin 17).

---

## 3. URLs locais

| Serviço | URL | Usuário/Senha padrão |
|---|---|---|
| MinIO Console | http://localhost:9001 | `ecosort` / `ecosort123` |
| Prefect UI | http://localhost:4200 | não exige login local |
| Great Expectations Data Docs | http://localhost:8088 | não exige login |
| Metabase | http://localhost:3000 | configurar no primeiro acesso |

---

## 4. Configurando o dashboard no Metabase

O Metabase requer configuração manual no primeiro acesso:

### 4.1 — Criar conta

Acesse http://localhost:3000 e clique em **Let's get started**. Preencha nome, e-mail e senha (podem ser fictícios para uso local).

### 4.2 — Conectar o DuckDB

Na etapa **Add your data**, selecione **DuckDB** e preencha:

| Campo | Valor |
|---|---|
| Display name | `EcoSort` |
| Database file | `/data/duckdb/ecosort.duckdb` |

Clique em **Connect database**.

> Se o driver DuckDB não aparecer na lista, aguarde o container finalizar o download do plugin (pode levar 1–2 minutos) e recarregue a página.

### 4.3 — Dashboard de Gestão de Resíduos

Após conectar o banco, acesse **Our analytics** e abra o dashboard **EcoSort — Gestão de Resíduos**, que exibe:

- **Taxa de Reciclabilidade** — percentual geral de itens recicláveis
- **Total de Itens Processados** — volume total classificado
- **Total de Recicláveis** — contagem de itens recicláveis
- **Volume por Turno** — distribuição de resíduos por turno (Manhã, Tarde, Noite)
- **Resíduos por Classe** — quantidade por categoria de resíduo
- **Série Temporal** — evolução dos eventos ao longo do tempo

---

## 5. Ordem correta de execução da arquitetura

A orquestração principal fica em `src/ecosort/orchestration/flows.py` e executa:

1. **Preparação MinIO** — cria buckets `bronze`, `silver` e `gold`.
2. **Dataset Kaggle** — verifica se o dataset já está em `data/raw/garbage-classification-v2`; se não estiver, baixa pelo Kaggle API.
3. **Ingestão Batch Python → Bronze** — lê as subpastas por classe, gera metadados e grava Parquet na Bronze.
4. **Simulação Streaming Kafka** — publica eventos JSON no tópico `residuos-eventos` e consome para a Bronze.
5. **PySpark Bronze → Silver Candidate** — normaliza, deduplica e aplica a regra reciclável/não reciclável.
6. **Great Expectations** — valida colunas obrigatórias, classes esperadas, booleanos e faixa de confiança.
7. **Promoção para Silver** — escreve a Silver em Delta Lake e exporta Parquet para dbt/DuckDB.
8. **dbt Silver → Gold** — cria modelos analíticos: totais por classe, taxa de reciclabilidade, volume por turno e série temporal.
9. **DuckDB para Metabase** — consolida as tabelas Gold em `data/duckdb/ecosort.duckdb`.
10. **Upload Gold para MinIO** — publica os Parquets Gold no bucket `gold`.

---

## 6. Estrutura principal

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

## 7. Modo amostra

Por padrão, `ECOSORT_ALLOW_SAMPLE_DATA=true` no `.env.example`. Isso permite que a stack suba mesmo sem credenciais Kaggle, gerando uma pequena amostra sintética para validar Docker, MinIO, Prefect, Spark, GE, dbt, DuckDB e Metabase.

Para executar obrigatoriamente com a base real do Kaggle, altere:

```env
ECOSORT_ALLOW_SAMPLE_DATA=false
```

---

## 8. Comandos úteis

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

Limpar volumes e dados gerados:

```bash
docker compose down -v
rm -rf data
```

No Windows PowerShell:

```powershell
docker compose down -v
Remove-Item -Recurse -Force data
```

---

## 9. Observações importantes

- O Spark roda em modo `local[*]`, como previsto nos documentos do projeto.
- A camada Silver é gravada em Delta Lake e exportada também como Parquet para viabilizar dbt/DuckDB local.
- O Metabase utiliza a versão **v0.50.36** com o driver comunitário DuckDB 1.0.0, instalado no build do container.
- O Kafka e Zookeeper utilizam as imagens **Confluent Platform 7.6.0** (`confluentinc/cp-kafka` e `confluentinc/cp-zookeeper`).
- O Java utilizado no container do pipeline é o **Temurin 17** (Adoptium), necessário para compatibilidade com PySpark 3.5 e Delta Lake 3.2.
- O repositório não contém imagens do Kaggle, credenciais ou dados sensíveis.
