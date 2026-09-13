# ADR-0002 — Pending-order payment TTL and a per-user purchase cap

**Status:** Accepted · **Context:** two leaks after deduct-at-checkout — non-payers and scalpers

## Context

Decrementing at checkout closes the abandoned-cart leak but opens two smaller ones: a buyer
can place an order (stock decremented, order pending) and never pay, stranding the unit; and a
few bots can fire many requests each and hoard the whole drop. Both waste stock that real,
paying buyers wanted.

## Decision

- **Put a TTL on every pending order.** If payment doesn't complete within the window, cancel
  the order and return the unit to available stock, where waiting demand re-buys it. Run the
  reclaim on a schedule (or via a delayed job / DynamoDB TTL).
- **Cap purchases per user** (e.g. one unit per account) for the flash SKU, enforced at the
  atomic decrement. This is the inventory-side half of anti-bot defense.

## Rationale

- Pending-order TTL, measured: at 30% non-payment, stock actually sold rises from 70% (no TTL)
  to ~100% (with TTL) because reclaimed units are resold. Without it, every non-payer
  permanently strands a unit.
- Per-user cap, measured (100 units, 200 genuine + 20 scalpers x 50 requests): the scalper
  share drops from 83% to 20% and unique buyers served rise from ~36 to 100. Stock goes to
  more real people instead of whoever sends the most requests.

## Consequences

**Positive** — stock utilization approaches 100% under both abandonment-after-order and bot
pressure; the drop reaches many unique buyers.

**Negative / trade-offs** — the TTL adds a reclaim job and a race between "pay" and "reclaim"
(resolve by locking/checking the order's state on both paths, as in the ticketing lab's
convert-vs-reap). The per-user cap needs identity (account / verified phone) to be meaningful
and must be paired with rate limiting and bot filtering, since a cap alone is beaten by many
fake accounts.

## Defense in depth against Sybil attacks

A per-account cap assumes one person = one account; a bot creates thousands of free fake
accounts (a Sybil attack) and walks around it. No single control wins, so stack layers that
each spend a *different scarce* bot resource. Measured scalper share of 100 units, cumulative:

```
no defense              94%      + payment/card cap      15%
+ per-user cap          94%      + account-age gate       0%  (but 25 real first-timers blocked)
+ datacenter/ASN block  69%
```

Anchor on resources bots can't cheaply mass-produce — **cards, phone numbers, aged accounts,
non-datacenter IPs**. Each layer has a cost or a gap: IP caps false-positive on CGNAT (use IP
for rate-limiting and datacenter/proxy blocking, not a hard purchase cap); an account-age gate
also excludes genuine first-time buyers; CAPTCHA can be farmed. It is an economics game — raise
the attacker's cost above their expected profit — plus post-hoc fraud scoring to cancel and
refund suspicious orders after the fact.

## Notes

The TTL/reclaim is the seat-hold reaper from `high-demand-ticketing`, applied at the order
level; the "pay vs reclaim" race is resolved the same way (lock the row, re-check state).
