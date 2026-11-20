select
    bal.entity,
    bal.account_id,
    bal.account_name,
    bal.period,
    bal.net_change as actual_amount,
    bud.budget_amount,
    bal.net_change - bud.budget_amount as variance_amount,
    (bal.net_change - bud.budget_amount) / bud.budget_amount as variance_pct
from {{ ref('fct_account_balances') }} as bal
join {{ ref('stg_budgets') }} as bud
    on bal.entity = bud.entity
    and bal.account_id = bud.account_id
    and bal.period = bud.period
where bal.account_type = 'Expense'