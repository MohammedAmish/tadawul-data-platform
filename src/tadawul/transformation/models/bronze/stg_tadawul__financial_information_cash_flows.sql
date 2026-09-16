select
    period,
    metric,
    value,
    _dlt_root_id as company_id
from {{ source('raw_tadawul', 'raw_company__financial_information__cash_flows') }}