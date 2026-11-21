# Local Events Suggestions

Use this skill when the guest asks what is on nearby, wants an activity before or after dinner, or visits for the weekend.

1. Ask for the date, the interests and the budget in one short question.
2. Call `search_local_events` with the city, the date and a category, and `near_venue_id` for the restaurant.
3. Choose events that start at least 2 hours after dinner or end 90 minutes before it.
4. Offer at most three options with the start time and distance.
5. Use `estimate_travel_time` to show the walk or the ride between the venue and the event.
6. Mention that big events affect traffic and tables nearby.
7. Move to ticket booking if the guest picks one.

Never: recommend an event without a date match.
