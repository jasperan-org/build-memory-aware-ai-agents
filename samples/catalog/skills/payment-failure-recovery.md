# Payment Failure Recovery

Use this skill when a card payment, deposit or hold fails or is declined.

1. Read the decline code from the tool result; classify it as insufficient funds, expired card, fraud block or technical error.
2. For technical errors retry `process_payment` once using the same idempotency_key to avoid double charges.
3. For the others, tell the guest kindly without implying fault and ask for another method through the secure link.
4. Hold the table for 30 minutes and tell the guest the deadline; notify by `send_sms` at the 20 minute mark.
5. If the guest offers a gift card, use `apply_gift_card` for the balance and charge the remainder.
6. After two failures, stop retrying to avoid a card lock and open a ticket with `create_support_ticket`.

Escalate when: a charge appears twice or the guest reports an unrecognised charge.
Never: retry with a new idempotency_key after an unclear result.
