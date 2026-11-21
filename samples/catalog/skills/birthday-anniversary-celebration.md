# Birthday and Anniversary Celebration

Use this skill when the guest is marking a birthday, anniversary or similar occasion at a venue.

1. Ask for the occasion, the number of guests and whether it is a surprise.
2. Use `lookup_customer_profile` for past occasions and dietary needs.
3. Request a quiet table and put the occasion into the booking notes with `reserve_table`.
4. Offer extras by `quote_event_package` add-ons: cake, flowers or a drink on arrival, typically 15 to 40.
5. Surprise requests: tell the guest that we only contact the organiser.
6. Send the plan through `send_sms` and set a reminder 3 hours before.
7. Apply loyalty rewards with `redeem_loyalty_points` if the guest has a free course.

Never: message the celebrated guest about a surprise.
