select
    name,
    role,
    classification,
    bd_session_start,
    bd_session_end,
    designation,
    _dlt_root_id as company_root_id

from {{ source('raw_tadawul', 'raw_company__management_team__senior_executives') }}