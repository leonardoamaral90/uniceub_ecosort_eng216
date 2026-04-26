# EcoSort

Protótipo de ciclo de vida de engenharia de dados para classificação inteligente de resíduos urbanos.

## Objetivo

Simular uma arquitetura de dados capaz de ingerir imagens e eventos de esteiras de triagem, classificar resíduos como recicláveis ou não recicláveis, armazenar os dados em um Lakehouse com arquitetura Medalhão e disponibilizar indicadores operacionais em dashboards.

## Arquitetura

O projeto utiliza uma arquitetura Lakehouse com camadas Bronze, Silver e Gold.

- Bronze: dados brutos.
- Silver: dados limpos, classificados e validados.
- Gold: indicadores de negócio.

## Tecnologias previstas

- Python
- Apache Kafka
- MinIO
- Delta Lake ou Apache Iceberg
- PySpark
- dbt
- Prefect ou Airflow
- Great Expectations
- Metabase ou Apache Superset

## Domínio do problema

O projeto simula o backend de dados de um sistema de triagem automática instalado em esteiras de separação de resíduos. Câmeras capturam imagens dos itens em tempo real, um modelo de ML os classifica, e o pipeline de dados processa, armazena e disponibiliza os resultados para os gestores.