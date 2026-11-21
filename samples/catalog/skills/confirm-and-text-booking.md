# Confirm a Booking and Text the Confirmation

Use this skill when the guest has chosen a restaurant and time and wants the table booked and the confirmation sent by SMS.

1. Restate venue, date, time and party size and wait for an explicit yes.
2. Call `check_table_availability` one last time; tables can disappear between search and booking.
3. Call `reserve_table` with the confirmed arguments. If a deposit applies, call `collect_deposit` straight after and note the amount.
4. Call `send_sms` with template booking_confirmation. Keep it under 320 characters: venue name, date, time, party size, address, reference code and the cancellation deadline.
5. Call `set_reminder` by SMS for 24 hours before the booking.
6. Reply with the reference code and tell the guest the text is on its way.

Escalate when: `reserve_table` fails twice in a row.
Never: send the SMS before the booking has succeeded, or include card details in a text.
