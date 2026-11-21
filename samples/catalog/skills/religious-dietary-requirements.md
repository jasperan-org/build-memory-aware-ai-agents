# Religious Dietary Requirements

Use this skill when the guest requires halal, kosher or fasting-friendly meals such as Ramadan iftar.

1. Ask which standard applies: halal certified, kosher supervised or simply no pork or shellfish.
2. Call `find_dietary_options` with diet halal or kosher and `dedicated_menu_only` true.
3. Verify the venue certificate on the menu; call `get_restaurant_menu` with the matching tag.
4. Check alcohol handling: some guests need food prepared without alcohol.
5. For fasting periods, book at sunset time from `get_weather_forecast` hourly data or the venue list.
6. Note the need with `update_guest_preferences` and in the booking.
7. Large groups should be sent to a venue with prayer space if asked, and the host should be told the number of guests who are fasting.

Never: claim certification the venue has not published.
