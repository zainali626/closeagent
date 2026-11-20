select
    entity,
    quarter,
    cast(pretax_income as decimal(18, 2)) as pretax_income,
    cast(provision_amount as decimal(18, 2)) as provision_amount
from {{ ref('tax_provision') }}