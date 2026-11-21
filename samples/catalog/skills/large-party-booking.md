# Large Party Booking

Use this skill when a booking is for 8 or more guests, or the guest asks for a long table or one bill.

1. Confirm headcount, date, time and whether children are included; ask for a firm number 7 days out.
2. Use `check_table_availability` with seating_area private_room; if none, ask the venue for a semi-private area.
3. Parties of 8 to 12 require a deposit of 20 per head; 13 or more go through `request_private_dining`.
4. Use `collect_deposit` once the venue confirms and `reserve_table` with the confirmed size.
5. Offer a set menu with `get_restaurant_menu` course tasting to speed up service; collect dietary needs for every guest.
6. Tell the guest that final numbers can drop by 10 percent without penalty up to 72 hours before.
7. Explain bill options early: a single bill, or `split_bill` equal at the end.

Escalate when: the group is above the venue capacity.
Never: confirm a group booking without a deposit.
