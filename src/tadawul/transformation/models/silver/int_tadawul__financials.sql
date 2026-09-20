select
    c.symbol || '-' || c.language as company_key,
    c.symbol,
    c.language,
    'balance_sheet' as statement_type,
    'detailed' as source_type,
    b.period,
    b.metric,
    coalesce(b.value::numeric, b.value_double::numeric) as value
from {{ ref('stg_tadawul__balance_sheet') }} b
inner join {{ ref('stg_tadawul__company') }} c
    on b.company_id = c.company_id

union all

select
    c.symbol || '-' || c.language as company_key,
    c.symbol,
    c.language,
    'balance_sheet' as statement_type,
    'financial_information' as source_type,
    b.period,
    b.metric,
    coalesce(b.value::numeric, b.value_double::numeric) as value
from {{ ref('stg_tadawul__financial_information_balance_sheet') }} b
inner join {{ ref('stg_tadawul__company') }} c
    on b.company_id = c.company_id

union all

select
    c.symbol || '-' || c.language as company_key,
    c.symbol,
    c.language,
    'statement_of_income' as statement_type,
    'detailed' as source_type,
    i.period,
    i.metric,
    coalesce(i.value::numeric, i.value_double::numeric) as value
from {{ ref('stg_tadawul__statement_of_income') }} i
inner join {{ ref('stg_tadawul__company') }} c
    on i.company_id = c.company_id

union all

select
    c.symbol || '-' || c.language as company_key,
    c.symbol,
    c.language,
    'statement_of_income' as statement_type,
    'financial_information' as source_type,
    i.period,
    i.metric,
    coalesce(i.value::numeric, i.value_double::numeric) as value
from {{ ref('stg_tadawul__financial_information_statement_of_income') }} i
inner join {{ ref('stg_tadawul__company') }} c
    on i.company_id = c.company_id

union all

select
    c.symbol || '-' || c.language as company_key,
    c.symbol,
    c.language,
    'cash_flows' as statement_type,
    'detailed' as source_type,
    cf.period,
    cf.metric,
    coalesce(cf.value::numeric, cf.value_double::numeric) as value
from {{ ref('stg_tadawul__cash_flows') }} cf
inner join {{ ref('stg_tadawul__company') }} c
    on cf.company_id = c.company_id

union all

select
    c.symbol || '-' || c.language as company_key,
    c.symbol,
    c.language,
    'cash_flows' as statement_type,
    'financial_information' as source_type,
    cf.period,
    cf.metric,
    coalesce(cf.value::numeric, cf.value_double::numeric) as value
from {{ ref('stg_tadawul__company') }} c
inner join {{ ref('stg_tadawul__financial_information_cash_flows') }} cf
    on cf.company_id = c.company_id