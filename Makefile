.PHONY: help funnel timeout limit all

# Pure standard library — no dependencies, no services, nothing to install.
PY ?= python3

help:
	@echo "make funnel   - reserve-at-cart vs deduct-at-checkout as abandonment rises"
	@echo "make timeout  - pending-order payment TTL reclaims stock from non-payers"
	@echo "make limit    - per-user cap stops scalpers hoarding the drop"
	@echo "make sybil    - why a per-user cap alone fails, and defense in depth"
	@echo "make all      - run all four"

funnel:
	$(PY) sim/cart_vs_checkout.py

timeout:
	$(PY) sim/pending_order_timeout.py

limit:
	$(PY) sim/per_user_limit.py

sybil:
	$(PY) sim/sybil_defense.py

all: funnel timeout limit sybil
