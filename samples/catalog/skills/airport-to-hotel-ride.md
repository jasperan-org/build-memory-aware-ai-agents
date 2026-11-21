# Airport to Hotel Ride

Use this skill when the guest needs a ride from an airport or station to a hotel or restaurant, especially late in the evening.

1. Confirm flight number, terminal, hotel name and passenger count; call `get_flight_status` to get the real arrival time.
2. Pick pickup time as arrival plus 30 minutes for domestic and 60 minutes for international flights.
3. Call `estimate_travel_time` with mode rideshare and the pickup time to check duration and traffic.
4. Call `book_rideshare` with `flight_number` so the pickup follows delays. Use xl for 4 or more passengers or heavy luggage and wheelchair_accessible when needed.
5. Call `notify_hotel_concierge` with request_type late_arrival if arrival is after 22:00 so the front desk keeps the room.
6. Send the driver details and pickup point with `send_sms`.

Escalate when: the booking is unavailable for 20 minutes after the requested pickup.
Never: book without the passenger count or a pickup point.
