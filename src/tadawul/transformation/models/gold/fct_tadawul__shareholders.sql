with normalized as (

    select
        split_part(company_key, '-', 1) as symbol,
        trading_date,
        person_name,

        replace(
            trim(total_shares_held_trading_day::text),
            '%',
            ''
        )::numeric as total_shares_held_trading_day,

        replace(
            trim(total_shares_held_prev_trading_day::text),
            '%',
            ''
        )::numeric as total_shares_held_prev_trading_day,

        case
            when trim(total_shares_change::text) ~ '^[0-9.]+-$'
                then (
                    '-' ||
                    left(
                        trim(total_shares_change::text),
                        length(trim(total_shares_change::text)) - 1
                    )
                )::numeric

            else nullif(
                replace(
                    trim(total_shares_change::text),
                    '%',
                    ''
                ),
                ''
            )::numeric
        end as total_shares_change

    from {{ ref('int_tadawul__shareholders') }}
),

deduplicated as (

    select
        *,
        row_number() over (
            partition by
                symbol,
                trading_date,
                person_name,
                total_shares_held_trading_day,
                total_shares_held_prev_trading_day,
                total_shares_change
            order by symbol
        ) as rn

    from normalized
)

select
    symbol,
    trading_date,
    person_name,
    total_shares_held_trading_day,
    total_shares_held_prev_trading_day,
    total_shares_change
from deduplicated
where rn = 1