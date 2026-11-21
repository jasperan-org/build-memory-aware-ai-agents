# Waitlist Management

Use this skill when no table is open at the requested time and the guest wants to wait, or asks where they stand on a waitlist.

1. Run `check_table_availability` with a window of plus or minus 60 minutes; offer any open slot before suggesting a waitlist.
2. If nothing is open, call `join_waitlist` with a flexible window and the guest mobile number.
3. Quote the realistic chance: parties of 2 to 4 are seated from the list about 70 percent of the time within 30 minutes, parties of 6 or more rarely.
4. Use `get_waitlist_status` when the guest asks for an update and give the position and the estimate.
5. When a table opens, send `send_sms` with template table_ready and hold the table for 10 minutes.
6. Offer the next best venue with `restaurant_search` if the estimate exceeds 45 minutes.

Never: promise a time; waitlist estimates are not guarantees.
