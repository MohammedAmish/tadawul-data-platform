with board_members as (

    select
        company_key,

        jsonb_agg(
            jsonb_build_object(
                'person_name', person_name,
                'management_type', management_type,
                'role', role,
                'classification', classification,
                'bd_session_start', bd_session_start,
                'bd_session_end', bd_session_end,
                'designation', designation
            )
            order by management_type, person_name
        ) as board_members

    from {{ ref('int_tadawul__board_members') }}

    group by company_key

),

shareholdings as (

    select
        company_key,

        jsonb_agg(
            jsonb_build_object(
                'trading_date', trading_date,
                'shareholder_name', shareholder_name,
                'shareholding_type', shareholding_type,
                'is_lockup', is_lockup,
                'designation', designation,
                'total_shares_held_trading_day',
                    total_shares_held_trading_day,
                'total_shares_held_prev_trading_day',
                    total_shares_held_prev_trading_day,
                'total_shares_change',
                    total_shares_change
            )
            order by trading_date, shareholder_name
        ) as shareholdings

    from {{ ref('int_tadawul__board_shareholdings') }}

    group by company_key

),

financial_reports as (

    select
        company_key,

        jsonb_agg(
            jsonb_build_object(
                'section', section,
                'period', period,
                'year', year,
                'publication_date', publication_date,
                'file_type', file_type,
                'file_url', file_url
            )
            order by year desc, publication_date desc
        ) as financial_reports

    from {{ ref('int_tadawul__financial_reports') }}

    group by company_key

),

financials as (

    select
        company_key,

        jsonb_agg(
            jsonb_build_object(
                'statement_type', statement_type,
                'source_type', source_type,
                'period', period,
                'metric', metric,
                'value', value
            )
            order by period desc, statement_type, source_type, metric
        ) as financials

    from {{ ref('int_tadawul__financials') }}

    group by company_key

)

select
    c.company_key,
    c.symbol,
    c.language,
    c.company_id,

    c.company_name,
    c.trading_name,

    c.market,
    c.sector,
    c.shares_type,

    c.foreign_ownership_investors_ownership_percent,
    c.foreign_ownership_last_updated,
    c.foreign_ownership_maximum_limit_percent,
    c.foreign_ownership_actual_percent,

    c.date_established,
    c.financial_year_end,
    c.listing_date,
    c.external_auditors,
    c.isin_code,
    c.number_of_employees,

    c.investor_relations_contact_name,
    c.investor_relations_company_address,
    c.investor_relations_company_website,

    c.email,
    c.phone,
    c.fax,

    c.company_overview,
    c.company_history,
    c.company_bylaws_url,

    c.authorized_capital,
    c.total_issued_shares,
    c.paid_up_capital,
    c.nominal_value_per_unit,
    c.paid_value_per_unit,

    c.subsidiaries,

    coalesce(
        bm.board_members,
        '[]'::jsonb
    ) as board_members,

    coalesce(
        sh.shareholdings,
        '[]'::jsonb
    ) as shareholdings,

    coalesce(
        fr.financial_reports,
        '[]'::jsonb
    ) as financial_reports,

    coalesce(
        f.financials,
        '[]'::jsonb
    ) as financials

from {{ ref('int_tadawul__companies') }} c

left join board_members bm
    on c.company_key = bm.company_key

left join shareholdings sh
    on c.company_key = sh.company_key

left join financial_reports fr
    on c.company_key = fr.company_key

left join financials f
    on c.company_key = f.company_key