select
    journal_id,
    cast(journal_date as date) as journal_date,
    period,
    entity,
    account_id,
    cast(debit as decimal(18, 2)) as debit,
    cast(credit as decimal(18, 2)) as credit,
    region,
    channel,
    cost_center,
    vendor,
    location,
    memo
from {{ ref('gl_lines') }}