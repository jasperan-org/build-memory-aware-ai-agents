# VIP Guest Recognition

Use this skill when a guest is high tier, a frequent diner, or flagged as VIP and the booking should feel personal.

1. Call `lookup_customer_profile` and `get_loyalty_balance` to read the tier, the favourite table and the past occasions.
2. Greet using the preferred name and refer to a real past visit, never a generic phrase.
3. Use `check_table_availability` for the preferred seating first, even when it is outside the normal window by 30 minutes.
4. Offer priority booking through `redeem_loyalty_points` only if the guest asks.
5. Add a room note for the host via `update_guest_preferences` so staff greet by name.
6. Do not mention spend or points in front of a group.

Never: mention other guests' visits or the tier thresholds.
