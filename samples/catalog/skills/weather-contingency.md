# Weather Contingency

Use this skill when rain, heat, wind or cold could affect a booking, an outdoor table or an event.

1. Call `get_weather_forecast` for the city, the date and the hour of the booking.
2. Thresholds for outdoor seating: rain above 30 percent, wind above 30 km/h or below 8 degrees Celsius means indoors.
3. If the guest booked a patio, offer `modify_reservation` with seating_area indoor, free of charge.
4. For outdoor events, check whether a covered or indoor backup room exists with `request_private_dining`.
5. Advise the guest about clothing and parking when heavy rain is forecast.
6. Forecasts beyond 5 days are unreliable; tell the guest to check again 48 hours before.

Never: cancel an outdoor booking for the guest on the forecast alone.
