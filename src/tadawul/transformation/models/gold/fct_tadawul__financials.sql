select
    company_key,
    symbol,
    language,
    statement_type,
    source_type,
    period,
    metric,
    value
from {{ ref('int_tadawul__financials') }}