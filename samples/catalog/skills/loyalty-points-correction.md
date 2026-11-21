# Loyalty Points Correction

Use this skill when the guest says points or tier credit are missing after a visit, or a redemption failed.

1. Ask for the visit date and venue; call `get_loyalty_balance` with `include_history` true.
2. Points post within 48 hours of payment; do not act on visits less than 2 days old.
3. If the visit is older and no earning appears, look up the payment with `query_order_status` to confirm it was linked to the profile.
4. Missing points are 1 per currency unit spent, excluding tax and tips.
5. Corrections up to 500 points can be made through a ticket with `create_support_ticket` category loyalty.
6. Tell the guest the expected posting date.

Escalate when: the missing amount is above 500 points or a tier downgrade is involved.
Never: edit a balance directly.
