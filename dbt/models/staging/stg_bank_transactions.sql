select
    cast(bank_date as date) as bank_date,
    description,
    cast(amount as decimal(18, 2)) as amount,
    reference
from {{ ref('bank_transactions') }}