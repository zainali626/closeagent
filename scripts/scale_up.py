"""Scale up the CloseAgent dataset WITHOUT moving any planted storyline.

Reads the canonical small dataset in data/raw/ and writes a scaled copy to
data/scaled/. The original files are never touched.

Protection rules (each maps to a check in verify_data.py):
- Filler never touches accounts 1000 (except paired bank journals in Oct),
  1300, 1350, 2150, 2400, 5100, 6100, 6400, 6450.
- Filler never uses the vendors LoneStar Freight or Brightline Media.
- Every filler journal gets a unique memo (protects the duplicate check)
  and a non-empty memo (protects the unsupported-journal check).
- Bank scaling adds matched pairs: one October GL cash line AND one bank
  row with the identical amount, so the exception counts cannot move.
- Inventory scaling adds NEW locations whose subledger and GL control
  totals tie exactly; Dallas and Chicago rows are untouched.
- Tax scaling adds other quarters / other entities only; the five planted
  entities' 2026-Q2 and 2026-Q3 rows are untouched.
- Accrual scaling adds only status='received' rows; the 2 missing stay 2.
- Budgets: existing rows are never modified; new rows are added only for
  (entity, account, period) keys that do not already exist.

Run:  python scripts/scale_up.py
Then: the script verifies the scaled output with the same 12 storyline
checks as verify_data.py and prints PASS/FAIL for each.
"""

import csv
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "scaled"
PARTS = OUT / "parts"

rng = random.Random(42)

ENTITIES = ["NP-PARENT", "NP-ENERGY", "NP-CHEM", "NP-BUILD", "NP-ELEC",
            "NP-AG", "NP-GLASS", "NP-SOFT", "NP-CAP"]
ENTITY_SCALE = {"NP-PARENT": 1.4, "NP-ENERGY": 2.2, "NP-CHEM": 1.6,
                "NP-BUILD": 1.2, "NP-ELEC": 1.1, "NP-AG": 1.5,
                "NP-GLASS": 0.9, "NP-SOFT": 0.8, "NP-CAP": 0.7}
PERIODS = [("2026-08", 2026, 8), ("2026-09", 2026, 9), ("2026-10", 2026, 10)]

# New chart-of-accounts rows (none of these IDs exist in the planted chart,
# and none collide with a storyline account).
NEW_ACCOUNTS = [
    ("1450", "Other Current Assets", "Asset"),
    ("1650", "Construction in Progress", "Asset"),
    ("2550", "Current Portion of Long-Term Debt", "Liability"),
    ("4400", "Interest Income", "Revenue"),
    ("4500", "Dividend Income", "Revenue"),
    ("6920", "Office Supplies Expense", "Expense"),
    ("7150", "Bank Service Charges", "Expense"),
    ("7250", "Repairs and Maintenance Expense", "Expense"),
    ("7350", "Training and Development Expense", "Expense"),
    ("7450", "Freight and Logistics Expense", "Expense"),
]

# Filler expense accounts -> (vendors, memo base). All are storyline-free.
FILLER = {
    "6200": (["PayPro Services", "NorthStar Staffing"], "Payroll batch"),
    "6300": (["Skyline Properties", "Meridian Property Group"], "Facility rent"),
    "6500": (["CityPower Energy", "GridWorks Utilities"], "Utilities service"),
    "6600": (["AdVantage Media", "ClearChannel Partners"], "Campaign spend"),
    "6700": (["Sentinel Insurance", "Hartford Mutual Group"], "Insurance premium"),
    "6800": ([], "Depreciation run"),
    "6900": (["Voyage Travel Group", "SkyRoute Airlines"], "Business travel"),
    "7100": (["First National Bank", "Capital Markets Desk"], "Interest accrual"),
    "6920": (["SupplyHub Office", "Staples Business Advantage"], "Office supplies order"),
    "7150": (["First National Bank"], "Bank service charges"),
    "7250": (["FixIt Industrial Services", "ProMaint Contractors"], "Maintenance work order"),
    "7350": (["SkillPath Training", "LinkedIn Learning"], "Training program"),
    "7450": (["TransGlobal Freight", "RoadRunner Logistics"], "Freight charges"),
}
COST_CENTERS = ["OPS", "FIN", "IT", "MFG", "SALES", "HR", "ENG"]
REGIONS = ["Central", "East", "West", "South", "North", ""]

TARGET_GL_LINES = 1_000_000
BANK_PAIRS = 25_000          # journals; each adds 2 GL lines + 1 bank row
NEW_LOCATIONS = ["Houston", "Tulsa", "Kansas City", "Nashville", "Denver",
                 "Phoenix", "Atlanta", "Charlotte", "Columbus", "Indianapolis",
                 "Memphis", "Omaha", "Wichita", "Lubbock", "Midland",
                 "Baton Rouge", "Little Rock", "Des Moines", "Fargo", "Boise",
                 "Reno", "Amarillo", "Beaumont", "Corpus Christi"]
SKUS_PER_LOCATION = 60


def load(name, base=RAW):
    with open(base / name, newline="") as f:
        return list(csv.DictReader(f))


def write(name, rows, fields):
    with open(OUT / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def money(x):
    return f"{x:,.2f}".replace(",", "")


def amount_for(entity):
    base = rng.lognormvariate(12.6, 1.05) * ENTITY_SCALE[entity]
    return round(min(max(base, 500.0), 25_000_000.0), 2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PARTS.mkdir(parents=True, exist_ok=True)

    gl = load("gl_lines.csv")
    gl_fields = list(gl[0].keys())
    budgets = load("budgets.csv")
    bank = load("bank_transactions.csv")
    chart = load("chart_of_accounts.csv")
    subs = load("accrual_submissions.csv")
    tax = load("tax_provision.csv")
    sub = load("inventory_subledger.csv")
    ctrl = load("gl_inventory_control.csv")

    seq = 0

    def next_jid(period):
        nonlocal seq
        seq += 1
        return f"JE-{period.replace('-', '')}-F{seq:06d}"

    def filler_journal(period, y, m, entity, account, amt):
        vendors, memo_base = FILLER[account]
        jid = next_jid(period)
        day = rng.randint(1, 28)
        memo = f"{memo_base} #{seq:06d}"
        common = {"journal_id": jid, "journal_date": f"{y}-{m:02d}-{day:02d}",
                      "period": period, "entity": entity,
                      "region": rng.choice(REGIONS), "channel": "",
                      "cost_center": rng.choice(COST_CENTERS),
                      "vendor": rng.choice(vendors) if vendors else "",
                      "location": "", "memo": memo}
        return [
            dict(common, account_id=account, debit=money(amt), credit="0.00"),
            dict(common, account_id="2100", debit="0.00", credit=money(amt)),
        ]

    # ---- bank-matched pairs (October only) -------------------------------
    used_amounts = {round(float(r["amount"]), 2) for r in bank}
    used_amounts |= {-245000.0, -12000000.0, 1041265375.50}
    filler_totals = defaultdict(float)   # (entity, account, period) -> actual
    new_gl = []
    new_bank = []
    pay_accounts = ["6200", "6300", "6500"]
    for _ in range(BANK_PAIRS):
        entity = rng.choice(ENTITIES)
        amt = amount_for(entity)
        while round(amt, 2) in used_amounts:
            amt = round(amt + rng.uniform(0.01, 9.99), 2)
        used_amounts.add(round(amt, 2))
        jid = next_jid("2026-10")
        day = rng.randint(1, 28)
        date = f"2026-10-{day:02d}"
        if rng.random() < 0.6:      # customer receipt: Dr Cash / Cr Revenue
            memo = f"Customer receipt #{seq:06d}"
            rows = [
                {"journal_id": jid, "journal_date": date, "period": "2026-10",
                     "entity": entity, "account_id": "1000", "debit": money(amt),
                     "credit": "0.00", "region": "", "channel": "Direct",
                     "cost_center": "FIN", "vendor": "", "location": "", "memo": memo},
                {"journal_id": jid, "journal_date": date, "period": "2026-10",
                     "entity": entity, "account_id": "4100", "debit": "0.00",
                     "credit": money(amt), "region": "", "channel": "Direct",
                     "cost_center": "FIN", "vendor": "", "location": "", "memo": memo},
            ]
            signed = amt
            desc = f"Customer receipt - {entity}"
        else:                        # operating payment: Dr Expense / Cr Cash
            acct = rng.choice(pay_accounts)
            memo = f"Operating payment #{seq:06d}"
            rows = [
                {"journal_id": jid, "journal_date": date, "period": "2026-10",
                     "entity": entity, "account_id": acct, "debit": money(amt),
                     "credit": "0.00", "region": "", "channel": "",
                     "cost_center": "OPS", "vendor": "", "location": "", "memo": memo},
                {"journal_id": jid, "journal_date": date, "period": "2026-10",
                     "entity": entity, "account_id": "1000", "debit": "0.00",
                     "credit": money(amt), "region": "", "channel": "",
                     "cost_center": "OPS", "vendor": "", "location": "", "memo": memo},
            ]
            signed = -amt
            desc = f"Operating payment - {entity}"
            filler_totals[(entity, acct, "2026-10")] += amt
        new_gl.extend(rows)
        new_bank.append({"bank_date": date, "description": desc,
                             "amount": money(signed), "reference": jid})

    # ---- general expense filler ------------------------------------------
    remaining_lines = TARGET_GL_LINES - len(gl) - len(new_gl)
    n_journals = remaining_lines // 2
    accounts = list(FILLER.keys())
    for _ in range(n_journals):
        period, y, m = rng.choice(PERIODS)
        entity = rng.choice(ENTITIES)
        account = rng.choice(accounts)
        amt = amount_for(entity)
        new_gl.extend(filler_journal(period, y, m, entity, account, amt))
        filler_totals[(entity, account, period)] += amt

    gl_all = gl + new_gl
    write("gl_lines.csv", gl_all, gl_fields)

    # split gl_lines into 3 upload-sized parts for the Databricks volume
    chunk = (len(gl_all) + 2) // 3
    for i in range(3):
        part = gl_all[i * chunk:(i + 1) * chunk]
        with open(PARTS / f"gl_lines_part{i + 1}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=gl_fields)
            w.writeheader()
            w.writerows(part)

    # ---- bank -------------------------------------------------------------
    write("bank_transactions.csv", bank + new_bank, list(bank[0].keys()))

    # ---- chart of accounts -------------------------------------------------
    existing_ids = {r["account_id"] for r in chart}
    for aid, name, typ in NEW_ACCOUNTS:
        if aid not in existing_ids:
            chart.append({"account_id": aid, "account_name": name,
                              "account_type": typ})
    write("chart_of_accounts.csv", chart, list(chart[0].keys()))

    # ---- budgets: add only missing keys, sized near filler actuals --------
    have = {(b["entity"], b["account_id"], b["period"]) for b in budgets}
    for (entity, account, period), actual in sorted(filler_totals.items()):
        if (entity, account, period) not in have and actual > 0:
            amt = round(actual * rng.uniform(0.94, 1.06), 2)
            budgets.append({"entity": entity, "account_id": account,
                                "period": period, "budget_amount": money(amt)})
    write("budgets.csv", budgets, list(budgets[0].keys()))

    # ---- accrual submissions: received only --------------------------------
    depts = ["Finance", "Legal", "IT", "Marketing", "Operations", "HR",
             "Procurement", "Engineering", "EHS", "Treasury"]
    items = ["Vendor accrual", "Contract services accrual", "Bonus accrual",
             "Freight accrual", "Professional fees accrual",
             "Software true-up", "Facilities accrual", "Royalty accrual"]
    for i in range(120):
        period, _, _ = rng.choice(PERIODS)
        subs.append({"department": rng.choice(depts),
                         "item": f"{rng.choice(items)} - batch {i + 1:03d}",
                         "expected_amount": money(rng.uniform(500_000, 25_000_000)),
                         "status": "received", "period": period})
    write("accrual_submissions.csv", subs, list(subs[0].keys()))

    # ---- tax provision: other quarters and entities only -------------------
    quarters = ["2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1",
                "2026-Q4"]
    have_tax = {(r["entity"], r["quarter"]) for r in tax}
    for entity in ENTITIES:
        for q in quarters:
            if (entity, q) in have_tax:
                continue
            pretax = rng.uniform(800_000_000, 6_500_000_000)
            prov = round(pretax * rng.uniform(0.12, 0.16) / 1_000_000) * 1_000_000
            tax.append({"entity": entity, "quarter": q,
                            "pretax_income": money(round(pretax, 2)),
                            "provision_amount": money(float(prov))})
    write("tax_provision.csv", tax, list(tax[0].keys()))

    # ---- inventory: new locations that tie exactly -------------------------
    parts_catalog = [
        ("Hydraulic pump assembly", 4200.00), ("Steel housing unit", 1850.50),
        ("Control valve kit", 975.25), ("Conveyor belt section", 3120.00),
        ("Motor drive unit", 7640.00), ("Sensor array module", 2210.75),
        ("Gearbox assembly", 5480.00), ("Filtration cartridge", 640.00),
        ("Pressure gauge set", 890.50), ("Welding electrode pack", 315.25),
    ]
    {r["location"]: r for r in ctrl}
    for loc in NEW_LOCATIONS:
        total = 0.0
        for i in range(SKUS_PER_LOCATION):
            desc, base_cost = parts_catalog[i % len(parts_catalog)]
            qty = rng.randint(50, 9000)
            unit = round(base_cost * rng.uniform(0.9, 1.1), 2)
            value = round(qty * unit, 2)
            total += value
            sub.append({"sku": f"SKU-{loc[:3].upper()}-{i + 1:03d}",
                            "description": desc, "location": loc, "quantity": qty,
                            "unit_cost": money(unit), "value": money(value)})
        ctrl.append({"location": loc, "gl_balance": money(round(total, 2)),
                         "as_of_date": "2026-10-31"})
    write("inventory_subledger.csv", sub, list(sub[0].keys()))
    write("gl_inventory_control.csv", ctrl, list(ctrl[0].keys()))

    # ---- summary ------------------------------------------------------------
    print("\nRow counts (before -> after):")
    for name in ["gl_lines.csv", "bank_transactions.csv", "budgets.csv",
                 "chart_of_accounts.csv", "accrual_submissions.csv",
                 "tax_provision.csv", "inventory_subledger.csv",
                 "gl_inventory_control.csv"]:
        before = len(load(name))
        after = len(load(name, OUT))
        print(f"  {name:28s} {before:>8,} -> {after:>10,}")

    verify_scaled()


def verify_scaled():
    """The same 12 storyline checks as verify_data.py, run on data/scaled."""
    gl = load("gl_lines.csv", OUT)
    budgets = load("budgets.csv", OUT)
    tax = load("tax_provision.csv", OUT)
    sub = load("inventory_subledger.csv", OUT)
    ctrl = {r["location"]: float(r["gl_balance"])
            for r in load("gl_inventory_control.csv", OUT)}
    failures = []

    def check(name, ok, detail=""):
        print(("PASS" if ok else "FAIL"), name, detail)
        if not ok:
            failures.append(name)

    print("\nStoryline checks on the SCALED data:")
    by_journal = defaultdict(lambda: [0.0, 0.0])
    for ln in gl:
        by_journal[ln["journal_id"]][0] += float(ln["debit"])
        by_journal[ln["journal_id"]][1] += float(ln["credit"])
    unbalanced = [j for j, (d, c) in by_journal.items() if abs(d - c) > 0.01]
    check("all journals balance", not unbalanced, f"({len(by_journal):,} journals)")

    actual = sum(float(ln["debit"]) - float(ln["credit"]) for ln in gl
                 if ln["account_id"] == "6100" and ln["period"] == "2026-10")
    budget = sum(float(b["budget_amount"]) for b in budgets
                 if b["account_id"] == "6100" and b["period"] == "2026-10")
    var = (actual / budget - 1) * 100
    check("Oct prof services 20-24% over budget", 20 <= var <= 24,
          f"(actual {actual:,.0f} vs budget {budget:,.0f} = {var:.1f}%)")

    sig = defaultdict(set)
    for ln in gl:
        if ln["period"] == "2026-10":
            sig[(ln["journal_date"], ln["entity"], ln["account_id"],
                 ln["debit"], ln["credit"], ln["memo"])].add(ln["journal_id"])
    dup_journals = {j for v in sig.values() if len(v) > 1 for j in v}
    check("exactly one duplicate pair in October", len(dup_journals) == 2,
          f"({sorted(dup_journals)})")

    ar = defaultdict(float)
    for ln in gl:
        if ln["account_id"] == "1300":
            ar[ln["channel"]] += float(ln["debit"]) - float(ln["credit"])
    check("AR positive in all 3 channels",
          all(ar[c] > 0 for c in ["Direct", "Partner", "Online"]))

    sub_tot = defaultdict(float)
    for r in sub:
        sub_tot[r["location"]] += float(r["value"])
    check("Dallas inventory ties", abs(ctrl["Dallas"] - sub_tot["Dallas"]) < 1.0)
    check("Chicago inventory short 48.5M",
          abs((ctrl["Chicago"] - sub_tot["Chicago"]) - 48_500_000) < 1.0)

    prov = {(r["entity"], r["quarter"]): float(r["provision_amount"]) for r in tax}
    TAX_ENTS = ["NP-PARENT", "NP-ENERGY", "NP-CHEM", "NP-AG", "NP-BUILD"]
    total_change = sum(prov[(e, "2026-Q3")] - prov[(e, "2026-Q2")] for e in TAX_ENTS)
    ag_change = prov[("NP-AG", "2026-Q3")] - prov[("NP-AG", "2026-Q2")]
    check("tax provision change 375M / Ag drove 354M",
          total_change == 375_000_000 and ag_change == 354_000_000)

    surcharge = [ln for ln in gl if ln["vendor"] == "LoneStar Freight"
                 and ln["period"] == "2026-10" and ln["account_id"] == "5100"]
    check("Oct Dallas COGS surcharge present",
          len(surcharge) == 1 and float(surcharge[0]["debit"]) == 21_500_000)

    due_from = sum(float(ln["debit"]) - float(ln["credit"]) for ln in gl
                   if ln["account_id"] == "1350" and ln["entity"] == "NP-SOFT")
    due_to = sum(float(ln["credit"]) - float(ln["debit"]) for ln in gl
                 if ln["account_id"] == "2150" and ln["entity"] == "NP-ENERGY")
    check("intercompany mismatch is 1.65M", due_from - due_to == 1_650_000)

    accrued = sum(float(ln["credit"]) - float(ln["debit"]) for ln in gl
                  if ln["account_id"] == "2400")
    check("unreversed Sep accrual still in 2400", accrued == 14_200_000)

    unsupported = {ln["journal_id"] for ln in gl
                   if ln["period"] == "2026-10" and ln["memo"] == ""}
    check("exactly one unsupported October journal", len(unsupported) == 1)

    gl_cash = Counter()
    for ln in gl:
        if ln["period"] == "2026-10" and ln["account_id"] == "1000":
            gl_cash[round(float(ln["debit"]) - float(ln["credit"]), 2)] += 1
    bank = Counter()
    for r in load("bank_transactions.csv", OUT):
        bank[round(float(r["amount"]), 2)] += 1
    gl_only = gl_cash - bank
    bank_only = bank - gl_cash
    check("bank rec exceptions as planted",
          sum(gl_only.values()) == 2 and bank_only == Counter({-245000.0: 1}),
          f"(GL-only {dict(gl_only)}, bank-only {dict(bank_only)})")

    subs = load("accrual_submissions.csv", OUT)
    missing = [s for s in subs if s["status"] == "missing"]
    check("two accrual submissions missing", len(missing) == 2)

    if failures:
        print(f"\n{len(failures)} CHECK(S) FAILED - do not use the scaled data.")
        sys.exit(1)
    print("\nAll storyline checks pass on the scaled data.")


if __name__ == "__main__":
    main()
