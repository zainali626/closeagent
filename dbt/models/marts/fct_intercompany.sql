select
    entity,
    sum(case when account_id = '1350' then debit - credit else 0 end) as due_from_affiliates,
    sum(case when account_id = '2150' then credit - debit else 0 end) as due_to_affiliates
from {{ ref('stg_gl_lines') }}
where account_id in ('1350', '2150')
group by entity