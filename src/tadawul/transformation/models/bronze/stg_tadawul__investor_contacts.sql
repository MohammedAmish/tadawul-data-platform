select
    value,
    _dlt_root_id as company_root_id

from {{ source('raw_tadawul', 'raw_company__company_details_md71ngr_relations__contact_details') }}