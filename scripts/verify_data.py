"""Verify the planted storylines in data/raw are exactly as designed.

Run: python scripts/verify_data.py - exits non-zero if any check fails.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def load(name):
    with open(RAW / name) as f:
        return list(csv.DictReader(f))


gl = load("gl_lines.csv")
budgets = load("budgets.csv")
tax = load("tax_provision.csv")
sub = load("inventory_subledger.csv")
ctrl = {r["location"]: float(r["gl_balance"]) for r in load("gl_inventory_control.csv")}

failures = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL"), name, detail)
    if not ok:
        failures.append(name)


# 1. Every journal balances
by_journal = defaultdict(lambda: [0.0, 0.0])
for ln in gl:
    by_journal[ln["journal_id"]][0] += float(ln["debit"])
    by_journal[ln["journal_id"]][1] += float(ln["credit"])
unbalanced = [j for j, (d, c) in by_journal.items() if abs(d - c) > 0.01]
check("all journals balance", not unbalanced, f"({len(by_journal)} journals)")

# 2. October professional services 20-24% over budget
actual = sum(float(ln["debit"]) - float(ln["credit"]) for ln in gl
             if ln["account_id"] == "6100" and ln["period"] == "2026-10")
budget = sum(float(b["budget_amount"]) for b in budgets
             if b["account_id"] == "6100" and b["period"] == "2026-10")
var = (actual / budget - 1) * 100
check("Oct prof services 20-24% over budget", 20 <= var <= 24,
      f"(actual {actual:,.0f} vs budget {budget:,.0f} = {var:.1f}%)")

# 3. Exactly one duplicate journal group in October (same date, entity,
# account, amounts, memo - different journal_id)
sig = defaultdict(set)
for ln in gl:
    if ln["period"] == "2026-10":
        sig[(ln["journal_date"], ln["entity"], ln["account_id"], ln["debit"],
             ln["credit"], ln["memo"])].add(ln["journal_id"])
dups = {k: v for k, v in sig.items() if len(v) > 1}
dup_journals = {j for v in dups.values() for j in v}
check("exactly one duplicate pair in October", len(dup_journals) == 2,
      f"({sorted(dup_journals)})")

# 4. AR balance by channel at Oct 31 - all three channels positive
ar = defaultdict(float)
for ln in gl:
    if ln["account_id"] == "1300":
        ar[ln["channel"]] += float(ln["debit"]) - float(ln["credit"])
check("AR positive in all 3 channels",
      all(ar[c] > 0 for c in ["Direct", "Partner", "Online"]),
      f"({ {c: round(v) for c, v in ar.items() if c} })")

# 5. Inventory tie-out: Dallas ties, Chicago short exactly 48,500
sub_tot = defaultdict(float)
for r in sub:
    sub_tot[r["location"]] += float(r["value"])
check("Dallas inventory ties", abs(ctrl["Dallas"] - sub_tot["Dallas"]) < 1.0,
      f"(GL {ctrl['Dallas']:,.0f} vs subledger {sub_tot['Dallas']:,.0f})")
check("Chicago inventory short 48.5M",
      abs((ctrl["Chicago"] - sub_tot["Chicago"]) - 48_500_000) < 1.0,
      f"(diff {ctrl['Chicago'] - sub_tot['Chicago']:,.0f})")

# 6. Tax: Q3-Q2 change is 375,000, of which Logistics drove 354,000
prov = {(r["entity"], r["quarter"]): float(r["provision_amount"]) for r in tax}
TAX_ENTS = ["NP-PARENT", "NP-ENERGY", "NP-CHEM", "NP-AG", "NP-BUILD"]
total_change = sum(prov[(e, "2026-Q3")] - prov[(e, "2026-Q2")] for e in TAX_ENTS)
ag_change = prov[("NP-AG", "2026-Q3")] - prov[("NP-AG", "2026-Q2")]
check("tax provision change 375M / Ag drove 354M",
      total_change == 375_000_000 and ag_change == 354_000_000,
      f"(total {total_change:,.0f}, AG {ag_change:,.0f})")

# 7. Dallas COGS October includes the 21,500 LoneStar surcharge
surcharge = [ln for ln in gl if ln["vendor"] == "LoneStar Freight"
             and ln["period"] == "2026-10" and ln["account_id"] == "5100"]
check("Oct Dallas COGS surcharge present",
      len(surcharge) == 1 and float(surcharge[0]["debit"]) == 21_500_000,
      f"({len(surcharge)} lines)")

# 8. Intercompany: Software's due-from Energy is 66M; Energy's
# due-to Software is 64.35M - the pair disagrees by exactly 1.65M
due_from = sum(float(ln["debit"]) - float(ln["credit"]) for ln in gl
               if ln["account_id"] == "1350" and ln["entity"] == "NP-SOFT")
due_to = sum(float(ln["credit"]) - float(ln["debit"]) for ln in gl
             if ln["account_id"] == "2150" and ln["entity"] == "NP-ENERGY")
check("intercompany mismatch is 1.65M", due_from - due_to == 1_650_000,
      f"(due from {due_from:,.0f} vs due to {due_to:,.0f})")

# 9. Unreversed accrual: 2400 still carries the full 14.2M at Oct 31
accrued = sum(float(ln["credit"]) - float(ln["debit"]) for ln in gl
              if ln["account_id"] == "2400")
check("unreversed Sep accrual still in 2400", accrued == 14_200_000,
      f"(2400 balance {accrued:,.0f})")

# 10. Exactly one October journal has no supporting memo
unsupported = {ln["journal_id"] for ln in gl
               if ln["period"] == "2026-10" and ln["memo"] == ""}
check("exactly one unsupported October journal", len(unsupported) == 1,
      f"({sorted(unsupported)})")

# 11. Bank rec: bank-only item is the 385 fee; GL-only items are exactly 2
from collections import Counter

gl_cash = Counter()
for ln in gl:
    if ln["period"] == "2026-10" and ln["account_id"] == "1000":
        gl_cash[round(float(ln["debit"]) - float(ln["credit"]), 2)] += 1
bank = Counter()
for r in load("bank_transactions.csv"):
    bank[round(float(r["amount"]), 2)] += 1
gl_only = gl_cash - bank
bank_only = bank - gl_cash
check("bank rec exceptions as planted",
      sum(gl_only.values()) == 2 and bank_only == Counter({-245000.0: 1}),
      f"(GL-only {dict(gl_only)}, bank-only {dict(bank_only)})")

# 12. Two accrual submissions still missing
subs = load("accrual_submissions.csv")
missing = [s for s in subs if s["status"] == "missing"]
check("two accrual submissions missing", len(missing) == 2,
      f"({[s['department'] for s in missing]})")

sys.exit(1 if failures else 0)
