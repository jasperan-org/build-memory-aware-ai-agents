# Gift Card Redemption

Use this skill when the guest wants to pay with, check or top up a gift card.

1. Ask for the code and the PIN if the card has one; do not repeat the code in the reply.
2. Call `apply_gift_card` with `amount_to_apply` left empty to use the full balance, or the part the guest names.
3. If the balance does not cover the bill, charge the rest with `process_payment`.
4. Gift cards never expire for 5 years after purchase; cards older than that need staff review.
5. Leftover balance stays on the card; tell the guest the remaining balance.
6. Gift cards cannot be refunded to cash except where required by law.
7. After a lost card report, do not reveal the balance.

Escalate when: the code reports as used but the guest disputes it.
Never: apply a card to someone else's booking without the guest's consent.
