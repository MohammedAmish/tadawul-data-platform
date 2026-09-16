select
    symbol,
    company_name_en,
    company_name_ar,
    trading_name_en,
    trading_name_ar
from {{ source('raw_tadawul', 'raw_servlet') }}