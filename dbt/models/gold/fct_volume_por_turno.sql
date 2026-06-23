select
    coalesce(turno_simulado, 'NAO_INFORMADO') as turno_simulado,
    recyclable,
    count(*) as total_itens
from {{ ref('_silver_source') }}
group by turno_simulado, recyclable
order by turno_simulado, recyclable
