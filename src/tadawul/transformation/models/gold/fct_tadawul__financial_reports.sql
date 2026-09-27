select
    company_key,
    section,
    period,
    year,
    publication_date,
    file_type,
    file_url
from {{ ref('int_tadawul__financial_reports') }}