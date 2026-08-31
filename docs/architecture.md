# Architecture walkthrough

A flash sale and a ticket on-sale are the same problem — a contended, finite inventory under
a demand spike — but the *inventory-holding* design is opposite, because their failure modes
differ. A ticket is a unique seat you must not sell twice, reserved the moment it's chosen. A
flash-sale unit is fungible, and most carts are abandoned, so reserving stock at the cart
would waste it on people who never buy. This lab measures the three decisions that follow.

## 1. Oversubscribe the cart, decrement at checkout

`cart_vs_checkout.py`: the choice is *when* stock is decremented.

- **reserve-at-cart** decrements on add-to-cart. Every abandoner locks a unit for the flash
  window, and the cart "sells out" to holds, turning real buyers away. Measured: only 25% of
  shoppers even get an item into the cart, and at 40% abandonment just 60 of 100 units sell.
- **deduct-at-checkout** touches no stock until the order is placed. Add-to-cart succeeds for
  100% of shoppers, and no unit is spent on an abandoner, so the full 100 units sell at every
  abandonment rate.

The counter-intuitive result — "everyone adds to cart but few check out" — is the *correct*
design: it keeps 100% of stock available to the buyers who actually convert.

## 2. A payment TTL on the pending order

`pending_order_timeout.py`: deduct-at-checkout still leaves a gap — a buyer places the order
(stock decremented, order pending) then never pays, stranding the unit. A TTL on the pending
order cancels it and returns the unit to waiting demand. Measured: at 30% non-payment,
utilization goes from 70% (no TTL) back to ~100% (with TTL). This is the seat-hold + reaper
pattern from ticketing, applied one stage later — at the order rather than the cart.

## 3. A per-user purchase cap

`per_user_limit.py`: flash sales attract bots — a few accounts firing many requests each.
With no cap, stock goes to whoever sends the most requests: 20 scalpers scoop 83% and only ~36
people are served. A one-per-account cap drops the scalper share to 20% and spreads the drop
across all 100 unique buyers. The cap is the inventory-side control; it pairs with
authentication, rate limiting, and bot filtering.

## 4. What the checkout inherits from ticketing

The checkout's correctness rests on mechanics proven in `high-demand-ticketing` and unchanged
here: an **atomic decrement** (`UPDATE ... SET stock = stock - :n WHERE stock >= :n`) so a
burst of orders never oversells and multi-unit buys are all-or-nothing; **idempotent payment**
on a client key; a **virtual waiting room** for backpressure when the spike is large; and
per-SKU / per-warehouse counters (the sharded hot-key model). The one deliberate difference:
e-commerce may tolerate a small intentional oversell (backorder / refund) to lift conversion —
a product decision, where ticketing's is zero-tolerance.

## 5. What to take to an interview

- **Reserve stock at the cart only when the unit is unique and rarely abandoned** (a seat).
  For fungible goods with high abandonment, **oversubscribe the cart and decrement at
  checkout** — you sell the full stock instead of wasting it on abandoners.
- **Put a TTL on the pending order** so non-payers don't strand inventory; it's the reaper
  pattern at the order level.
- **Cap purchases per user** to blunt scalpers — the inventory half of anti-bot defense.
- The **checkout decrement must be atomic** and **payment idempotent** — same invariants as
  ticketing; only the reservation point and the oversell tolerance change.
