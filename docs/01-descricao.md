# 01 — Descrição do Projeto

## Nome do Projeto

EcoSort — Protótipo de Ciclo de Vida de Engenharia de Dados para Classificação Inteligente de Resíduos Urbanos

---

## Contexto de Negócio

A gestão inadequada de resíduos sólidos é um dos grandes desafios ambientais e operacionais de municípios brasileiros. A triagem manual em cooperativas e aterros é lenta, sujeita a erros e cara. A automação desse processo, por meio de visão computacional e engenharia de dados, pode aumentar a taxa de recuperação de recicláveis e reduzir o volume destinado a aterros.

O EcoSort simula o backend de dados de um sistema de triagem automática instalado em esteiras de separação de resíduos. Câmeras capturam imagens dos itens em tempo real, um modelo de ML os classifica, e o pipeline de dados processa, armazena e disponibiliza os resultados para os gestores.

---

## Problema que o Projeto Pretende Resolver

> **Como classificar automaticamente resíduos domésticos em recicláveis e não recicláveis, e disponibilizar indicadores operacionais confiáveis para apoiar a gestão de coleta seletiva?**

Problemas específicos abordados:

- Ausência de dados estruturados sobre o volume e tipo de resíduos processados
- Falta de visibilidade em tempo real sobre o desempenho das esteiras de triagem
- Dificuldade em gerar relatórios consolidados para tomada de decisão gerencial

---

## Objetivos Principais

1. Construir um pipeline de ingestão batch a partir de imagens do Garbage Dataset
2. Simular um fluxo de streaming representando câmeras de esteira em operação
3. Processar e classificar cada resíduo como reciclável ou não reciclável via PySpark
4. Garantir qualidade dos dados com Great Expectations
5. Armazenar os dados em um Lakehouse com arquitetura Medalhão (Bronze → Silver → Gold)
6. Disponibilizar indicadores operacionais via Metabase (com DuckDB como camada intermediária)

---

## Classificação Reciclável × Não Reciclável

A partir das 10 classes do Garbage Dataset:

| Classe | Quantidade | Classificação |
|---|---|---|
| Metal | 930 | Reciclável |
| Glass | 1.736 | Reciclável |
| Paper | 1.336 | Reciclável |
| Cardboard | 1.411 | Reciclável |
| Plastic | 1.597 | Reciclável |
| Biological | 699 | Não Reciclável |
| Battery | 756 | Não Reciclável |
| Trash | 453 | Não Reciclável |
| Shoes | 1.449 | Não Reciclável |
| Clothes | 1.892 | Não Reciclável |
| **Total** | **12.259** | — |

> **Nota:** Baterias possuem descarte especial na prática, mas para simplificação do protótipo são tratadas como não recicláveis no fluxo padrão.

---

## Principais Stakeholders / Usuários Finais

| Stakeholder | Domínio | Interesse nos Dados |
|---|---|---|
| Secretários / Gestores municipais | Gestão Municipal | Indicadores executivos de reciclabilidade e metas |
| Coordenadores de rota | Coleta Seletiva | Volume reciclável por rota e frequência de coleta |
| Operadores de esteira | Triagem e Separação | Classificação em tempo real e alertas de anomalia |
| Analistas ambientais | Meio Ambiente e Sustentabilidade | Série histórica, taxa de reciclabilidade e relatórios de impacto |
| Equipe de TI / Engenharia | Transversal | Saúde do pipeline e qualidade dos dados |
