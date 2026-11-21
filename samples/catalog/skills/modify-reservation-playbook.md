# Modify a Reservation

Use this skill when the guest wants to change the time, party size or seating of an existing booking.

1. Fetch the booking with `query_order_status` and confirm the changes requested.
2. Check feasibility with `check_table_availability` for the new time or size; size increases of more than 2 guests need venue approval.
3. Call `modify_reservation` with the new values and the stated reason.
4. If the party grows and a deposit is per head, call `collect_deposit` for the difference; if it shrinks, do not refund within 24 hours of the booking.
5. Confirm the new details and send them with `send_sms`; update the reminder using `set_reminder`.
6. Changes within 2 hours of the booking time must be phoned through to the venue.

Escalate when: the new time is unavailable and the guest refuses alternatives.
Never: cancel and rebook as a way to change a booking, which loses the deposit.
