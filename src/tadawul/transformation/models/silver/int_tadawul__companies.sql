with investor_contacts as (

    select
        company_id,

        string_agg(
            distinct nullif(
                trim(
                    regexp_replace(
                        value,
                        '^\s*(Email|بريد الالكتروني)\s*:?\s*',
                        '',
                        'i'
                    )
                ),
                '-'
            ),
            ' / '
            order by nullif(
                trim(
                    regexp_replace(
                        value,
                        '^\s*(Email|بريد الالكتروني)\s*:?\s*',
                        '',
                        'i'
                    )
                ),
                '-'
            )
        ) filter (
            where value ~* '^\s*(Email|بريد الالكتروني)\s*:?\s*'
              and nullif(
                    trim(
                        regexp_replace(
                            value,
                            '^\s*(Email|بريد الالكتروني)\s*:?\s*',
                            '',
                            'i'
                        )
                    ),
                    '-'
                  ) is not null
        ) as email,

        string_agg(
            distinct nullif(
                trim(
                    regexp_replace(
                        value,
                        '^\s*(Telephone|الهاتف)\s*:?\s*',
                        '',
                        'i'
                    )
                ),
                '-'
            ),
            ' / '
            order by nullif(
                trim(
                    regexp_replace(
                        value,
                        '^\s*(Telephone|الهاتف)\s*:?\s*',
                        '',
                        'i'
                    )
                ),
                '-'
            )
        ) filter (
            where value ~* '^\s*(Telephone|الهاتف)\s*:?\s*'
              and nullif(
                    trim(
                        regexp_replace(
                            value,
                            '^\s*(Telephone|الهاتف)\s*:?\s*',
                            '',
                            'i'
                        )
                    ),
                    '-'
                  ) is not null
        ) as phone,

        string_agg(
            distinct nullif(
                trim(
                    regexp_replace(
                        value,
                        '^\s*(Fax|فاكس)\s*:?\s*',
                        '',
                        'i'
                    )
                ),
                '-'
            ),
            ' / '
            order by nullif(
                trim(
                    regexp_replace(
                        value,
                        '^\s*(Fax|فاكس)\s*:?\s*',
                        '',
                        'i'
                    )
                ),
                '-'
            )
        ) filter (
            where value ~* '^\s*(Fax|فاكس)\s*:?\s*'
              and nullif(
                    trim(
                        regexp_replace(
                            value,
                            '^\s*(Fax|فاكس)\s*:?\s*',
                            '',
                            'i'
                        )
                    ),
                    '-'
                  ) is not null
        ) as fax

    from {{ ref('stg_tadawul__investor_contacts') }}

    group by company_id

),

subsidiaries as (

    select
        company_id,

        jsonb_agg(
            jsonb_build_object(
                'name', name,
                'ownership_percentage', ownership_percentage,
                'main_business', main_business,
                'location', location,
                'country', country
            )
            order by name
        ) as subsidiaries

    from {{ ref('stg_tadawul__subsidiaries') }}

    group by company_id

)

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

    c.foreign_ownership_investors_ownership_percent::numeric
        as foreign_ownership_investors_ownership_percent,

    c.foreign_ownership_last_updated,

    c.foreign_ownership_maximum_limit_percent::numeric
        as foreign_ownership_maximum_limit_percent,

    c.foreign_ownership_actual_percent::numeric
        as foreign_ownership_actual_percent,

    c.date_established,
    c.financial_year_end,
    c.listing_date,
    c.external_auditors,
    c.isin_code,

    nullif(c.number_of_employees, '-')::integer
        as number_of_employees,

    c.investor_relations_contact_name,
    c.investor_relations_company_address,
    c.investor_relations_company_website,

    ic.email,
    ic.phone,
    ic.fax,

    c.company_overview,
    c.company_history,
    c.company_bylaws_url,

    replace(c.authorized_capital, ',', '')::numeric
        as authorized_capital,

    replace(c.total_issued_shares, ',', '')::numeric
        as total_issued_shares,

    replace(c.paid_up_capital, ',', '')::numeric
        as paid_up_capital,

    nullif(
        replace(c.nominal_value_per_unit, ',', ''),
        '-'
    )::numeric as nominal_value_per_unit,

    nullif(
        replace(c.paid_value_per_unit, ',', ''),
        '-'
    )::numeric as paid_value_per_unit,

    coalesce(
        sub.subsidiaries,
        '[]'::jsonb
    ) as subsidiaries

from {{ ref('stg_tadawul__company') }} c

left join {{ ref('stg_tadawul__servlet') }} s
    on c.symbol = s.symbol

left join investor_contacts ic
    on c.company_id = ic.company_id

left join subsidiaries sub
    on c.company_id = sub.company_id