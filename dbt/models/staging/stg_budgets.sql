select
    entity,
    account_id,
    period,
    cast(budget_amount as decimal(18, 2)) as budget_amount
from {{ ref('budgets') }}