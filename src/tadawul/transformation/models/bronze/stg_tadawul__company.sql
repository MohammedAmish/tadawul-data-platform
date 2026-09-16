select
    _dlt_id as company_id,
    symbol,
    company_name,
    language,
    market,
    sector,
    shares_type,

    foreign_ownership__foreign_sthndtma_investors_ownership_percent
        as foreign_ownership_investors_ownership_percent,

    foreign_ownership__last_updated
        as foreign_ownership_last_updated,

    foreign_ownership__total_foreu7gftarship__maximum_limit_percent
        as foreign_ownership_maximum_limit_percent,

    foreign_ownership__total_foreign_ownership__actual_percent
        as foreign_ownership_actual_percent,

    company_details__date_established
        as date_established,

    company_details__financial_year_end
        as financial_year_end,

    company_details__listing_date
        as listing_date,

    company_details__external_auditors
        as external_auditors,

    company_details__isin_code
        as isin_code,

    company_details__number_of_employees
        as number_of_employees,

    company_details__investor_relations__contact_name
        as investor_relations_contact_name,

    company_details__investor_relations__company_address
        as investor_relations_company_address,

    company_details__investor_relations__company_website
        as investor_relations_company_website,

    company_profile__company_overview
        as company_overview,

    company_profile__company_history
        as company_history,

    company_profile__company_bylaws_url
        as company_bylaws_url,

    company_profile__authorized_capital
        as authorized_capital,

    company_profile__total_issued_shares
        as total_issued_shares,

    company_profile__paid_up_capital
        as paid_up_capital,

    company_profile__nominal_value_per_unit
        as nominal_value_per_unit,

    company_profile__paid_value_per_unit
        as paid_value_per_unit

from {{ source('raw_tadawul', 'raw_company') }}