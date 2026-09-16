with companies as (

    select
        symbol,
        company_name,
        trading_name
    from {{ ref('dim_tadawul__companies') }}
    where language = 'en'

),

board_members as (

    select distinct
        person_key,
        split_part(company_key, '-', 1) as symbol
    from {{ ref('int_tadawul__board_members') }}

),

senior_executives as (

    select distinct
        person_key,
        split_part(company_key, '-', 1) as symbol
    from {{ ref('int_tadawul__senior_executives') }}

),

board_shareholdings as (

    select distinct
        person_key,
        split_part(company_key, '-', 1) as symbol
    from {{ ref('int_tadawul__board_shareholdings') }}

),

substantial_shareholders as (

    select distinct
        person_key,
        split_part(company_key, '-', 1) as symbol
    from {{ ref('int_tadawul__shareholders') }}

),

shareholders_lockup as (

    select distinct
        person_key,
        split_part(company_key, '-', 1) as symbol
    from {{ ref('int_tadawul__shareholders_lockup') }}

),

board_details as (

    select
        b.person_key,
        count(distinct b.symbol) as board_company_count,
        jsonb_agg(
            jsonb_build_object(
                'symbol', c.symbol,
                'company_name', c.company_name,
                'trading_name', c.trading_name
            )
            order by c.symbol
        ) as board_companies
    from board_members b
    inner join companies c
        on b.symbol = c.symbol
    group by b.person_key

),

senior_executive_details as (

    select
        s.person_key,
        count(distinct s.symbol) as senior_executive_company_count,
        jsonb_agg(
            jsonb_build_object(
                'symbol', c.symbol,
                'company_name', c.company_name,
                'trading_name', c.trading_name
            )
            order by c.symbol
        ) as senior_executive_companies
    from senior_executives s
    inner join companies c
        on s.symbol = c.symbol
    group by s.person_key

),

board_shareholding_details as (

    select
        b.person_key,
        count(distinct b.symbol) as board_shareholding_company_count,
        jsonb_agg(
            jsonb_build_object(
                'symbol', c.symbol,
                'company_name', c.company_name,
                'trading_name', c.trading_name
            )
            order by c.symbol
        ) as board_shareholding_companies
    from board_shareholdings b
    inner join companies c
        on b.symbol = c.symbol
    group by b.person_key

),

substantial_shareholder_details as (

    select
        s.person_key,
        count(distinct s.symbol) as substantial_shareholder_company_count,
        jsonb_agg(
            jsonb_build_object(
                'symbol', c.symbol,
                'company_name', c.company_name,
                'trading_name', c.trading_name
            )
            order by c.symbol
        ) as substantial_shareholder_companies
    from substantial_shareholders s
    inner join companies c
        on s.symbol = c.symbol
    group by s.person_key

),

lockup_details as (

    select
        l.person_key,
        count(distinct l.symbol) as lockup_company_count,
        jsonb_agg(
            jsonb_build_object(
                'symbol', c.symbol,
                'company_name', c.company_name,
                'trading_name', c.trading_name
            )
            order by c.symbol
        ) as lockup_companies
    from shareholders_lockup l
    inner join companies c
        on l.symbol = c.symbol
    group by l.person_key

),

all_relationships as (

    select person_key, symbol
    from board_members

    union

    select person_key, symbol
    from senior_executives

    union

    select person_key, symbol
    from board_shareholdings

    union

    select person_key, symbol
    from substantial_shareholders

    union

    select person_key, symbol
    from shareholders_lockup

),

all_company_details as (

    select
        ar.person_key,
        count(distinct ar.symbol) as total_company_count,
        jsonb_agg(
            jsonb_build_object(
                'symbol', c.symbol,
                'company_name', c.company_name,
                'trading_name', c.trading_name
            )
            order by c.symbol
        ) as all_companies
    from all_relationships ar
    inner join companies c
        on ar.symbol = c.symbol
    group by ar.person_key

)

select
    p.person_key,
    p.canonical_name,

    coalesce(
        bd.board_company_count,
        0
    ) as board_company_count,

    coalesce(
        bd.board_companies,
        '[]'::jsonb
    ) as board_companies,

    coalesce(
        sed.senior_executive_company_count,
        0
    ) as senior_executive_company_count,

    coalesce(
        sed.senior_executive_companies,
        '[]'::jsonb
    ) as senior_executive_companies,

    coalesce(
        bsd.board_shareholding_company_count,
        0
    ) as board_shareholding_company_count,

    coalesce(
        bsd.board_shareholding_companies,
        '[]'::jsonb
    ) as board_shareholding_companies,

    coalesce(
        ssd.substantial_shareholder_company_count,
        0
    ) as substantial_shareholder_company_count,

    coalesce(
        ssd.substantial_shareholder_companies,
        '[]'::jsonb
    ) as substantial_shareholder_companies,

    coalesce(
        ld.lockup_company_count,
        0
    ) as lockup_company_count,

    coalesce(
        ld.lockup_companies,
        '[]'::jsonb
    ) as lockup_companies,

    coalesce(
        acd.total_company_count,
        0
    ) as total_company_count,

    coalesce(
        acd.all_companies,
        '[]'::jsonb
    ) as all_companies

from {{ ref('dim_tadawul__persons') }} p

left join board_details bd
    on p.person_key = bd.person_key

left join senior_executive_details sed
    on p.person_key = sed.person_key

left join board_shareholding_details bsd
    on p.person_key = bsd.person_key

left join substantial_shareholder_details ssd
    on p.person_key = ssd.person_key

left join lockup_details ld
    on p.person_key = ld.person_key

left join all_company_details acd
    on p.person_key = acd.person_key

where coalesce(acd.total_company_count, 0) > 0