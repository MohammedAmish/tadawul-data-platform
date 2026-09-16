select
    person_key,
    canonical_name
from {{ ref('int_tadawul__persons') }}