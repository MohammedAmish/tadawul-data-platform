select
    name,
    ownership_percentage,
    main_business,
    location,
    country,
    _dlt_root_id as company_root_id

from {{ source('raw_tadawul', 'raw_company__subsidiaries') }}