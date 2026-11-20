select
    entity,
    sum(case when quarter = '2026-Q2' then provision_amount else 0 end) as q2_provision,
    sum(case when quarter = '2026-Q3' then provision_amount else 0 end) as q3_provision,
    sum(case when quarter = '2026-Q3' then provision_amount else 0 end)
        - sum(case when quarter = '2026-Q2' then provision_amount else 0 end) as change_amount
from {{ ref('stg_tax_provision') }}
group by entity