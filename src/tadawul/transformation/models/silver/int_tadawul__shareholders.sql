select
    c.symbol || '-' || c.language as company_key,
    s.trading_date,
    s.shareholder as person_name,
    s.total_shares_held_trading_day,
    s.total_shares_held_prev_trading_day,
    s.total_shares_change

from {{ ref('stg_tadawul__substantial_shareholders') }} s

inner join {{ ref('stg_tadawul__company') }} c
    on s.company_root_id = c.company_id