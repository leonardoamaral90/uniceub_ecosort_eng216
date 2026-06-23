select
    count(*) as total_itens,
    sum(case when recyclable then 1 else 0 end) as total_reciclaveis,
    sum(case when not recyclable then 1 else 0 end) as total_nao_reciclaveis,
    round(100.0 * sum(case when recyclable then 1 else 0 end) / nullif(count(*), 0), 2) as taxa_reciclabilidade_pct
from {{ ref('_silver_source') }}
