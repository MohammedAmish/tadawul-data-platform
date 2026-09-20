select
    section,
    period,
    year,
    publication_date,
    file_type,
    file_url,
    _dlt_root_id as company_id

from {{ source('raw_tadawul', 'raw_company__financial_statements_and_reports') }}