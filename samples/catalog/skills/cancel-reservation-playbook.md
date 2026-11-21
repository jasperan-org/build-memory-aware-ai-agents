# Cancel a Reservation

Use this skill when the guest wants to cancel a table booking and needs to know the consequences.

1. Find the booking with `query_order_status` and confirm identity from the profile.
2. Call `calculate_cancellation_fee` first and tell the guest what it costs to cancel now before doing anything.
3. Offer alternatives: moving the date with `modify_reservation` keeps the deposit in full.
4. Only after explicit confirmation call `cancel_reservation` with a reason_code.
5. Handle the deposit with `release_deposit` according to the fee calculation and send the written result with `send_followup_email`.
6. If the cancellation window is under 2 hours, offer to put the guest on the waitlist for a later date.

Escalate when: the guest cites illness or bereavement and the fee is above zero.
Never: cancel on ambiguous wording such as maybe; ask again.
