select
    c.symbol || '-' || c.language as company_key,
    i.value as contact_value
from {{ ref('stg_tadawul__investor_contacts') }} i
inner join {{ ref('stg_tadawul__company') }} c
    on i.company_root_id = c.company_id