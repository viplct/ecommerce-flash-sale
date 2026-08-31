"""Per-user purchase limit: stop a handful of scalpers from hoarding the whole drop.

A flash sale attracts bots: a few "buyers" firing many concurrent requests each. With no
per-user cap, stock goes to whoever sends the most requests — scalpers scoop most of it and
few real people get anything. A cap of one-per-account flips that: each account can win at
most one unit, so the stock spreads across many unique buyers.

Setup: S units, G genuine buyers (one attempt each) + B scalpers (each firing K attempts).
Attempts race in random order; averaged over many trials.

Run:  python sim/per_user_limit.py   (or: make limit)
"""

from __future__ import annotations

import random

S = 100          # units
G = 200          # genuine buyers, one attempt each
B = 20           # scalpers...
K = 50           # ...each firing K concurrent attempts
TRIALS = 3000


def trial(limit: bool, seed: int) -> tuple[int, int, int]:
    rng = random.Random(seed)
    attempts = [('g', i) for i in range(G)] + [('s', i) for i in range(B) for _ in range(K)]
    rng.shuffle(attempts)

    stock = S
    held: dict[tuple[str, int], int] = {}
    for buyer in attempts:
        if stock <= 0:
            break
        if limit and held.get(buyer, 0) >= 1:
            continue                       # this account already has one — reject
        stock -= 1
        held[buyer] = held.get(buyer, 0) + 1

    scalper_units = sum(c for (kind, _), c in held.items() if kind == 's')
    unique_buyers = len(held)
    most_by_one = max(held.values(), default=0)
    return scalper_units, unique_buyers, most_by_one


def main() -> None:
    total_attempts = G + B * K
    print(f"{S} units. {G} genuine (1 attempt each) + {B} scalpers x {K} attempts "
          f"= {total_attempts} requests.")
    print(f"Averaged over {TRIALS:,} trials.\n")
    print(f"  {'policy':<22}{'to scalpers':>13}{'unique buyers':>16}{'most by one':>14}")
    print(f"  {'-' * 63}")
    for label, limit in [('no limit', False), ('per-user limit = 1', True)]:
        su = ub = mo = 0
        for t in range(TRIALS):
            a, b, c = trial(limit, seed=(1 if limit else 0) * 100000 + t)
            su += a; ub += b; mo += c
        su, ub, mo = su / TRIALS, ub / TRIALS, mo / TRIALS
        print(f"  {label:<22}{su:>10.0f} ({su / S * 100:>3.0f}%){ub:>16.0f}{mo:>14.1f}")

    print("\n  No cap: scalpers send most of the requests, so they win most of the stock —")
    print("  a few accounts hoard it and only a few dozen people are served. A one-per-account")
    print("  cap drops the scalper share hard and spreads the stock across all 100 unique")
    print("  buyers. (Pair with auth + bot filtering; the cap is the inventory-side half.)")


if __name__ == "__main__":
    main()
