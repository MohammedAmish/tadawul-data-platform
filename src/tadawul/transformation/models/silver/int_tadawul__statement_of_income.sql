select
    c.symbol || '-' || c.language as company_key,
    i.period,
    i.metric,
    i.value,
    i.value_double
from {{ ref('stg_tadawul__statement_of_income') }} i
inner join {{ ref('stg_tadawul__company') }} c
    on i.company_id = c.company_id

union all

select
    c.symbol || '-' || c.language as company_key,
    i.period,
    i.metric,
    i.value,
    i.value_double
from {{ ref('stg_tadawul__financial_information_statement_of_income') }} i
inner join {{ ref('stg_tadawul__company') }} c
    on i.company_id = c.company_id