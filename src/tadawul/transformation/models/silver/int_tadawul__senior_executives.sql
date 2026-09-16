select
    c.symbol || '-' || c.language as company_key,
    e.name as person_name,
    e.role,
    e.classification,
    e.bd_session_start,
    e.bd_session_end,
    e.designation
from {{ ref('stg_tadawul__senior_executives') }} e
inner join {{ ref('stg_tadawul__company') }} c
    on e.company_root_id = c.company_id