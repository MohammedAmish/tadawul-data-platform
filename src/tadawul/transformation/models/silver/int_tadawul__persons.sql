select
    person_key,
    min(alias) as canonical_name

from {{ ref('tadawul_person_aliases') }}

group by person_key