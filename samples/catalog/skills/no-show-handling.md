# No-Show Handling

Use this skill when a booked party did not arrive, or the guest asks about a no-show charge.

1. Mark a party as a no-show only after 15 minutes past the booking time and two attempts to reach them by `send_sms`.
2. Retrieve the booking and deposit with `query_order_status` and the policy with `retrieve_policy`.
3. If a deposit is held, call `release_deposit` outcome forfeit; without a deposit, no fee is charged for parties under 6.
4. Parties of 6 or more without deposit incur a charge of 25 per head, charged by `process_payment` only if the guest accepted the terms at booking.
5. If the guest later contacts us with an explanation, check `get_flight_status` or ask for evidence of illness and reopen under the deposit-retention-rules skill.
6. Log the no-show in `update_guest_preferences` notes; three no-shows in 12 months trigger mandatory deposits.

Escalate when: the guest disputes a charge or says they were turned away.
Never: charge without confirmed terms acceptance on file.
