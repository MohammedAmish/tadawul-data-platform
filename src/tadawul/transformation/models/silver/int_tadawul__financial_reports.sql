select
    c.symbol || '-' || c.language as company_key,
    r.section,
    r.period,
    r.year,
    r.publication_date,
    r.file_type,
    r.file_url
from {{ ref('stg_tadawul__financial_reports') }} r
inner join {{ ref('stg_tadawul__company') }} c
    on r.company_root_id = c.company_id