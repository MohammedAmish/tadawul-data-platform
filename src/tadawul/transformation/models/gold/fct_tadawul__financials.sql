with financials as (

    select
        c.symbol,
        b.period,
        'balance_sheet' as statement_type,
        b.metric,
        b.value,
        b.value_double::numeric as value_double,
        c.language
    from {{ ref('int_tadawul__balance_sheet') }} b
    inner join {{ ref('stg_tadawul__company') }} c
        on b.company_key = c.symbol || '-' || c.language

    union all

    select
        c.symbol,
        i.period,
        'statement_of_income' as statement_type,
        i.metric,
        i.value,
        i.value_double::numeric as value_double,
        c.language
    from {{ ref('int_tadawul__statement_of_income') }} i
    inner join {{ ref('stg_tadawul__company') }} c
        on i.company_key = c.symbol || '-' || c.language

    union all

    select
        c.symbol,
        cf.period,
        'cash_flow' as statement_type,
        cf.metric,
        cf.value,
        cf.value_double::numeric as value_double,
        c.language
    from {{ ref('int_tadawul__cash_flows') }} cf
    inner join {{ ref('stg_tadawul__company') }} c
        on cf.company_key = c.symbol || '-' || c.language
),

mapped as (

    select
        symbol,
        period,
        statement_type,
        language,

        case

            -- Balance sheet
            when statement_type = 'balance_sheet'
                and metric = 'Total Assets'
                then 'total_assets'
            when statement_type = 'balance_sheet'
                and metric = 'إجمالي  الموجودات'
                then 'total_assets'

            when statement_type = 'balance_sheet'
                and metric = 'Total Liabilities'
                then 'total_liabilities'
            when statement_type = 'balance_sheet'
                and metric = 'إجمالي المطلوبات'
                then 'total_liabilities'

            when statement_type = 'balance_sheet'
                and metric = 'Total Liabilities and Shareholder Equity'
                then 'total_liabilities_and_shareholders_equity'
            when statement_type = 'balance_sheet'
                and metric = 'إجمالي المطلوبات و حقوق المساهمين'
                then 'total_liabilities_and_shareholders_equity'
            when statement_type = 'balance_sheet'
                and metric = 'إجمالي المطلوبات وحقوق المساهمين'
                then 'total_liabilities_and_shareholders_equity'

            when statement_type = 'balance_sheet'
                and metric = 'Current Assets'
                then 'current_assets'
            when statement_type = 'balance_sheet'
                and metric = 'الموجودات المتداولة'
                then 'current_assets'

            when statement_type = 'balance_sheet'
                and metric = 'Current Liabilities'
                then 'current_liabilities'
            when statement_type = 'balance_sheet'
                and metric = 'المطلوبات المتداولة'
                then 'current_liabilities'

            when statement_type = 'balance_sheet'
                and metric = 'Fixed Assets'
                then 'fixed_assets'
            when statement_type = 'balance_sheet'
                and metric = 'الموجودات الثابتة'
                then 'fixed_assets'

            when statement_type = 'balance_sheet'
                and metric = 'Inventory'
                then 'inventory'
            when statement_type = 'balance_sheet'
                and metric = 'المخزون'
                then 'inventory'

            when statement_type = 'balance_sheet'
                and metric = 'Investments'
                then 'investments'
            when statement_type = 'balance_sheet'
                and metric = 'الاستثمارات'
                then 'investments'

            when statement_type = 'balance_sheet'
                and metric = 'Minority Interests'
                then 'minority_interests'
            when statement_type = 'balance_sheet'
                and metric = 'حقوق الاقلية'
                then 'minority_interests'

            when statement_type = 'balance_sheet'
                and metric = 'Non-Current Liabilities'
                then 'non_current_liabilities'
            when statement_type = 'balance_sheet'
                and metric = 'المطلوبات غير المتداولة'
                then 'non_current_liabilities'

            when statement_type = 'balance_sheet'
                and metric = 'Other Assets'
                then 'other_assets'
            when statement_type = 'balance_sheet'
                and metric = 'الموجودات الأخرى'
                then 'other_assets'

            when statement_type = 'balance_sheet'
                and metric = 'Other Liabilities'
                then 'other_liabilities'
            when statement_type = 'balance_sheet'
                and metric = 'المطلوبات الأخرى'
                then 'other_liabilities'

            when statement_type = 'balance_sheet'
                and metric = 'Shareholders Equity'
                then 'shareholders_equity'
            when statement_type = 'balance_sheet'
                and metric = 'حقوق المساهمين'
                then 'shareholders_equity'

            when statement_type = 'balance_sheet'
                and metric = 'Total Shareholders Equity (After Deducting the Minority Equity)'
                then 'total_shareholders_equity_after_minority'
            when statement_type = 'balance_sheet'
                and metric = 'إجمالي حقوق الملكية (بعد استبعاد الحصص غير المسيطرة)'
                then 'total_shareholders_equity_after_minority'


            -- Income statement
            when statement_type = 'statement_of_income'
                and metric = 'Total Revenues'
                then 'total_revenues'
            when statement_type = 'statement_of_income'
                and metric = 'إجمالي الإيرادات'
                then 'total_revenues'

            when statement_type = 'statement_of_income'
                and metric = 'Total Revenue (Sales/Operating)'
                then 'total_revenues'
            when statement_type = 'statement_of_income'
                and metric = 'إجمالي الإيرادات (المبيعات/العمليات)'
                then 'total_revenues'

            when statement_type = 'statement_of_income'
                and metric = 'Total Income'
                then 'total_income'
            when statement_type = 'statement_of_income'
                and metric = 'إجمالي الدخل'
                then 'total_income'

            when statement_type = 'statement_of_income'
                and metric = 'Total Expenses'
                then 'total_expenses'
            when statement_type = 'statement_of_income'
                and metric = 'إجمالي المصاريف'
                then 'total_expenses'

            when statement_type = 'statement_of_income'
                and metric = 'Admin and Marketing Expenses'
                then 'admin_and_marketing_expenses'
            when statement_type = 'statement_of_income'
                and metric = 'المصاريف الإدارية والتسويقية'
                then 'admin_and_marketing_expenses'

            when statement_type = 'statement_of_income'
                and metric = 'Other Expenses'
                then 'other_expenses'
            when statement_type = 'statement_of_income'
                and metric = 'المصاريف الأخرى'
                then 'other_expenses'

            when statement_type = 'statement_of_income'
                and metric = 'Other Revenues'
                then 'other_revenues'
            when statement_type = 'statement_of_income'
                and metric = 'الإيرادات الأخرى'
                then 'other_revenues'

            when statement_type = 'statement_of_income'
                and metric = 'Sales'
                then 'sales'
            when statement_type = 'statement_of_income'
                and metric = 'المبيعات'
                then 'sales'

            when statement_type = 'statement_of_income'
                and metric = 'Sales Cost'
                then 'sales_cost'
            when statement_type = 'statement_of_income'
                and metric = 'تكاليف المبيعات'
                then 'sales_cost'

            when statement_type = 'statement_of_income'
                and metric = 'Depreciation'
                then 'depreciation'
            when statement_type = 'statement_of_income'
                and metric = 'الاستهلاكات'
                then 'depreciation'

            when statement_type = 'statement_of_income'
                and metric = 'Zakat'
                then 'zakat'
            when statement_type = 'statement_of_income'
                and metric = 'الزكاة'
                then 'zakat'

            when statement_type = 'statement_of_income'
                and metric = 'Zakat and Income Tax'
                then 'zakat_and_income_tax'
            when statement_type = 'statement_of_income'
                and metric = 'الزكاة وضريبة الدخل'
                then 'zakat_and_income_tax'

            when statement_type = 'statement_of_income'
                and metric = 'Net Income'
                then 'net_income'
            when statement_type = 'statement_of_income'
                and metric = 'صافي الدخل'
                then 'net_income'

            when statement_type = 'statement_of_income'
                and metric = 'Net Income Before Zakat'
                then 'net_income_before_zakat'
            when statement_type = 'statement_of_income'
                and metric = 'صافي الدخل قبل الزكاة'
                then 'net_income_before_zakat'

            when statement_type = 'statement_of_income'
                and metric = 'Net Profit (Loss) Attributable to Shareholders of the Issuer'
                then 'net_profit_attributable_to_shareholders'
            when statement_type = 'statement_of_income'
                and metric = 'صافي الربح (الخسارة) العائد لمساهمي المصدر'
                then 'net_profit_attributable_to_shareholders'

            when statement_type = 'statement_of_income'
                and metric = 'Net Profit (Loss) before Zakat and Tax'
                then 'net_profit_before_zakat_and_tax'
            when statement_type = 'statement_of_income'
                and metric = 'صافي الربح (الخسارة) قبل الزكاة والضريبة'
                then 'net_profit_before_zakat_and_tax'

            when statement_type = 'statement_of_income'
                and metric = 'Profit (Loss) per Share'
                then 'earnings_per_share'
            when statement_type = 'statement_of_income'
                and metric = 'ربحية (خسارة) السهم'
                then 'earnings_per_share'

            when statement_type = 'statement_of_income'
                and metric = 'Total Comprehensive Income Attributable to Shareholders of the Issuer'
                then 'total_comprehensive_income_attributable_to_shareholders'
            when statement_type = 'statement_of_income'
                and metric = 'إجمالي الدخل الشامل العائد لمساهمي المصدر'
                then 'total_comprehensive_income_attributable_to_shareholders'

            when statement_type = 'statement_of_income'
                and metric = 'Cash Dividends'
                then 'cash_dividends'
            when statement_type = 'statement_of_income'
                and metric = 'الارباح النقدية المقترح توزيعها'
                then 'cash_dividends'

            when statement_type = 'statement_of_income'
                and metric = 'Other Distributions'
                then 'other_distributions'
            when statement_type = 'statement_of_income'
                and metric = 'التوزيعات الأخرى'
                then 'other_distributions'

            when statement_type = 'statement_of_income'
                and metric = 'Reserves'
                then 'reserves'
            when statement_type = 'statement_of_income'
                and metric = 'المحول الى الإحتياطات'
                then 'reserves'

            when statement_type = 'statement_of_income'
                and metric = 'Balance First Period'
                then 'retained_earnings_beginning'
            when statement_type = 'statement_of_income'
                and metric = 'رصيدالأرباح المبقاة أول الفترة'
                then 'retained_earnings_beginning'

            when statement_type = 'statement_of_income'
                and metric = 'Balance End Period'
                then 'retained_earnings_ending'
            when statement_type = 'statement_of_income'
                and metric = 'رصيد الأرباح المبقاة آخر الفترة'
                then 'retained_earnings_ending'


            -- Cash flow
            when statement_type = 'cash_flow'
                and metric = 'Accounts Payable'
                then 'accounts_payable'
            when statement_type = 'cash_flow'
                and metric = 'الحسابات الدائنة'
                then 'accounts_payable'

            when statement_type = 'cash_flow'
                and metric = 'Accounts Receivable'
                then 'accounts_receivable'
            when statement_type = 'cash_flow'
                and metric = 'الحسابات المدينة'
                then 'accounts_receivable'

            when statement_type = 'cash_flow'
                and metric = 'Cash at Begining of Period'
                then 'cash_beginning'
            when statement_type = 'cash_flow'
                and metric = 'النقد في بداية الفترة'
                then 'cash_beginning'

            when statement_type = 'cash_flow'
                and metric = 'Cash at End of Period'
                then 'cash_ending'
            when statement_type = 'cash_flow'
                and metric = 'النقد في نهاية الفترة'
                then 'cash_ending'

            when statement_type = 'cash_flow'
                and metric = 'Cash and Cash Equivalents, Beginning of the Period'
                then 'cash_beginning'
            when statement_type = 'cash_flow'
                and metric = 'النقد وما يماثله في بداية الفترة'
                then 'cash_beginning'

            when statement_type = 'cash_flow'
                and metric = 'Cash and Cash Equivalents, End of the Period'
                then 'cash_ending'
            when statement_type = 'cash_flow'
                and metric = 'النقد وما يماثله في نهاية الفترة'
                then 'cash_ending'

            when statement_type = 'cash_flow'
                and metric = 'Depreciation'
                then 'depreciation'
            when statement_type = 'cash_flow'
                and metric = 'الاستهلاكات'
                then 'depreciation'

            when statement_type = 'cash_flow'
                and metric = 'Increase in Debts'
                then 'increase_in_debts'
            when statement_type = 'cash_flow'
                and metric = 'الزيادة في الديون'
                then 'increase_in_debts'

            when statement_type = 'cash_flow'
                and metric = 'Inventory'
                then 'inventory'
            when statement_type = 'cash_flow'
                and metric = 'المخزون'
                then 'inventory'

            when statement_type = 'cash_flow'
                and metric = 'Net Income'
                then 'net_income'
            when statement_type = 'cash_flow'
                and metric = 'صافي الدخل'
                then 'net_income'

            when statement_type = 'cash_flow'
                and metric = 'Other Changes in Financing Act.'
                then 'other_changes_financing'
            when statement_type = 'cash_flow'
                and metric = 'التغييرات الأخرى في نشاط التمويل'
                then 'other_changes_financing'

            when statement_type = 'cash_flow'
                and metric = 'Other Changes in Investing Act.'
                then 'other_changes_investing'
            when statement_type = 'cash_flow'
                and metric = 'التغييرات الأخرى في نشاط الإستثمار'
                then 'other_changes_investing'

            when statement_type = 'cash_flow'
                and metric = 'Other Changes in Oper. Activity'
                then 'other_changes_operating'
            when statement_type = 'cash_flow'
                and metric = 'التغييرات الأخرى في نشاط العمليات'
                then 'other_changes_operating'

            when statement_type = 'cash_flow'
                and metric = 'Prepaid Expenses'
                then 'prepaid_expenses'
            when statement_type = 'cash_flow'
                and metric = 'المصاريف المدفوعة مقدما'
                then 'prepaid_expenses'

            when statement_type = 'cash_flow'
                and metric = 'Purchases of Fixed Assets'
                then 'purchases_of_fixed_assets'
            when statement_type = 'cash_flow'
                and metric = 'مشتريات الموجودات الثابتة'
                then 'purchases_of_fixed_assets'

            when statement_type = 'cash_flow'
                and metric = 'Net Cash From Financing Activities'
                then 'net_cash_from_financing'
            when statement_type = 'cash_flow'
                and metric = 'صافي النقد من الأنشطة التمويلية'
                then 'net_cash_from_financing'

            when statement_type = 'cash_flow'
                and metric = 'Net Cash From Investing Activities'
                then 'net_cash_from_investing'
            when statement_type = 'cash_flow'
                and metric = 'صافي النقد من الأنشطة الإستثمارية'
                then 'net_cash_from_investing'

            when statement_type = 'cash_flow'
                and metric = 'Net Cash From Operating Activities'
                then 'net_cash_from_operating'
            when statement_type = 'cash_flow'
                and metric = 'صافي النقد من الأنشطة التشغيلية'
                then 'net_cash_from_operating'

            else null

        end as canonical_metric,

        coalesce(
            value_double,
            nullif(trim(value::text), '')::numeric
        ) as metric_value

    from financials
),

deduplicated as (

    select
        symbol,
        period,
        statement_type,
        canonical_metric,
        metric_value,
        row_number() over (
            partition by
                symbol,
                period,
                statement_type,
                canonical_metric
            order by
                case when language = 'en' then 1 else 2 end
        ) as rn

    from mapped
    where canonical_metric is not null
      and metric_value is not null
)

select
    symbol,
    period,
    statement_type,
    canonical_metric as metric,
    metric_value
from deduplicated
where rn = 1