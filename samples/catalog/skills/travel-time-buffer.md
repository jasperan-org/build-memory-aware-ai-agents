# Travel Time Buffer

Use this skill when the guest needs to know when to leave or whether they can make a booking in time.

1. Call `estimate_travel_time` for the mode and the planned departure, with traffic_model pessimistic for time-critical trips.
2. Add buffers: 10 minutes for parking or finding the entrance, 15 minutes with children, 30 minutes with luggage.
3. Compare with the booking time and say plainly: leave by 18:10 to arrive by 19:00.
4. If the guest cannot make it, offer `modify_reservation` to a later slot within the 90 minute hold.
5. Offer `set_reminder` by SMS for the departure time.
6. Rush hour adds 30 to 60 percent in most cities.

Never: give an exact arrival time without stating the assumption.
