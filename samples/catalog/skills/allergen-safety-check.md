# Allergen Safety Check

Use this skill when a guest reports an allergy such as peanut, shellfish, sesame or gluten, or asks whether a dish is safe.

1. Record the exact allergens and the severity: intolerance, mild, severe or anaphylactic.
2. Call `check_allergens` for every dish under consideration with the full allergen list and the severity.
3. If any dish shows cross-contact risk and the severity is severe or anaphylactic, do not recommend it; offer venues with a separate prep area instead.
4. Tell the guest which allergens are declared, which are cross-contact risks, and that the kitchen makes the final confirmation on arrival.
5. Add the allergy to the reservation notes and, with consent, save it using `update_guest_preferences`.
6. Send the allergy summary to the venue with `send_followup_email` at least 24 hours before the visit.

Escalate when: the guest reports a reaction, or the severity is anaphylactic and the venue cannot confirm a separate prep area.
Never: state a dish is allergen-free; say it is declared free of the allergen.
