-- Example staging model (Muse's worked example for the pattern).
-- Staging models do exactly three things: rename, cast, and nothing else.
-- No joins, no business logic - that lives in the marts.
select
    cast(account_id as varchar) as account_id,
    account_name,
    account_type
from {{ ref('chart_of_accounts') }}
