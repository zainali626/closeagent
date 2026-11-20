with gl_cash as (
    select debit - credit as amount, count(*) as gl_count
    from {{ ref('stg_gl_lines') }}
    where period = '2026-10' and account_id = '1000'
    group by amount
),
bank as (
    select amount, count(*) as bank_count
    from {{ ref('stg_bank_transactions') }}
    group by amount
)
select
    coalesce(gl_cash.amount, bank.amount) as amount,
    coalesce(gl_cash.gl_count, 0) as gl_count,
    coalesce(bank.bank_count, 0) as bank_count
from gl_cash
full outer join bank
    on gl_cash.amount = bank.amount
where coalesce(gl_cash.gl_count, 0) <> coalesce(bank.bank_count, 0)