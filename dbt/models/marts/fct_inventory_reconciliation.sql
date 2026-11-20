select
    ctrl.location,
    ctrl.gl_balance,
    sum(sub.value) as subledger_value,
    ctrl.gl_balance - sum(sub.value) as difference
from {{ ref('stg_gl_inventory_control') }} as ctrl
join {{ ref('stg_inventory_subledger') }} as sub
    on ctrl.location = sub.location
group by ctrl.location, ctrl.gl_balance