"""Pending orders + payment timeout: reclaim stock from buyers who order but never pay.

Deducting at checkout still leaves a gap: a buyer places the order (stock is decremented,
order = "pending payment") and then never completes payment. Without a timeout, that unit is
stuck forever — sold to no one. The fix is a TTL on the pending order: if payment doesn't
land in time, cancel it and RETURN the unit to the pool, where remaining demand snaps it up.

This measures stock actually sold (paid) with and without the timeout, as the non-payment
rate rises. Demand exceeds stock (S units, plenty of waiting buyers), so any returned unit
gets resold. A deterministic expected-value model — no randomness.

Run:  python sim/pending_order_timeout.py   (or: make timeout)
"""

from __future__ import annotations

S = 100                 # units
NONPAY = [0.1, 0.3, 0.5]  # fraction of placed orders that never pay in time


def without_release(nonpay: float) -> float:
    """One shot: place min(S, demand) orders; unpaid ones stay stuck forever."""
    placed = S            # demand >> stock, so all stock is ordered
    paid = placed * (1 - nonpay)
    return paid           # the rest is stranded in pending orders


def with_release(nonpay: float) -> float:
    """Unpaid orders time out and return their unit; waiting demand re-buys it."""
    available = float(S)
    paid_total = 0.0
    # Demand is effectively unlimited relative to S, so we only run out of stock, not buyers.
    while available >= 0.5:
        placed = available
        paid = placed * (1 - nonpay)
        paid_total += paid
        available -= paid          # paid units leave for good; the unpaid fraction returns
    return paid_total


def main() -> None:
    print(f"{S} units, demand >> stock. Stock actually SOLD (paid), by non-payment rate:\n")
    print(f"  {'non-payment':>12}{'no timeout: sold':>20}{'with timeout: sold':>22}")
    print(f"  {'-' * 54}")
    for p in NONPAY:
        wo = without_release(p)
        wr = with_release(p)
        print(f"  {p * 100:>10.0f}%  {wo:>13.0f} ({wo / S * 100:>3.0f}%)"
              f"  {wr:>13.0f} ({wr / S * 100:>3.0f}%)")

    print("\n  Without a timeout, every unpaid order permanently strands its unit — at 30%")
    print("  non-payment you sell only 70% of stock. A payment TTL cancels the unpaid order")
    print("  and returns the unit; waiting demand buys it, driving utilization back to ~100%.")
    print("  (This is the hold/reaper pattern moved to the ORDER level — same idea, later stage.)")


if __name__ == "__main__":
    main()
