# Hotel Room Block for Events

Use this skill when an event or private dinner has out-of-town guests who need rooms nearby.

1. Ask for the event date, the number of rooms and the number of nights.
2. Call `book_hotel_room` for each room with `linked_reservation_id` set to the event booking.
3. Blocks of 10 or more rooms get a 10 percent group rate; hold the block for 14 days.
4. Use `get_directions` from the hotel to the venue and tell the host the walk time.
5. Plan transfers: `book_rideshare` for arrivals before the event.
6. Send a guest information message through `send_followup_email` with the venue address, the dress code and the contact.
7. Ask the hotel about late check-in with `notify_hotel_concierge`.

Escalate when: the block exceeds 20 rooms or the hotel has no availability.
Never: confirm the block without the host's payment terms.
