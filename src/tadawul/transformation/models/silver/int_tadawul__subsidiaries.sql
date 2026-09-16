select
    c.symbol || '-' || c.language as company_key,
    s.name as subsidiary_name,
    s.ownership_percentage,
    s.main_business,
    s.location,
    s.country

from {{ ref('stg_tadawul__subsidiaries') }} s

inner join {{ ref('stg_tadawul__company') }} c
    on s.company_root_id = c.company_id