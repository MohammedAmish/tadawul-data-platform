select

    c.symbol || '-' || c.language as company_key,

    b.trading_date,
    b.shareholder as shareholder_name,
    'board_shareholding' as shareholding_type,
    false as is_lockup,
    b.designation,

    b.total_shares_held_trading_day,
    b.total_shares_held_prev_trading_day,
    b.total_shares_change

from {{ ref('stg_tadawul__board_shareholding') }} b

inner join {{ ref('stg_tadawul__company') }} c
    on b.company_id = c.company_id

union all

select

    c.symbol || '-' || c.language as company_key,

    s.trading_date,
    s.shareholder as shareholder_name,
    'substantial_shareholder' as shareholding_type,
    false as is_lockup,
    null as designation,

    s.total_shares_held_trading_day,
    s.total_shares_held_prev_trading_day,
    s.total_shares_change

from {{ ref('stg_tadawul__substantial_shareholders') }} s

inner join {{ ref('stg_tadawul__company') }} c
    on s.company_id = c.company_id

union all

select

    c.symbol || '-' || c.language as company_key,

    l.trading_date,
    l.shareholder as shareholder_name,
    'substantial_shareholder' as shareholding_type,
    true as is_lockup,
    null as designation,

    l.total_shares_held_trading_day,
    l.total_shares_held_prev_trading_day,
    l.total_shares_change

from {{ ref('stg_tadawul__shareholders_lockup') }} l

inner join {{ ref('stg_tadawul__company') }} c
    on l.company_id = c.company_id