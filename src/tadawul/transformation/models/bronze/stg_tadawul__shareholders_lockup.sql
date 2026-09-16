select
    trading_date,
    shareholder,
    total_shares_held_trading_day,
    total_shares_held_prev_trading_day,
    total_shares_change,
    _dlt_root_id as company_root_id

from {{ source('raw_tadawul', 'raw_company__substantial_sharepdckwreholders_subject_to_lock_up') }}