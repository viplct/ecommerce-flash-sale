"""Defense in depth vs a Sybil attack: a per-user cap alone is defeated by fake accounts.

A per-account purchase cap assumes one person = one account. A bot creates thousands of
free fake accounts (a Sybil attack), so the cap barely dents it. No single control wins;
you stack layers that each attack a DIFFERENT scarce resource the bot has to spend:

  - per-user cap        -> beaten: fake accounts are unlimited and cheap
  - datacenter/ASN block-> real buyers aren't on cloud/proxy IPs; cuts most bot traffic
  - payment/card cap    -> real cards are expensive; caps the bot at its number of cards
  - account-age gate     -> Sybil accounts are brand new -> stops them cold, BUT it also
                            locks out genuine first-time buyers (real collateral)

This measures the scalper's share of stock as each layer is added, and the collateral the
age gate inflicts. Averaged over seeded trials.

Run:  python sim/sybil_defense.py   (or: make sybil)
"""

from __future__ import annotations

import random

S = 100              # units
GEN = 200            # genuine buyers (one request each)
GEN_NEW = 40         # of those, first-timers (new accounts) — collateral for the age gate
BOT_REQ = 3000       # bot requests (Sybil: a unique fake NEW account per request)
BOT_CARDS = 15       # real cards the bot ring has (the expensive, scarce resource)
BOT_DATACENTER = 0.85  # fraction of bot requests from cloud/proxy IPs (detectable)
TRIALS = 1500

LAYERS = [
    ("no defense", set()),
    ("+ per-user cap", {"account"}),
    ("+ datacenter/ASN block", {"account", "datacenter"}),
    ("+ payment/card cap", {"account", "datacenter", "card"}),
    ("+ account-age gate", {"account", "datacenter", "card", "age"}),
]


def build_requests(rng: random.Random) -> list[dict]:
    reqs = []
    # Genuine: unique account + unique card, residential IP, one request each.
    for i in range(GEN):
        reqs.append({
            "bot": False, "account": ("g", i), "card": ("g", i),
            "datacenter": False, "new": i < GEN_NEW,
        })
    # Bot: a unique NEW fake account per request (Sybil), cards drawn from a small pool.
    for j in range(BOT_REQ):
        reqs.append({
            "bot": True, "account": ("b", j), "card": ("b", rng.randrange(BOT_CARDS)),
            "datacenter": rng.random() < BOT_DATACENTER, "new": True,
        })
    rng.shuffle(reqs)
    return reqs


def run(reqs: list[dict], filters: set[str]) -> tuple[int, int, int]:
    stock = S
    won_accounts: set = set()
    won_cards: set = set()
    scalper = genuine = blocked_new_genuine = 0

    for r in reqs:
        if stock <= 0:
            break
        # Filters that reject before the purchase (each targets a different resource).
        if "age" in filters and r["new"]:
            if not r["bot"]:
                blocked_new_genuine += 1     # a real first-timer turned away (collateral)
            continue
        if "datacenter" in filters and r["datacenter"]:
            continue
        if "account" in filters and r["account"] in won_accounts:
            continue
        if "card" in filters and r["card"] in won_cards:
            continue

        stock -= 1
        won_accounts.add(r["account"])
        won_cards.add(r["card"])
        if r["bot"]:
            scalper += 1
        else:
            genuine += 1

    return scalper, genuine, blocked_new_genuine


def main() -> None:
    print(f"{S} units. {GEN} genuine ({GEN_NEW} first-timers) vs a bot with UNLIMITED fake "
          f"accounts,\n{BOT_CARDS} cards, {BOT_REQ} requests ({BOT_DATACENTER:.0%} from "
          f"datacenter/proxy IPs). Averaged over {TRIALS:,} trials.\n")
    print(f"  {'defense (cumulative)':<26}{'to scalpers':>13}{'to genuine':>12}"
          f"{'real buyers blocked':>21}")
    print(f"  {'-' * 72}")
    agg = {label: [0, 0, 0] for label, _ in LAYERS}
    for t in range(TRIALS):
        reqs = build_requests(random.Random(t))   # one request stream, all layers see it
        for label, filters in LAYERS:
            a, b, c = run(reqs, filters)
            agg[label][0] += a; agg[label][1] += b; agg[label][2] += c

    for label, _ in LAYERS:
        sc, ge, bl = (x / TRIALS for x in agg[label])
        print(f"  {label:<26}{sc:>9.0f} ({sc / S * 100:>3.0f}%){ge:>12.0f}{bl:>21.0f}")

    print("\n  A per-user cap alone barely moves the scalper share — fake accounts are free")
    print("  (the Sybil attack). Each further layer spends a scarcer bot resource: blocking")
    print("  cloud/proxy IPs cuts most bot traffic, the card cap pins it to its few real")
    print("  cards, and the age gate stops brand-new Sybil accounts entirely — but that last")
    print("  layer also locks out real first-time buyers, so it's a trade-off, not a free win.")


if __name__ == "__main__":
    main()
