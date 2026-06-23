select
    class_label,
    recyclable,
    count(*) as total_itens,
    avg(confidence) as confianca_media,
    min(processed_at) as primeiro_processamento,
    max(processed_at) as ultimo_processamento
from {{ ref('_silver_source') }}
group by class_label, recyclable
order by total_itens desc
