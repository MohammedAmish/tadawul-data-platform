with companies as (

    select *
    from {{ ref('int_tadawul__companies') }}

),

latest_financials as (

    select
        symbol,
        period,

        max(
            case
                when statement_type = 'balance_sheet'
                 and metric = 'total_assets'
                then metric_value
            end
        ) as total_assets,

        max(
            case
                when statement_type = 'balance_sheet'
                 and metric = 'total_liabilities'
                then metric_value
            end
        ) as total_liabilities,

        max(
            case
                when statement_type = 'balance_sheet'
                 and metric = 'shareholders_equity'
                then metric_value
            end
        ) as shareholders_equity,

        max(
            case
                when statement_type = 'statement_of_income'
                 and metric = 'total_revenues'
                then metric_value
            end
        ) as total_revenues,

        max(
            case
                when statement_type = 'statement_of_income'
                 and metric = 'net_income'
                then metric_value
            end
        ) as net_income,

        max(
            case
                when statement_type = 'statement_of_income'
                 and metric = 'earnings_per_share'
                then metric_value
            end
        ) as earnings_per_share

    from {{ ref('fct_tadawul__financials') }}

    group by
        symbol,
        period

),

latest_period as (

    select
        symbol,
        max(period) as latest_financial_period
    from latest_financials
    group by symbol

)

select

    -- ============================================================
    -- Company identity
    -- ============================================================

    c.symbol || '-' || c.language as company_key,

    c.symbol,
    c.language,
    c.company_name,
    c.trading_name,
    c.market,
    c.sector,
    c.shares_type,
    c.isin_code,

    -- ============================================================
    -- Company details
    -- ============================================================

    c.date_established,
    c.financial_year_end,
    c.listing_date,
    c.external_auditors,
    c.number_of_employees,

    -- ============================================================
    -- Investor relations
    -- ============================================================

    c.investor_relations_contact_name,
    c.investor_relations_company_address,
    c.investor_relations_company_website,

    -- ============================================================
    -- Company profile
    -- ============================================================

    c.company_overview,
    c.company_history,
    c.company_bylaws_url,

    -- ============================================================
    -- Capital information
    -- ============================================================

    c.authorized_capital,
    c.total_issued_shares,
    c.paid_up_capital,
    c.nominal_value_per_unit,
    c.paid_value_per_unit,

    -- ============================================================
    -- Foreign ownership
    -- ============================================================

    c.foreign_ownership_investors_ownership_percent,
    c.foreign_ownership_maximum_limit_percent,
    c.foreign_ownership_actual_percent,
    c.foreign_ownership_last_updated,

    -- ============================================================
    -- Latest financial indicators
    -- Shared between Arabic and English pages
    -- ============================================================

    f.period as latest_financial_period,
    f.total_assets,
    f.total_liabilities,
    f.shareholders_equity,
    f.total_revenues,
    f.net_income,
    f.earnings_per_share,

    -- ============================================================
    -- Board of directors
    -- Language-specific because names come from the page language
    -- ============================================================

    coalesce(
        (
            select jsonb_agg(
                jsonb_build_object(
                    'name', b.person_name,
                    'role', b.role,
                    'classification', b.classification,
                    'session_start', b.bd_session_start,
                    'session_end', b.bd_session_end,
                    'designation', b.designation
                )
                order by b.person_name
            )
            from {{ ref('int_tadawul__board_members') }} b
            where b.company_key = c.symbol || '-' || c.language
        ),
        '[]'::jsonb
    ) as board_members,

    -- ============================================================
    -- Senior executives
    -- Language-specific
    -- ============================================================

    coalesce(
        (
            select jsonb_agg(
                jsonb_build_object(
                    'name', e.person_name,
                    'role', e.role,
                    'classification', e.classification,
                    'session_start', e.bd_session_start,
                    'session_end', e.bd_session_end,
                    'designation', e.designation
                )
                order by e.person_name
            )
            from {{ ref('int_tadawul__senior_executives') }} e
            where e.company_key = c.symbol || '-' || c.language
        ),
        '[]'::jsonb
    ) as senior_executives,

    -- ============================================================
    -- Subsidiaries
    -- Language-specific source data
    -- ============================================================

    coalesce(
        (
            select jsonb_agg(
                jsonb_build_object(
                    'name', s.subsidiary_name,
                    'ownership_percentage', s.ownership_percentage,
                    'main_business', s.main_business,
                    'location', s.location,
                    'country', s.country
                )
                order by s.subsidiary_name
            )
            from {{ ref('int_tadawul__subsidiaries') }} s
            where s.company_key = c.symbol || '-' || c.language
        ),
        '[]'::jsonb
    ) as subsidiaries,

    -- ============================================================
    -- Financial reports
    -- Language-specific page/report information
    -- ============================================================

    coalesce(
        (
            select jsonb_agg(
                jsonb_build_object(
                    'section', r.section,
                    'period', r.period,
                    'year', r.year,
                    'publication_date', r.publication_date,
                    'file_type', r.file_type,
                    'file_url', r.file_url
                )
                order by r.publication_date desc nulls last
            )
            from {{ ref('int_tadawul__financial_reports') }} r
            where r.company_key = c.symbol || '-' || c.language
        ),
        '[]'::jsonb
    ) as financial_reports,

    -- ============================================================
    -- Investor contacts
    -- Language-specific
    -- ============================================================

    coalesce(
        (
            select jsonb_agg(
                jsonb_build_object(
                    'value', i.contact_value
                )
                order by i.contact_value
            )
            from {{ ref('int_tadawul__investor_contacts') }} i
            where i.company_key = c.symbol || '-' || c.language
        ),
        '[]'::jsonb
    ) as investor_contacts,

    -- ============================================================
    -- Board shareholdings
    -- Shared numeric facts
    -- ============================================================

    coalesce(
        (
            select jsonb_agg(
                jsonb_build_object(
                    'trading_date', sh.trading_date,
                    'person_name', sh.person_name,
                    'designation', sh.designation,
                    'total_shares_held_trading_day',
                        sh.total_shares_held_trading_day,
                    'total_shares_held_prev_trading_day',
                        sh.total_shares_held_prev_trading_day,
                    'total_shares_change',
                        sh.total_shares_change
                )
                order by sh.trading_date desc, sh.person_name
            )
            from {{ ref('fct_tadawul__shareholdings') }} sh
            where sh.symbol = c.symbol
        ),
        '[]'::jsonb
    ) as board_shareholdings,

    -- ============================================================
    -- Substantial shareholders
    -- Shared numeric facts
    -- ============================================================

    coalesce(
        (
            select jsonb_agg(
                jsonb_build_object(
                    'trading_date', s.trading_date,
                    'person_name', s.person_name,
                    'total_shares_held_trading_day',
                        s.total_shares_held_trading_day,
                    'total_shares_held_prev_trading_day',
                        s.total_shares_held_prev_trading_day,
                    'total_shares_change',
                        s.total_shares_change
                )
                order by s.trading_date desc, s.person_name
            )
            from {{ ref('fct_tadawul__shareholders') }} s
            where s.symbol = c.symbol
        ),
        '[]'::jsonb
    ) as substantial_shareholders,

    -- ============================================================
    -- Lock-up shareholders
    -- Shared numeric facts, but source names may be localized
    -- ============================================================

    coalesce(
        (
            select jsonb_agg(
                jsonb_build_object(
                    'trading_date', l.trading_date,
                    'person_name', l.person_name,
                    'total_shares_held_trading_day',
                        l.total_shares_held_trading_day,
                    'total_shares_held_prev_trading_day',
                        l.total_shares_held_prev_trading_day,
                    'total_shares_change',
                        l.total_shares_change
                )
                order by l.trading_date desc, l.person_name
            )
            from {{ ref('int_tadawul__shareholders_lockup') }} l
            where l.company_key = c.symbol || '-' || c.language
        ),
        '[]'::jsonb
    ) as shareholders_lockup

from companies c

left join latest_period lp
    on c.symbol = lp.symbol

left join latest_financials f
    on lp.symbol = f.symbol
    and lp.latest_financial_period = f.period