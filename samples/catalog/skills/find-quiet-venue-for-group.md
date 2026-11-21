# Find a Quiet Venue for a Group

Use this skill when a guest wants a calm, low-noise restaurant where a group can talk, especially with a dietary or accessibility need.

1. Call `lookup_customer_profile` for stored seating and dietary preferences; only ask the guest about what is missing.
2. Confirm date, party size and neighbourhood, then call `find_dietary_options` when a diet is named, otherwise `restaurant_search`.
3. For each of the top five candidates call `get_venue_ambience` for the requested service period. Keep venues under 70 dB at that hour; prefer early dinner or weekday lunch, which run about 10 dB quieter than late weekend service.
4. Call `check_table_availability` with `seating_area` set to private_room or indoor for the shortlisted venues. Groups of 7 or more should be offered a semi-private room first.
5. Optionally confirm with `fetch_reviews` using keyword `noise` for the last 90 days.
6. Present at most three options with noise level, diet fit and the open time slots, and ask the guest to pick one.

Escalate when: no venue meets both the quiet and the dietary need on the requested date.
Never: reserve a table before the guest has chosen the venue and time.
