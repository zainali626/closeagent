-- CloseAgent - Databricks port (Step 3)
-- Platform: Databricks Free Edition, catalog "workspace", schema "closeagent"
-- Source data: data/scaled/ output of scripts/scale_up.py, uploaded to the
-- Unity Catalog volume workspace.closeagent.raw_files
-- (gl_lines uploaded as gl_lines_part1/2/3.csv).
--
-- Verified results on Databricks (2026-11-21), matching the local DuckDB/dbt
-- build exactly:
--   raw_gl_lines row count .................... 1,000,000
--   Oct professional services (acct 6100) ..... 51,468,108.90
--   NP-SOFT software subscriptions variance ... +100.00% (the duplicate)
--   Chicago inventory gap ..................... 48,500,000.00
--   Bank rec exception rows ................... 3
--   Tax provision change Q2 -> Q3 ............. 375,000,000.00
--   Intercompany: NP-SOFT due-from 66,000,000 vs NP-ENERGY due-to 64,350,000

-- =====================================================================
-- 1. Raw tables (all columns land as text; casting lives in staging)
-- =====================================================================
CREATE OR REPLACE TABLE workspace.closeagent.raw_gl_lines AS
SELECT * FROM read_files('/Volumes/workspace/closeagent/raw_files/gl_lines_part*.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE workspace.closeagent.raw_chart_of_accounts AS
SELECT * FROM read_files('/Volumes/workspace/closeagent/raw_files/chart_of_accounts.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE workspace.closeagent.raw_budgets AS
SELECT * FROM read_files('/Volumes/workspace/closeagent/raw_files/budgets.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE workspace.closeagent.raw_bank_transactions AS
SELECT * FROM read_files('/Volumes/workspace/closeagent/raw_files/bank_transactions.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE workspace.closeagent.raw_accrual_submissions AS
SELECT * FROM read_files('/Volumes/workspace/closeagent/raw_files/accrual_submissions.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE workspace.closeagent.raw_tax_provision AS
SELECT * FROM read_files('/Volumes/workspace/closeagent/raw_files/tax_provision.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE workspace.closeagent.raw_inventory_subledger AS
SELECT * FROM read_files('/Volumes/workspace/closeagent/raw_files/inventory_subledger.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE workspace.closeagent.raw_gl_inventory_control AS
SELECT * FROM read_files('/Volumes/workspace/closeagent/raw_files/gl_inventory_control.csv',
  format => 'csv', header => true, inferSchema => false);

-- =====================================================================
-- 2. Staging views (casting layer - mirrors dbt/models/staging)
-- =====================================================================
CREATE OR REPLACE VIEW workspace.closeagent.stg_chart_of_accounts AS
SELECT account_id, account_name, account_type
FROM workspace.closeagent.raw_chart_of_accounts;

CREATE OR REPLACE VIEW workspace.closeagent.stg_gl_lines AS
SELECT
  journal_id,
  CAST(journal_date AS DATE) AS journal_date,
  period,
  entity,
  account_id,
  CAST(debit AS DECIMAL(18,2)) AS debit,
  CAST(credit AS DECIMAL(18,2)) AS credit,
  region, channel, cost_center, vendor, location, memo
FROM workspace.closeagent.raw_gl_lines;

CREATE OR REPLACE VIEW workspace.closeagent.stg_budgets AS
SELECT entity, account_id, period, CAST(budget_amount AS DECIMAL(18,2)) AS budget_amount
FROM workspace.closeagent.raw_budgets;

CREATE OR REPLACE VIEW workspace.closeagent.stg_bank_transactions AS
SELECT CAST(bank_date AS DATE) AS bank_date, description,
  CAST(amount AS DECIMAL(18,2)) AS amount, reference
FROM workspace.closeagent.raw_bank_transactions;

CREATE OR REPLACE VIEW workspace.closeagent.stg_accrual_submissions AS
SELECT department, item, CAST(expected_amount AS DECIMAL(18,2)) AS expected_amount, status, period
FROM workspace.closeagent.raw_accrual_submissions;

CREATE OR REPLACE VIEW workspace.closeagent.stg_tax_provision AS
SELECT entity, quarter, CAST(pretax_income AS DECIMAL(18,2)) AS pretax_income,
  CAST(provision_amount AS DECIMAL(18,2)) AS provision_amount
FROM workspace.closeagent.raw_tax_provision;

CREATE OR REPLACE VIEW workspace.closeagent.stg_inventory_subledger AS
SELECT sku, description, location, CAST(quantity AS INT) AS quantity,
  CAST(unit_cost AS DECIMAL(18,2)) AS unit_cost, CAST(value AS DECIMAL(18,2)) AS value
FROM workspace.closeagent.raw_inventory_subledger;

CREATE OR REPLACE VIEW workspace.closeagent.stg_gl_inventory_control AS
SELECT location, CAST(gl_balance AS DECIMAL(18,2)) AS gl_balance, CAST(as_of_date AS DATE) AS as_of_date
FROM workspace.closeagent.raw_gl_inventory_control;

-- =====================================================================
-- 3. Marts (mirror dbt/models/marts)
-- =====================================================================
CREATE OR REPLACE TABLE workspace.closeagent.fct_account_balances AS
SELECT
  g.entity,
  g.account_id,
  c.account_name,
  c.account_type,
  g.period,
  SUM(g.debit) AS total_debits,
  SUM(g.credit) AS total_credits,
  SUM(g.debit - g.credit) AS net_change
FROM workspace.closeagent.stg_gl_lines g
JOIN workspace.closeagent.stg_chart_of_accounts c
  ON g.account_id = c.account_id
GROUP BY g.entity, g.account_id, c.account_name, c.account_type, g.period;

CREATE OR REPLACE TABLE workspace.closeagent.fct_variance AS
SELECT a.entity, a.account_id, a.account_name, a.period,
  a.net_change AS actual_amount, b.budget_amount,
  a.net_change - b.budget_amount AS variance_amount,
  (a.net_change - b.budget_amount) / b.budget_amount * 100 AS variance_pct
FROM workspace.closeagent.fct_account_balances a
JOIN workspace.closeagent.stg_budgets b
  ON a.entity = b.entity AND a.account_id = b.account_id AND a.period = b.period
WHERE a.account_type = 'Expense';

CREATE OR REPLACE TABLE workspace.closeagent.fct_inventory_reconciliation AS
SELECT c.location, c.gl_balance, s.subledger_total,
  c.gl_balance - s.subledger_total AS difference
FROM workspace.closeagent.stg_gl_inventory_control c
JOIN (SELECT location, SUM(value) AS subledger_total
      FROM workspace.closeagent.stg_inventory_subledger GROUP BY location) s
  ON c.location = s.location;

CREATE OR REPLACE TABLE workspace.closeagent.fct_intercompany AS
SELECT entity,
  SUM(CASE WHEN account_id = '1350' THEN debit - credit ELSE 0 END) AS due_from_affiliates,
  SUM(CASE WHEN account_id = '2150' THEN credit - debit ELSE 0 END) AS due_to_affiliates
FROM workspace.closeagent.stg_gl_lines
WHERE account_id IN ('1350', '2150')
GROUP BY entity;

CREATE OR REPLACE TABLE workspace.closeagent.fct_bank_rec_exceptions AS
WITH gl AS (
  SELECT CAST(debit - credit AS DECIMAL(18,2)) AS amount, COUNT(*) AS gl_count
  FROM workspace.closeagent.stg_gl_lines
  WHERE account_id = '1000' AND period = '2026-10' GROUP BY amount
),
bank AS (
  SELECT amount, COUNT(*) AS bank_count
  FROM workspace.closeagent.stg_bank_transactions GROUP BY amount
)
SELECT COALESCE(g.amount, b.amount) AS amount,
  COALESCE(g.gl_count, 0) AS gl_count, COALESCE(b.bank_count, 0) AS bank_count
FROM gl g FULL OUTER JOIN bank b ON g.amount = b.amount
WHERE COALESCE(g.gl_count, 0) <> COALESCE(b.bank_count, 0);

CREATE OR REPLACE TABLE workspace.closeagent.fct_tax_provision AS
SELECT entity,
  SUM(CASE WHEN quarter = '2026-Q2' THEN provision_amount END) AS q2_provision,
  SUM(CASE WHEN quarter = '2026-Q3' THEN provision_amount END) AS q3_provision,
  SUM(CASE WHEN quarter = '2026-Q3' THEN provision_amount END)
    - SUM(CASE WHEN quarter = '2026-Q2' THEN provision_amount END) AS change_amount
FROM workspace.closeagent.stg_tax_provision
GROUP BY entity;
