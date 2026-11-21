# Ticket Booking Around Dinner

Use this skill when the guest wants tickets to a show, concert or game and a table timed around it.

1. Call `check_ticket_availability` with the quantity and any price cap; ask for accessible seating if needed.
2. Fix the event time, then plan dinner to end 60 minutes before the curtain and start at least 90 minutes earlier.
3. Call `estimate_travel_time` from the venue to the event with a 20 minute margin.
4. Use `check_table_availability` for the planned window and `reserve_table` after confirmation.
5. Share the ticket link and the combined plan by `send_followup_email`.
6. Set a reminder with `set_reminder` 3 hours before the event.
7. Tickets bought through us are non-refundable once issued.

Never: promise seats until `check_ticket_availability` returns them.
