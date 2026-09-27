select
    company_key,
    symbol,
    language,
    company_id,

    company_name,
    trading_name,

    market,
    sector,
    shares_type,

    foreign_ownership_investors_ownership_percent,
    foreign_ownership_last_updated,
    foreign_ownership_maximum_limit_percent,
    foreign_ownership_actual_percent,

    date_established,
    financial_year_end,
    listing_date,
    external_auditors,
    isin_code,
    number_of_employees,

    investor_relations_contact_name,
    investor_relations_company_address,
    investor_relations_company_website,

    email,
    phone,
    fax,

    company_overview,
    company_history,
    company_bylaws_url,

    authorized_capital,
    total_issued_shares,
    paid_up_capital,
    nominal_value_per_unit,
    paid_value_per_unit,

    subsidiaries

from {{ ref('int_tadawul__companies') }}