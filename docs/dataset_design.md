# Dataset design - APPROVED 2026-11-15; RESCALED to Koch scale the same
# day at Zain's direction (amounts and entity structure now mirror a
# ~$115B-revenue conglomerate; journal volume is a sample)

A fictional conglomerate, NorthPeak, patterned on Koch Industries' shape:
a parent plus eight businesses - Energy, Chemicals, Building Products,
Electronics, Ag & Fertilizer, Glass, Software, Capital - running about
$9.6B of revenue a month. Three months of books (Aug-Oct 2026), budgets,
tax provision by entity, bank statement, and an inventory subledger.
Every pilot question has a real answer hidden in the data, including
planted problems for the agent to find.

Why scale matters (the interview point): at this size, close problems
stop being about finding a wrong number and become about matching rules,
tolerances, and materiality - a $1.65M intercompany difference is small
enough to chase for a week and large enough to matter. The dbt logic is
identical at any scale; the controls are what change.

## Dimensions on every journal line
- Entity, Region (Dallas, Chicago, Remote), Channel (Direct, Partner,
  Online), Cost center, Vendor (where relevant), Location (inventory)

## Tables
- `chart_of_accounts` - 29 accounts incl. intercompany due from/to (1350/2150).
- `gl_lines` - 420 journals / 840 lines, Aug-Oct 2026; every journal balances.
- `budgets` - monthly budget by account and entity.
- `tax_provision` - provision and pretax income by entity, Q2 and Q3 2026.
- `inventory_subledger` - quantity and value by SKU and location (Dallas, Chicago).
- `gl_inventory_control` - GL inventory balance by location (~$1.05B total).
- `bank_transactions` - the October bank statement, derived from GL cash
  lines with planted exceptions.
- `accrual_submissions` - accruals the close is waiting on, by department,
  with received/missing status (2 missing).

## SOP / policy documents (the agent's rulebook - written in Step 4)
1. Accrual policy - invoices received after close (question 4).
2. Close calendar and flux thresholds - which moves need commentary.
3. Inventory count and reconciliation policy.
4. Tax provision process.
5. Professional services engagement policy.

## Planted storylines (the answers must be findable, not invented)
- Professional services (6100) is ~22.5% over budget in October
  ($51.5M vs $42.0M): consultants engaged on a systems project at Energy
  ($6.2M) and close support at Software ($3.2M), in journal memos.
- Bank rec: an unrecorded $245K bank fee, the parent's $12M rent check
  still outstanding, and a ~$1.04B Energy deposit in transit (question 1).
- Two accrual submissions never arrived: Legal ($9.2M) and IT ($3.1M)
  (question 2).
- A September marketing accrual ($14.2M, Building Products) was never
  reversed and the invoice was paid in October - double-counted (question 3).
- One journal is an exact duplicate: Software's $12.4M CloudNine
  subscription (question 5). Another October journal ($1.475M, Parent)
  was posted with no supporting memo (question 5).
- Intercompany: Software bills Energy $22M/month for shared IT services;
  in October Energy recorded $20.35M - the pair disagrees by $1.65M
  (question 6).
- Inventory ties in Dallas but NOT Chicago: a $48.5M receiving entry is
  missing from the subledger (question 7).
- Dallas COGS runs hot: a LoneStar Freight fuel surcharge, $14M in Sep
  and $21.5M in Oct, at Energy (question 12).
- Tax provision rose $375M in Q3 (to $1,335M); Ag & Fertilizer drove
  $354M of it on a pretax spike (question 11).

## Known scale gaps (honest, deferred)
- No multi-currency / FX translation yet - a real conglomerate close
  pain, noted for a later slice.
- Journal volume is sampled (420 journals); a real Koch-scale close is
  tens of thousands. The matching and control logic is the same.
