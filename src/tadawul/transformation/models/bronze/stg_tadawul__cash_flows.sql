select
    period,
    metric,
    value,
    value__v_double as value_double,
    _dlt_root_id as company_id
from {{ source('raw_tadawul', 'raw_company__cash_flows') }}