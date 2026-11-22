# Inventory Count and Reconciliation Policy

**Owner:** Corporate Accounting - Inventory Control
**Applies to:** All NorthPeak stocking locations
**Effective:** 2026-01-01 · Version 1.0

## 1. Purpose

This policy ensures the inventory subledger and the general ledger agree
at every close, and that differences are explained by root cause - never
plugged - before the books are finalized.

## 2. Counts

- Locations run cycle counts monthly on a rotating SKU schedule.
- A full physical count is performed at each location at fiscal year end.
- Counts are recorded in the inventory subledger as of the last calendar
  day of the period.

## 3. Reconciliation

- By **business day 3** of the close, each location's subledger balance is
  tied to the GL inventory control account for that location.
- The reconciliation is location by location; a consolidated total that
  nets a shortage at one location against an overage at another does not
  satisfy this policy.

## 4. Differences

- Any location difference of **$1 million or more**, or **1% or more** of
  the location's balance, must be root-caused and documented before the
  close is finalized.
- The most common root causes, checked in this order:
  1. **Receiving cutoff** - goods physically received and counted, but the
     receiving entry was never posted to the GL.
  2. **Shipping cutoff** - goods shipped and relieved from the subledger
     but not yet relieved from the GL, or the reverse.
  3. **Count or costing errors** - wrong quantity, unit cost, or SKU.
- Differences below the threshold are still logged and trended; a location
  with three consecutive months of differences, at any size, is escalated.

## 5. Adjustments

- No adjustment is posted to force a tie. Every adjustment references its
  root-cause finding (PO, receiving record, or count sheet).
- Adjustments of $1 million or more require entity controller approval.
- An unresolved difference above the threshold blocks close sign-off for
  that location's entity until it is explained; the amount and cause are
  disclosed in the close package.
