select
    trading_date,
    shareholder,
    designation,
    total_shares_held_trading_day,
    total_shares_held_prev_trading_day,
    total_shares_change,
    _dlt_root_id as company_id

from {{ source('raw_tadawul', 'raw_company__board_of_directors_shareholding') }}