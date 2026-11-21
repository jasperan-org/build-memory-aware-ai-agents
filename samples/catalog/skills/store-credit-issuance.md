# Store Credit Issuance

Use this skill when the venue owes the guest a goodwill gesture or a refund in credit rather than cash.

1. Confirm the reason: service failure, cancelled event, venue closure or loyalty gesture.
2. Check limits: agents may issue up to 50 in credit; between 50 and 200 needs manager approval.
3. Call `issue_store_credit` with the reason and an expiry of 12 months.
4. Tell the guest the amount, the expiry date and how to use it at the next booking.
5. Offer cash back through `issue_refund` only when the credit was the guest's own payment and they decline credit.
6. Log the credit on the case with `update_support_ticket`.

Escalate when: the amount exceeds 200 or the guest has received credit 3 times this year.
Never: issue credit as a way to avoid a legitimate refund the guest requested.
