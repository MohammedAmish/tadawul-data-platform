with normalized as (

    select
        split_part(company_key, '-', 1) as symbol,
        trading_date,
        person_name,

        case
            when designation in ('Board of Directors', 'أعضاء مجلس الإدارة')
                then 'Board of Directors'

            when designation in ('Senior Executives', 'كبار التنفيذيين')
                then 'Senior Executives'

            when designation in ('Chairman', 'رئيس مجلس الإدارة')
                then 'Chairman'

            else designation
        end as designation,

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

    from {{ ref('int_tadawul__board_shareholdings') }}
),

deduplicated as (

    select
        *,
        row_number() over (
            partition by
                symbol,
                trading_date,
                person_name,
                designation,
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
    designation,
    total_shares_held_trading_day,
    total_shares_held_prev_trading_day,
    total_shares_change
from deduplicated
where rn = 1