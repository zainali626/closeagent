"""Generate CloseAgent's synthetic finance dataset - Koch-scale edition.

Deterministic (seeded). Implements docs/dataset_design.md: a fictional
conglomerate patterned on Koch Industries' shape (~$115B annual revenue,
9 entities across energy, chemicals, building products, electronics, ag,
glass, software, capital). Dollar amounts are at that scale; journal
volume is a sample.

Planted storylines (all verified by scripts/verify_data.py):
- Professional services ~22% over budget in October (consultants engaged)
- One exact duplicate journal in October (Software's CloudNine bill)
- Dallas COGS runs hot from a LoneStar Freight fuel surcharge
- Q3 tax provision +$375M, driven by Ag & Fertilizer (+$354M)
- Inventory ties in Dallas but not Chicago (missing receiving, $48.5M)
- Intercompany mismatch: Software billed Energy $22M, Energy booked $20.35M
- September marketing accrual ($14.2M) never reversed - double-counted
- One October journal posted with no supporting memo
- Bank rec exceptions: unrecorded $245K fee, one outstanding rent check,
  one deposit in transit
- Two accrual submissions still missing (Legal, IT)

Run: python scripts/generate_data.py  (writes CSVs to data/raw/)
"""

import csv
import random
from pathlib import Path

random.seed(42)
OUT = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

M = 1_000_000
ENTITIES = {
    "NP-PARENT": "NorthPeak Industries (Parent)",
    "NP-ENERGY": "NorthPeak Energy",
    "NP-CHEM": "NorthPeak Chemicals",
    "NP-BUILD": "NorthPeak Building Products",
    "NP-ELEC": "NorthPeak Electronics",
    "NP-AG": "NorthPeak Ag & Fertilizer",
    "NP-GLASS": "NorthPeak Glass",
    "NP-SOFT": "NorthPeak Software",
    "NP-CAP": "NorthPeak Capital",
}
PHYSICAL = ["NP-ENERGY", "NP-CHEM", "NP-BUILD", "NP-ELEC", "NP-AG", "NP-GLASS"]
MONTHS = ["2026-08", "2026-09", "2026-10"]

ACCOUNTS = [
    ("1000", "Cash", "Asset"),
    ("1300", "Accounts Receivable", "Asset"),
    ("1350", "Due from Affiliates", "Asset"),
    ("1400", "Inventory", "Asset"),
    ("1500", "Prepaid Expenses", "Asset"),
    ("1550", "Accumulated Depreciation", "Asset"),
    ("2100", "Accounts Payable", "Liability"),
    ("2150", "Due to Affiliates", "Liability"),
    ("2200", "Accrued Payroll", "Liability"),
    ("2300", "Tax Payable", "Liability"),
    ("2400", "Accrued Expenses", "Liability"),
    ("2500", "Deferred Revenue", "Liability"),
    ("3000", "Common Stock", "Equity"),
    ("3100", "Retained Earnings", "Equity"),
    ("4100", "Sales Revenue", "Revenue"),
    ("4200", "Service Revenue", "Revenue"),
    ("4300", "Other Income", "Revenue"),
    ("5100", "Cost of Goods Sold", "Expense"),
    ("6100", "Professional Services", "Expense"),
    ("6200", "Payroll Expense", "Expense"),
    ("6300", "Rent Expense", "Expense"),
    ("6400", "Software Subscriptions", "Expense"),
    ("6450", "Intercompany Services Expense", "Expense"),
    ("6500", "Utilities", "Expense"),
    ("6600", "Marketing Expense", "Expense"),
    ("6700", "Insurance Expense", "Expense"),
    ("6800", "Depreciation Expense", "Expense"),
    ("6900", "Travel Expense", "Expense"),
    ("7100", "Interest Expense", "Expense"),
]

# Monthly run-rates per entity, in $M.
BASE = {
    "NP-PARENT": {"revenue": 0, "payroll": 68, "rent": 12, "prof": 6.5},
    "NP-ENERGY": {"revenue": 2850, "payroll": 212, "rent": 38, "prof": 8.2},
    "NP-CHEM": {"revenue": 1420, "payroll": 118, "rent": 21, "prof": 4.6},
    "NP-BUILD": {"revenue": 1680, "payroll": 142, "rent": 26, "prof": 5.1},
    "NP-ELEC": {"revenue": 1150, "payroll": 164, "rent": 19, "prof": 3.8},
    "NP-AG": {"revenue": 890, "payroll": 74, "rent": 14, "prof": 2.9},
    "NP-GLASS": {"revenue": 640, "payroll": 88, "rent": 12, "prof": 2.2},
    "NP-SOFT": {"revenue": 380, "payroll": 121, "rent": 9, "prof": 4.4},
    "NP-CAP": {"revenue": 590, "payroll": 47, "rent": 7, "prof": 4.3},
}
CHANNELS = [("Direct", "Dallas", 0.45), ("Partner", "Chicago", 0.30), ("Online", "Remote", 0.25)]

lines = []
_journal_seq = {m: 0 for m in MONTHS}


def journal(period, day, entity, entries, memo):
    _journal_seq[period] += 1
    jid = f"JE-{period.replace('-', '')}-{_journal_seq[period]:03d}"
    date = f"{period}-{day:02d}"
    for acct, debit, credit, dims in entries:
        lines.append(
            {
                "journal_id": jid, "journal_date": date, "period": period,
                "entity": entity, "account_id": acct,
                "debit": f"{debit:.2f}", "credit": f"{credit:.2f}",
                "region": dims.get("region", ""), "channel": dims.get("channel", ""),
                "cost_center": dims.get("cost_center", ""),
                "vendor": dims.get("vendor", ""), "location": dims.get("location", ""),
                "memo": memo,
            }
        )
    return jid


def jit(amount, pct=3):
    return round(amount * (1 + random.uniform(-pct, pct) / 100), 2)


budgets = []


def budget(entity, account_id, period, amount):
    budgets.append({"entity": entity, "account_id": account_id, "period": period,
                    "budget_amount": f"{amount:.2f}"})


for period in MONTHS:
    for ent, b in BASE.items():
        rev = b["revenue"] * M
        if rev > 0:
            for channel, region, share in CHANNELS:
                amt = jit(rev * share)
                journal(period, 6, ent,
                        [("1300", amt, 0, {"channel": channel, "region": region, "cost_center": "SALES"}),
                         ("4100", 0, amt, {"channel": channel, "region": region, "cost_center": "SALES"})],
                        f"{channel} sales - {period}")
            budget(ent, "4100", period, rev)
            for channel, region, share in CHANNELS:
                amt = jit(rev * share * 0.8)
                journal(period, 24, ent,
                        [("1000", amt, 0, {"channel": channel}),
                         ("1300", 0, amt, {"channel": channel})],
                        "Customer collections")
        if ent in PHYSICAL:
            for loc, share in [("Dallas", 0.55), ("Chicago", 0.45)]:
                amt = jit(rev * 0.38 * share)
                journal(period, 9, ent,
                        [("1400", amt, 0, {"location": loc, "vendor": "ScaleWorks Inc"}),
                         ("2100", 0, amt, {"vendor": "ScaleWorks Inc"})],
                        f"Inventory receiving - {loc}")
                amt = jit(rev * 0.34 * share)
                journal(period, 27, ent,
                        [("5100", amt, 0, {"region": loc, "location": loc, "cost_center": "OPS"}),
                         ("1400", 0, amt, {"location": loc})],
                        f"COGS relief - {loc}")
            budget(ent, "5100", period, rev * 0.34)
        payroll_amt = jit(b["payroll"] * M)
        journal(period, 15, ent,
                [("6200", payroll_amt, 0, {"cost_center": "OPS"}),
                 ("1000", 0, payroll_amt, {})], "Monthly payroll")
        budget(ent, "6200", period, b["payroll"] * M)
        rent_amt = b["rent"] * M
        journal(period, 3, ent,
                [("6300", rent_amt, 0, {"region": "Dallas", "cost_center": "ADMIN"}),
                 ("1000", 0, rent_amt, {})], "Office rent")
        budget(ent, "6300", period, rent_amt)
        prof_amt = jit(b["prof"] * M, pct=1)
        journal(period, 11, ent,
                [("6100", prof_amt, 0, {"vendor": "Meridian Consulting", "cost_center": "ADMIN"}),
                 ("2100", 0, prof_amt, {"vendor": "Meridian Consulting"})],
                "Advisory retainer - Meridian Consulting")
        budget(ent, "6100", period, b["prof"] * M)
        util_amt, mkt_amt = jit(4.1 * M), jit(16.5 * M)
        journal(period, 8, ent,
                [("6500", util_amt, 0, {"cost_center": "ADMIN"}),
                 ("1000", 0, util_amt, {})], "Utilities")
        journal(period, 18, ent,
                [("6600", mkt_amt, 0, {"cost_center": "SALES"}),
                 ("1000", 0, mkt_amt, {})], "Marketing programs")
        journal(period, 28, ent,
                [("6800", 28 * M, 0, {"cost_center": "ADMIN"}),
                 ("1550", 0, 28 * M, {})], "Depreciation")

# Software subscriptions (October carries the planted duplicate)
for period in MONTHS:
    for ent in BASE:
        amt = 12_400_000 if ent == "NP-SOFT" else 3_900_000
        journal(period, 5, ent,
                [("6400", amt, 0, {"vendor": "CloudNine", "cost_center": "ADMIN"}),
                 ("1000", 0, amt, {"vendor": "CloudNine"})],
                "CloudNine subscription")
        budget(ent, "6400", period, amt)

# PLANTED: exact duplicate of October NP-SOFT software journal
journal("2026-10", 5, "NP-SOFT",
        [("6400", 12_400_000, 0, {"vendor": "CloudNine", "cost_center": "ADMIN"}),
         ("1000", 0, 12_400_000, {"vendor": "CloudNine"})],
        "CloudNine subscription")

# PLANTED: October professional services spike - consultants engaged
journal("2026-10", 14, "NP-ENERGY",
        [("6100", 6_200_000, 0, {"vendor": "Meridian Consulting", "cost_center": "ADMIN"}),
         ("2100", 0, 6_200_000, {"vendor": "Meridian Consulting"})],
        "Systems project assessment - Meridian Consulting")
journal("2026-10", 21, "NP-SOFT",
        [("6100", 3_200_000, 0, {"vendor": "Meridian Consulting", "cost_center": "ADMIN"}),
         ("2100", 0, 3_200_000, {"vendor": "Meridian Consulting"})],
        "Close support engagement - Meridian Consulting")

# PLANTED: Dallas COGS fuel surcharge from LoneStar Freight (Sep, Oct)
for period, amt in [("2026-09", 14_000_000), ("2026-10", 21_500_000)]:
    journal(period, 26, "NP-ENERGY",
            [("5100", amt, 0, {"region": "Dallas", "location": "Dallas",
                               "vendor": "LoneStar Freight", "cost_center": "OPS"}),
             ("2100", 0, amt, {"vendor": "LoneStar Freight"})],
            "Fuel surcharge - LoneStar Freight")

# PLANTED: intercompany billing - Software bills Energy $22M/month for
# shared IT services. In October, Energy recorded only $20.35M.
for period in MONTHS:
    recorded = 20_350_000 if period == "2026-10" else 22_000_000
    journal(period, 20, "NP-SOFT",
            [("1350", 22_000_000, 0, {"cost_center": "ADMIN"}),
             ("4200", 0, 22_000_000, {"cost_center": "ADMIN"})],
            f"Intercompany IT services billed to NP-ENERGY - {period}")
    journal(period, 20, "NP-ENERGY",
            [("6450", recorded, 0, {"cost_center": "ADMIN"}),
             ("2150", 0, recorded, {"cost_center": "ADMIN"})],
            f"Intercompany IT services from NP-SOFT - {period}")

# PLANTED: September marketing accrual never reversed; the real invoice
# was paid in October, so the $14.2M cost is counted twice.
journal("2026-09", 30, "NP-BUILD",
        [("6600", 14_200_000, 0, {"vendor": "Brightline Media", "cost_center": "SALES"}),
         ("2400", 0, 14_200_000, {"vendor": "Brightline Media"})],
        "Accrue Sep agency campaign - Brightline Media")
journal("2026-10", 12, "NP-BUILD",
        [("6600", 14_200_000, 0, {"vendor": "Brightline Media", "cost_center": "SALES"}),
         ("1000", 0, 14_200_000, {"vendor": "Brightline Media"})],
        "Brightline Media - Sep campaign invoice paid")

# PLANTED: an October journal posted with no supporting memo at all
journal("2026-10", 19, "NP-PARENT",
        [("6900", 1_475_000, 0, {"cost_center": "ADMIN"}),
         ("1000", 0, 1_475_000, {})],
        "")

# PLANTED: Chicago receiving entry in the GL that never reached the
# inventory subledger ($48.5M)
journal("2026-10", 16, "NP-ENERGY",
        [("1400", 48_500_000, 0, {"location": "Chicago", "vendor": "ScaleWorks Inc"}),
         ("2100", 0, 48_500_000, {"vendor": "ScaleWorks Inc"})],
        "Inventory receiving - Chicago - PO 8841")

# Tax provision by entity and quarter, $M (Q3 jump driven by Ag)
tax_rows = [
    ("NP-PARENT", "2026-Q2", 1240, 186), ("NP-ENERGY", "2026-Q2", 5860, 402),
    ("NP-CHEM", "2026-Q2", 2310, 158), ("NP-AG", "2026-Q2", 1385, 96),
    ("NP-BUILD", "2026-Q2", 1720, 118),
    ("NP-PARENT", "2026-Q3", 1205, 181), ("NP-ENERGY", "2026-Q3", 6140, 428),
    ("NP-CHEM", "2026-Q3", 2420, 166), ("NP-AG", "2026-Q3", 6480, 450),
    ("NP-BUILD", "2026-Q3", 1610, 110),
]

# Inventory subledger: ties to the GL by location, except Chicago, which
# is short exactly the missing $48.5M receipt.
gl_inv = {"Dallas": 0.0, "Chicago": 0.0}
for ln in lines:
    if ln["account_id"] == "1400" and ln["location"] in gl_inv:
        gl_inv[ln["location"]] += float(ln["debit"]) - float(ln["credit"])

SKUS = [("SCALE-200", "Industrial scale 200kg", 18500.0, 0.34),
        ("SCALE-450", "Industrial scale 450kg", 29000.0, 0.26),
        ("WIFI-AP7", "WiFi access point AP7", 4200.0, 0.22),
        ("WIFI-CTRL2", "WiFi controller CTRL2", 11500.0, 0.18)]
subledger = []
for loc in ["Dallas", "Chicago"]:
    target = gl_inv[loc] - (48_500_000 if loc == "Chicago" else 0)
    running = 0.0
    for i, (sku, desc, cost, w) in enumerate(SKUS):
        value = round(target * w, 2) if i < len(SKUS) - 1 else round(target - running, 2)
        running += value
        qty = max(1, round(value / cost))
        subledger.append({"sku": sku, "description": desc, "location": loc,
                          "quantity": qty, "unit_cost": f"{cost:.2f}",
                          "value": f"{qty * cost:.2f}"})
    total = sum(float(r["value"]) for r in subledger if r["location"] == loc)
    plug = round(target - total, 2)
    last = [r for r in subledger if r["location"] == loc][-1]
    last["value"] = f"{float(last['value']) + plug:.2f}"

# Bank statement for October, derived from GL cash lines with three
# planted exceptions: unrecorded $245K fee (bank only), one outstanding
# parent rent check (GL only), one Energy deposit in transit (GL only).
bank_rows = []
skipped_check = skipped_deposit = False
for ln in lines:
    if ln["period"] != "2026-10" or ln["account_id"] != "1000":
        continue
    amount = float(ln["debit"]) - float(ln["credit"])
    if (not skipped_check and ln["entity"] == "NP-PARENT"
            and ln["memo"] == "Office rent" and amount < 0):
        skipped_check = True
        continue
    if (not skipped_deposit and ln["entity"] == "NP-ENERGY"
            and ln["memo"] == "Customer collections" and amount > 0):
        skipped_deposit = True
        continue
    bank_rows.append({"bank_date": ln["journal_date"],
                      "description": f"{ln['memo']} - {ln['entity']}",
                      "amount": f"{amount:.2f}", "reference": ln["journal_id"]})
bank_rows.append({"bank_date": "2026-10-31", "description": "Account analysis fee",
                  "amount": "-245000.00", "reference": ""})
bank_rows.sort(key=lambda r: r["bank_date"])

# Accrual submissions the close is waiting on (2 of 5 still missing)
accrual_rows = [
    {"department": "Finance", "item": "Audit fee accrual", "expected_amount": "18500000.00", "status": "received", "period": "2026-10"},
    {"department": "Legal", "item": "Outside counsel - October invoice", "expected_amount": "9200000.00", "status": "missing", "period": "2026-10"},
    {"department": "Marketing", "item": "Brightline Media campaign accrual", "expected_amount": "14200000.00", "status": "received", "period": "2026-10"},
    {"department": "Operations", "item": "Warehouse overtime accrual", "expected_amount": "6700000.00", "status": "received", "period": "2026-10"},
    {"department": "IT", "item": "CloudNine true-up invoice", "expected_amount": "3100000.00", "status": "missing", "period": "2026-10"},
]


def write_csv(name, rows, fields):
    with open(OUT / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


write_csv("chart_of_accounts.csv",
          [{"account_id": a, "account_name": n, "account_type": t} for a, n, t in ACCOUNTS],
          ["account_id", "account_name", "account_type"])
write_csv("gl_lines.csv", lines,
          ["journal_id", "journal_date", "period", "entity", "account_id", "debit",
           "credit", "region", "channel", "cost_center", "vendor", "location", "memo"])
write_csv("budgets.csv", budgets, ["entity", "account_id", "period", "budget_amount"])
write_csv("tax_provision.csv",
          [{"entity": e, "quarter": q, "pretax_income": f"{p * M:.2f}",
            "provision_amount": f"{t * M:.2f}"} for e, q, p, t in tax_rows],
          ["entity", "quarter", "pretax_income", "provision_amount"])
write_csv("inventory_subledger.csv", subledger,
          ["sku", "description", "location", "quantity", "unit_cost", "value"])
write_csv("gl_inventory_control.csv",
          [{"location": loc, "gl_balance": f"{bal:.2f}", "as_of_date": "2026-10-31"}
           for loc, bal in gl_inv.items()],
          ["location", "gl_balance", "as_of_date"])
write_csv("bank_transactions.csv", bank_rows,
          ["bank_date", "description", "amount", "reference"])
write_csv("accrual_submissions.csv", accrual_rows,
          ["department", "item", "expected_amount", "status", "period"])

print(f"gl_lines: {len(lines)} rows, {len({ln['journal_id'] for ln in lines})} journals")
print(f"GL inventory: {gl_inv}")
print(f"Monthly revenue run-rate: ${sum(b['revenue'] for b in BASE.values()):,}M")
