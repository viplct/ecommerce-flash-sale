# ADR-0001 — Oversubscribe the cart, decrement stock at checkout

**Status:** Accepted · **Context:** where to decrement inventory in a flash sale

## Context

A flash sale has demand far above stock and a high cart-abandonment rate. The reservation
point — when a unit is removed from available inventory — decides whether abandoners waste
stock and whether real buyers can even start a checkout. Ticketing reserves at the cart (a
hold) because a seat is unique and rarely abandoned; copying that for fungible flash-sale
goods starves real buyers.

## Decision

Do **not** reserve stock when an item is added to the cart. Let the cart oversubscribe
(add-to-cart always succeeds) and perform the **atomic decrement only at order placement**
(`UPDATE ... SET stock = stock - :n WHERE stock >= :n`). Reserve-at-cart is reserved for
scarce, low-abandonment, assigned units (seats), not fungible flash-sale stock.

## Rationale

Measured (400 shoppers, 100 units), as abandonment rises:

```
abandon   reserve-at-cart (sold / wasted / add-cart)   deduct-at-checkout (sold / wasted / add-cart)
  20%          80 / 20 / 25%                                100 / 0 / 100%
  40%          60 / 40 / 25%                                100 / 0 / 100%
  60%          40 / 60 / 25%                                100 / 0 / 100%
```

- reserve-at-cart wastes one unit per abandoner and sells the cart out to holds, so only 25%
  of shoppers can add to cart and stock sold falls with abandonment.
- deduct-at-checkout keeps 100% of stock available to converting buyers and sells the full
  stock regardless of abandonment.

## Consequences

**Positive** — full stock reaches real buyers; add-to-cart never fails; no reaper needed for
cart holds; the hot decrement happens once, at a lower rate (only actual orders).

**Negative / trade-offs** — a shopper can have an item in the cart and still hit "sold out" at
checkout (worse UX for the loser than a guaranteed hold). Mitigate with clear "not reserved
until checkout" messaging and, for a few very hot SKUs, an optional short soft-reserve.

## Notes

The checkout decrement must be **atomic** (never read-then-write) and buying N units is one
all-or-nothing update — the same primitive proven in the `high-demand-ticketing` lab.
