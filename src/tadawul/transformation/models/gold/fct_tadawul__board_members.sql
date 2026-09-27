select
    company_key,
    person_name,
    management_type,
    role,
    classification,
    bd_session_start,
    bd_session_end,
    designation
from {{ ref('int_tadawul__board_members') }}