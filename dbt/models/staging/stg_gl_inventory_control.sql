select
    location,
    cast(gl_balance as decimal(18, 2)) as gl_balance,
    cast(as_of_date as date) as as_of_date
from {{ ref('gl_inventory_control') }}