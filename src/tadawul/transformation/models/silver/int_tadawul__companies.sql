select
    c.symbol || '-' || c.language as company_key,
    c.symbol,
    c.language,
    c.company_id,

    case
        when c.language = 'en' then s.company_name_en
        when c.language = 'ar' then s.company_name_ar
    end as company_name,

    case
        when c.language = 'en' then s.trading_name_en
        when c.language = 'ar' then s.trading_name_ar
    end as trading_name,

    c.market,
    c.sector,
    c.shares_type,

    cast(
        c.foreign_ownership_investors_ownership_percent as numeric
    ) as foreign_ownership_investors_ownership_percent,

    c.foreign_ownership_last_updated,

    cast(
        c.foreign_ownership_maximum_limit_percent as numeric
    ) as foreign_ownership_maximum_limit_percent,

    cast(
        c.foreign_ownership_actual_percent as numeric
    ) as foreign_ownership_actual_percent,

    c.date_established,
    c.financial_year_end,
    c.listing_date,
    c.external_auditors,
    c.isin_code,

    cast(
        nullif(c.number_of_employees, '-') as integer
    ) as number_of_employees,

    c.investor_relations_contact_name,
    c.investor_relations_company_address,
    c.investor_relations_company_website,

    c.company_overview,
    c.company_history,
    c.company_bylaws_url,

    cast(
        replace(c.authorized_capital, ',', '') as numeric
    ) as authorized_capital,

    cast(
        replace(c.total_issued_shares, ',', '') as numeric
    ) as total_issued_shares,

    cast(
        replace(c.paid_up_capital, ',', '') as numeric
    ) as paid_up_capital,

    cast(
        nullif(replace(c.nominal_value_per_unit, ',', ''), '-') as numeric
    ) as nominal_value_per_unit,

    cast(
        nullif(replace(c.paid_value_per_unit, ',', ''), '-') as numeric
    ) as paid_value_per_unit

from {{ ref('stg_tadawul__company') }} c

left join {{ ref('stg_tadawul__servlet') }} s
    on c.symbol = s.symbol