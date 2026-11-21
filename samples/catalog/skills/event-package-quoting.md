# Event Package Quoting

Use this skill when the guest needs a priced quote for a group meal or event including food, drinks, room and fees.

1. Confirm the package, headcount and currency; use the guest currency from `lookup_customer_profile` when available.
2. Call `quote_event_package` with `include_tax` true and any add-ons such as cake, av_equipment or flowers.
3. Break the total into per head, room fee, service charge (usually 18 percent) and tax.
4. If the guest is international, show the total with `convert_currency` and say the rate is indicative.
5. Offer one cheaper and one richer variant by changing the package or the add-ons and re-quoting.
6. Quotes are valid for 14 days; use `set_reminder` to chase 3 days before expiry.
7. Send the quote with `send_followup_email`.

Never: quote a price from memory; always call `quote_event_package`.
