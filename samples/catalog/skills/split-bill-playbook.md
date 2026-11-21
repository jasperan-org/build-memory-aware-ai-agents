# Split the Bill

Use this skill when a group wants to divide the bill by person, by item or in custom amounts.

1. Ask for the method: equal, by item or custom amounts, and who is in the group.
2. Get the open tab with `query_order_status` and check that all items are final before splitting.
3. Call `split_bill` with the method and the list of diners; add the gratuity percentage first so it is shared fairly.
4. Each diner receives a payment link; send them with `send_sms` and report which ones are paid.
5. If a diner wants to use a gift card, apply it with `apply_gift_card` before the card charge.
6. Rounding differences up to 1 unit go to the host.
7. When all links are paid, close the tab and offer a receipt by email.

Escalate when: more than 12 diners or more than 4 separate cards on a tab.
Never: split before the tab is finalised.
