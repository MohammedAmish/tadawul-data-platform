select
    company_key,
    trading_date,
    shareholder_name,
    shareholding_type,
    is_lockup,
    designation,
    total_shares_held_trading_day,
    total_shares_held_prev_trading_day,
    total_shares_change
from {{ ref('int_tadawul__board_shareholdings') }}