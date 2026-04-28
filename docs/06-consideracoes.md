# 06 — Considerações Finais

## Principais Riscos e Limitações
| Risco / Limitação | Impacto | Mitigação |
|---|---|---|
| Recursos de máquina | Kafka + Spark + Prefect + MinIO + Metabase rodando juntos pode ser pesado | Usar Spark em modo `local[2]`; desligar serviços não necessários durante testes; Prefect é mais leve e já está escolhido |
| Kafka em ambiente local | Configuração com Zookeeper pode apresentar instabilidades | Usar imagem `bitnami/kafka`; considerar substituir por Redpanda (mais leve, compatível com API Kafka) se necessário |
| Great Expectations + Spark | A integração entre GE e PySpark exige configuração adicional | Usar GE em modo Pandas (após coletar uma amostra) como alternativa mais simples |
| Metabase com Parquet/Delta | A versão open-source do Metabase não lê Parquet diretamente | Usar DuckDB como camada intermediária entre os arquivos Gold e o Metabase |
| Dados sintéticos | O streaming é simulado — o projeto não valida o comportamento com câmeras reais | Documentado explicitamente; o foco é o pipeline de dados, não o hardware |

---
## Próximos Passos — Parte 2 (Implementação)
1. Infraestrutura: Criar o `docker-compose.yml` com todos os serviços
2. Ingestão Batch: Implementar o script Python → Bronze (MinIO)
3. Streaming: Implementar Producer Kafka e Consumer → Bronze
4. Processamento: Implementar job PySpark (Bronze → Silver) com classificação
5. Qualidade: Configurar as expectativas no Great Expectations
6. Transformação: Criar modelos dbt (Silver → Gold) com testes de qualidade
7. Orquestração: Criar flows no Prefect conectando todas as etapas
8. Consumo: Configurar dashboards no Metabase + implementar API REST
9. Monitoramento: Validar Prefect UI e GE Data Docs em execução real; avaliar adição do Grafana + Prometheus para métricas de infraestrutura
10. Validação: Executar o pipeline ponta a ponta e documentar os resultados

## Referências
- REIS, Joe; HOUSLEY, Matt. *Fundamentals of Data Engineering*. O'Reilly Media, 2022.
- DEHGHANI, Zhamak. *Data Mesh: Delivering Data-Driven Value at Scale*. O'Reilly Media, 2022.
- Apache Kafka Documentation. Disponível em: https://kafka.apache.org/documentation/
- Apache Spark / PySpark Documentation. Disponível em: https://spark.apache.org/docs/latest/
- Delta Lake Documentation. Disponível em: https://docs.delta.io/
- dbt Documentation. Disponível em: https://docs.getdbt.com/
- Great Expectations Documentation. Disponível em: https://docs.greatexpectations.io/
- Prefect Documentation. Disponível em: https://docs.prefect.io/
- MinIO Documentation. Disponível em: https://min.io/docs/
- Grafana Documentation. Disponível em: https://grafana.com/docs/
- Metabase Documentation. Disponível em: https://www.metabase.com/docs/
- Garbage Dataset — Kaggle. Disponível em: https://www.kaggle.com/datasets/mostafaabla/garbage-classification
- KUMAR, Anil et al. *Managing Household Waste Through Transfer Learning*. 2023.