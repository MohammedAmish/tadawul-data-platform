select
    c.symbol || '-' || c.language as company_key,
    b.trading_date,
    b.shareholder as person_name,
    b.designation,
    b.total_shares_held_trading_day,
    b.total_shares_held_prev_trading_day,
    b.total_shares_change

from {{ ref('stg_tadawul__board_shareholding') }} b

inner join {{ ref('stg_tadawul__company') }} c
    on b.company_root_id = c.company_id