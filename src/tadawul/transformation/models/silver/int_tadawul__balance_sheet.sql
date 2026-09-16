select
    c.symbol || '-' || c.language as company_key,
    b.period,
    b.metric,
    b.value,
    b.value_double
from {{ ref('stg_tadawul__balance_sheet') }} b
inner join {{ ref('stg_tadawul__company') }} c
    on b.company_id = c.company_id

union all

select
    c.symbol || '-' || c.language as company_key,
    b.period,
    b.metric,
    b.value,
    null as value_double
from {{ ref('stg_tadawul__financial_information_balance_sheet') }} b
inner join {{ ref('stg_tadawul__company') }} c
    on b.company_id = c.company_id