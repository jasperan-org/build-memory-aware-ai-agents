# Deposit Collection

Use this skill when a booking or event requires a deposit and the guest needs to pay it.

1. State the amount, the reason and the refund window before asking for any payment detail.
2. Use `collect_deposit` with mode authorize_only for bookings more than 14 days away, capture otherwise.
3. Pass the tokenised method only; if no token exists ask the guest to add a card through the secure link, never in chat.
4. Confirm the receipt with the amount and the reservation reference through `send_followup_email`.
5. Set a reminder with `set_reminder` for the free-cancellation deadline, 48 hours before the booking.
6. On failure, move to the payment-failure-recovery skill and keep the table held for 30 minutes.

Escalate when: the guest asks to pay by bank transfer or cash.
Never: write a full card number into notes or messages.
