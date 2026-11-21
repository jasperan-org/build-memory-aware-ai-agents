# Wheelchair Accessibility

Use this skill when a guest or a member of their party uses a wheelchair or has limited mobility.

1. Ask for the type of chair or aid and the party size; do not ask for a medical reason.
2. Call `check_accessibility_options` with need wheelchair and `party_includes_wheelchair` true.
3. Require step-free entry, an accessible restroom on the same floor and a table with 90 cm clearance.
4. Exclude venues with a basement dining room or a stairs-only private room.
5. Book with `reserve_table` and add a note: accessible table near the entrance.
6. For transport use `book_rideshare` with vehicle_class wheelchair_accessible and book 24 hours ahead.
7. Record the need in `update_guest_preferences` with consent.

Escalate when: no venue offers step-free access for the date.
Never: say a venue is accessible if the data is missing.
