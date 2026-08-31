"""The flash-sale funnel: reserve-at-cart vs deduct-at-checkout.

A ticketing seat is reserved the moment it's in your cart (a hold decrements stock). A
flash-sale item usually is NOT: add-to-cart touches nothing, and stock is only decremented
at ORDER PLACEMENT. That is why "everyone can add to cart but few check out succeed" — and
it is the *correct* design when many shoppers abandon their cart.

This measures both, as the abandonment rate rises (demand > stock: N shoppers, S units):

  - reserve-at-cart: add-to-cart takes a unit. Abandoners lock stock they never buy, and
    real buyers are turned away at the cart because stock "sold out" to holds.
  - deduct-at-checkout: add-to-cart is free (100% succeed); only buyers reach the atomic
    decrement at checkout, so no unit is ever wasted on an abandoner.

Run:  python sim/cart_vs_checkout.py   (or: make funnel)
"""

from __future__ import annotations

import random

S = 100          # units in the flash sale
N = 400          # shoppers arriving (demand far exceeds stock)
TRIALS = 4000
ABANDON = [0.0, 0.2, 0.4, 0.6]   # fraction who add to cart but never check out


def trial(abandon: float, seed: int) -> tuple[float, ...]:
    rng = random.Random(seed)
    # True = a buyer who will pay; False = an abandoner (adds to cart, never checks out).
    shoppers = [rng.random() >= abandon for _ in range(N)]
    rng.shuffle(shoppers)  # random arrival order

    # reserve-at-cart: add-to-cart itself reserves (decrements) a unit.
    stock, r_cart, r_sold, r_wasted, r_lost = S, 0, 0, 0, 0
    for is_buyer in shoppers:
        if stock > 0:
            stock -= 1
            r_cart += 1
            if is_buyer:
                r_sold += 1        # buyer will later pay this held unit
            else:
                r_wasted += 1      # abandoner locks it for the whole flash window
        elif is_buyer:
            r_lost += 1            # a real buyer couldn't even add to cart

    # deduct-at-checkout: cart is free; only buyers reach the atomic decrement.
    stock, d_sold, d_lost = S, 0, 0
    for is_buyer in shoppers:
        if is_buyer:
            if stock > 0:
                stock -= 1
                d_sold += 1
            else:
                d_lost += 1

    return (r_cart / N * 100, r_sold, r_wasted, r_lost,
            100.0, d_sold, 0, d_lost)


def main() -> None:
    print(f"{N} shoppers, {S} units, demand >> stock. Averaged over {TRIALS:,} trials.\n")
    print(f"  {'abandon':>8}  {'strategy':<20}{'add-to-cart':>12}{'sold':>7}"
          f"{'wasted':>9}{'buyers lost':>13}")
    print(f"  {'-' * 71}")
    for a in ABANDON:
        agg = [0.0] * 8
        for t in range(TRIALS):
            for i, v in enumerate(trial(a, seed=a * 1000 + t)):
                agg[i] += v
        agg = [x / TRIALS for x in agg]
        rc, rs, rw, rl, dc, ds, dw, dl = agg
        print(f"  {a * 100:>6.0f}%  {'reserve-at-cart':<20}{rc:>11.0f}%{rs:>7.0f}"
              f"{rw:>9.0f}{rl:>13.0f}")
        print(f"  {'':>8}  {'deduct-at-checkout':<20}{dc:>11.0f}%{ds:>7.0f}"
              f"{dw:>9.0f}{dl:>13.0f}")
        print(f"  {'-' * 71}")

    print("\n  reserve-at-cart wastes a unit on every abandoner (and 'sells out' the cart to")
    print("  holds, turning real buyers away early). deduct-at-checkout keeps 100% of stock")
    print("  available to actual buyers → it sells the FULL stock and wastes nothing.")
    print("  That's why a flash sale lets the cart oversubscribe and only decrements at order.")


if __name__ == "__main__":
    main()
