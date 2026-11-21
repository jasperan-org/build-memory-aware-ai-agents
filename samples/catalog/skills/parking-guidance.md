# Parking Guidance

Use this skill when the guest is driving to a venue and asks where to park, about valet or EV charging.

1. Call `find_parking` with the arrival time, the expected stay and `ev_charging` if needed.
2. Rank options by walk time under 5 minutes first, then price per hour.
3. Mention valet only if the venue offers it, with the price and the tip custom.
4. Add that garages near theatres and stadiums fill 60 to 90 minutes before events; check `search_local_events`.
5. For a stay over 3 hours give the day rate if cheaper.
6. Send the address of the chosen car park by `send_sms`.
7. If no parking is within 10 minutes, suggest rideshare with `book_rideshare`.

Never: say parking is guaranteed.
