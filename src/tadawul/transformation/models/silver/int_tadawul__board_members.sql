select
    coalesce(
        p.person_key,
        lower(trim(b.name))
    ) as person_key,

    c.symbol || '-' || c.language as company_key,

    b.name as person_name,
    b.role,
    b.classification,
    b.bd_session_start,
    b.bd_session_end,
    b.designation

from {{ ref('stg_tadawul__board_of_directors') }} b

inner join {{ ref('stg_tadawul__company') }} c
    on b.company_root_id = c.company_id

left join {{ ref('tadawul_person_aliases') }} p
    on b.name = p.alias