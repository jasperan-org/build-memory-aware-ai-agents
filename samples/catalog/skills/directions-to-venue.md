# Directions to a Venue

Use this skill when the guest asks how to reach a restaurant, hotel or event from where they are.

1. Ask for the starting point and the mode of travel if not stated.
2. Call `get_directions` with the mode and the real departure time for traffic-aware routing.
3. Give the headline first: time, distance and the main step, then at most four turns.
4. For driving, call `find_parking` and mention the closest option and the walk.
5. For walking over 1 km in rain, suggest `book_rideshare` instead.
6. Mention a landmark by the entrance and the floor, if known.
7. Offer to text the route using `send_sms`.

Never: guess an address; use the venue record.
