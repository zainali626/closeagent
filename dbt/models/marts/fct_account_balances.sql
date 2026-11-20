select
    gl.entity,
    gl.account_id,
    coa.account_name,
    coa.account_type,
    gl.period,
    sum(gl.debit) as total_debits,
    sum(gl.credit) as total_credits,
    sum(gl.debit) - sum(gl.credit) as net_change
from {{ ref('stg_gl_lines') }} as gl
join {{ ref('stg_chart_of_accounts') }} as coa
    on gl.account_id = coa.account_id
group by gl.entity, gl.account_id, coa.account_name, coa.account_type, gl.period