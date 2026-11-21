# Flight Delay and Reservation Change

Use this skill when a guest says their flight is delayed or cancelled and asks to cancel, move or keep a booking or deposit.

1. Call `get_flight_status` for the flight and date to confirm the delay and the new arrival time.
2. Estimate whether the guest can still make the booking: arrival plus baggage and `estimate_travel_time`, with 45 minutes of buffer for international arrivals.
3. If they can make it, offer `modify_reservation` to a later time; the venue holds a table up to 90 minutes without a charge.
4. If they cannot, call `calculate_cancellation_fee` with reason_code travel_disruption. Documented travel disruption normally waives the fee and allows the deposit to be moved with `release_deposit` outcome transfer_to_new_date.
5. Check `retrieve_policy` for the venue exception wording before promising a full refund.
6. Confirm the choice, then call `cancel_reservation` or `modify_reservation` and send the result with `send_sms`.

Escalate when: the delay is under 2 hours but the guest still wants a full refund, or the policy excludes travel disruption.
Never: forfeit a deposit for a documented airline delay without a human decision.
