select
    date_trunc('hour', cast(event_timestamp as timestamp)) as hora_evento,
    source_type,
    class_label,
    recyclable,
    count(*) as total_eventos
from {{ ref('_silver_source') }}
where event_timestamp is not null
group by hora_evento, source_type, class_label, recyclable
order by hora_evento, class_label
