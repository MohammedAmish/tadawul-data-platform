select
    symbol,
    language,
    company_name,
    trading_name,
    market,
    sector,
    shares_type,
    isin_code

from {{ ref('int_tadawul__companies') }}