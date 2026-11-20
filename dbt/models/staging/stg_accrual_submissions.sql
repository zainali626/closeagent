select
    department,
    item,
    cast(expected_amount as decimal(18, 2)) as expected_amount,
    status,
    period
from {{ ref('accrual_submissions') }}