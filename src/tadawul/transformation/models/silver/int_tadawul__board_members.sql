select
    c.symbol || '-' || c.language as company_key,

    b.name as person_name,
    'board_of_directors' as management_type,
    b.role,
    b.classification,
    b.bd_session_start,
    b.bd_session_end,
    b.designation

from {{ ref('stg_tadawul__board_of_directors') }} b

inner join {{ ref('stg_tadawul__company') }} c
    on b.company_id = c.company_id

union all

select
    c.symbol || '-' || c.language as company_key,

    e.name as person_name,
    'senior_executive' as management_type,
    e.role,
    e.classification,
    e.bd_session_start,
    e.bd_session_end,
    e.designation

from {{ ref('stg_tadawul__senior_executives') }} e

inner join {{ ref('stg_tadawul__company') }} c
    on e.company_id = c.company_id