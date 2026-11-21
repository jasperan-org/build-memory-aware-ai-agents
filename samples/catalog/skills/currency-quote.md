# Currency Quote for International Guests

Use this skill when the guest asks what a price, deposit or bill is in their own currency.

1. Find the amount and its currency from the booking or `quote_event_package`.
2. Call `convert_currency` with the guest currency from `lookup_customer_profile`; ask if unknown.
3. Give both numbers: 120 EUR, about 130 USD, and mention that the rate is indicative.
4. Card payments are charged in the venue currency; the guest bank sets the final rate and any fee.
5. For deposits over 500, quote again on the day of payment because rates move.
6. Round to the nearest whole unit for display but keep cents for charges.
7. Never promise the rate for a later date.

Never: charge in another currency unless the booking says so.
