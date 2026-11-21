# Deposit Retention Rules

Use this skill when the guest asks whether a deposit is kept, refunded, forfeited or moved after a change or cancellation.

1. Find the reservation and the held amount with `query_order_status`.
2. Call `calculate_cancellation_fee` with `include_deposit` true to get the exact refundable amount and deadline.
3. Standard window: cancellation more than 48 hours before the booking returns 100 percent; between 48 and 24 hours returns 50 percent; under 24 hours or a no-show forfeits it.
4. Exceptions that keep the deposit alive: illness with a note, venue closure, and documented travel disruption. In these cases offer transfer_to_new_date through `release_deposit`.
5. Explain the outcome in one sentence with the amount and the date it will appear, normally 5 to 7 business days for card refunds.
6. Record the decision on the reservation with `update_support_ticket` if a ticket exists.

Escalate when: the deposit exceeds 500 in the quote currency or the guest disputes the policy.
Never: override the schedule yourself; only the venue manager can waive a forfeit.
