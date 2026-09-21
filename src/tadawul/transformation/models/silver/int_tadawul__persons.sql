select
    md5(normalized_name) as person_key,
    normalized_name as person_name

from {{ ref('tadawul_person_aliases') }}

where normalized_name is not null

group by normalized_name