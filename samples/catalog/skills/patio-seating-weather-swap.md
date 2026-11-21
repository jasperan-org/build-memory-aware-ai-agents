# Patio Seating Weather Swap

Use this skill when on the day of the booking the weather changes and a patio or terrace table needs to move indoors or be kept.

1. Call `get_weather_forecast` for the exact hour and compare with the thresholds: rain over 40 percent or temperature under 10 degrees.
2. Call `check_table_availability` with seating_area indoor for the same time.
3. If an indoor table is open, call `modify_reservation` to swap and tell the guest by `send_sms`.
4. If not, keep the patio and mention heaters and blankets if the venue has them.
5. Offer to move to a later time if the rain is forecast to stop within 90 minutes.
6. If the guest refuses both, apply the cancellation skill with no fee for weather.

Escalate when: the venue has no indoor tables and the guest has a mobility need.
Never: charge a fee for a weather-driven change.
