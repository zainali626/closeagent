select
    journal_id,
    sum(debit) - sum(credit) as imbalance
from {{ ref('stg_gl_lines') }}
group by journal_id
having abs(sum(debit) - sum(credit)) > 0.01