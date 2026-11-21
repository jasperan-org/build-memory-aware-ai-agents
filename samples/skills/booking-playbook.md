# Booking Playbook

Use this skill when the user asks the agent to choose, hold, or book a restaurant.

1. Retrieve the user's durable preferences before proposing options.
2. Retrieve relevant policy notes for deposits, cancellations, and accessibility.
3. Offer no more than three candidates unless the user asks for breadth.
4. Do not call `reserve_table` until the user confirms restaurant, date, time, and party size.
5. After booking, store a short summary in memory and offer a follow-up email.
