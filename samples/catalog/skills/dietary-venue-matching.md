# Match a Venue to a Dietary Need

Use this skill when the guest names a diet such as vegan, gluten-free, halal, kosher or nut-free and needs somewhere that can serve it properly.

1. Read the diet from the request or `lookup_customer_profile`; ask whether it is a preference, an intolerance or a medical allergy.
2. Call `find_dietary_options` with `dedicated_menu_only` true for vegan, halal and kosher, and false for gluten-free or dairy-free where careful kitchens can adapt.
3. For every shortlisted venue call `get_restaurant_menu` with the matching `dietary_tag` and count the mains. Fewer than three suitable mains means the venue is a weak fit for a group.
4. State clearly which dishes qualify and which need a kitchen modification, and add a booking note so the kitchen knows in advance.
5. Save a confirmed diet with `update_guest_preferences` so the guest is never asked again.

Escalate when: the need is a severe allergy; follow the allergen-safety-check skill instead.
Never: promise a dish is safe from the menu tag alone.
