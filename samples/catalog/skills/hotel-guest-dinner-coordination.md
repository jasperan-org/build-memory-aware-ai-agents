# Hotel Guest Dinner Coordination

Use this skill when a hotel guest or the hotel concierge is arranging a dinner reservation at a partner restaurant.

1. Collect the guest name, the room number or hotel, the date, the time and the party size.
2. Check `lookup_customer_profile` and the stay with `query_order_status` if a booking id exists.
3. Use `check_table_availability` and `reserve_table` as usual with a note: hotel guest, room and last name.
4. Call `notify_hotel_concierge` with request_type dinner_transfer if a transfer is wanted.
5. Arrange a return ride with `book_rideshare` for the end of the dinner, normally 2 hours after the start.
6. Hotel guests can charge to the room only if the hotel confirms it; otherwise use `process_payment`.

Never: give the room number to anyone but the hotel.
