select
    sku,
    description,
    location,
    cast(quantity as integer) as quantity,
    cast(unit_cost as decimal(18, 2)) as unit_cost,
    cast(value as decimal(18, 2)) as value
from {{ ref('inventory_subledger') }}