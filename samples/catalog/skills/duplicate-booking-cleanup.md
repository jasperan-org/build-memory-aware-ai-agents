# Duplicate Booking Cleanup

Use this skill when a guest has two bookings for the same time, or double deposits appear.

1. Find all bookings for the guest on that date with `query_order_status` and compare time, venue and party size.
2. Ask which one to keep; if both are at the same venue keep the earlier created one by default.
3. Cancel the other with `cancel_reservation` reason_code duplicate; duplicates are never subject to a fee.
4. If a deposit was taken twice, call `release_deposit` with outcome refund for the extra one and confirm the amount.
5. Look for double charges in `process_payment` history; refund extras using `issue_refund`.
6. Send a short note by `send_followup_email` with the booking that stands.
7. Check why it happened: tell support if the same user did it twice within 10 minutes.

Escalate when: the amounts differ or the second charge is on another card.
Never: cancel both bookings.
