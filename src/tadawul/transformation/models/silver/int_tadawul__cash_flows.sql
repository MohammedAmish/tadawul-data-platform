select
    c.symbol || '-' || c.language as company_key,
    cf.period,
    cf.metric,
    cf.value,
    null as value_double
from {{ ref('stg_tadawul__cash_flows') }} cf
inner join {{ ref('stg_tadawul__company') }} c
    on cf.company_id = c.company_id

union all

select
    c.symbol || '-' || c.language as company_key,
    cf.period,
    cf.metric,
    cf.value,
    null as value_double
from {{ ref('stg_tadawul__financial_information_cash_flows') }} cf
inner join {{ ref('stg_tadawul__company') }} c
    on cf.company_id = c.company_id