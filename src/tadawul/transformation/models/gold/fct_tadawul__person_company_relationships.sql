select distinct
    p.person_key,
    p.person_name,
    c.company_key,
    c.symbol,
    c.company_name,
    a.relationship_type,
    a.management_type,
    a.role,
    a.designation

from {{ ref('tadawul_person_aliases') }} a

inner join {{ ref('int_tadawul__persons') }} p
    on a.normalized_name = p.person_name

inner join {{ ref('dim_tadawul__companies') }} c
    on a.company_key = c.company_key

where a.normalized_name is not null
  and a.company_key is not null
  and a.relationship_type is not null