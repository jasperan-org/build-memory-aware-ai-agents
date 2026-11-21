# Guest Profile Update

Use this skill when the guest shares a lasting preference, allergy, language or contact choice that should be remembered.

1. Distinguish durable facts from one-off requests: "I am vegan" is durable; "a window table tonight" is not.
2. Check the existing profile with `lookup_customer_profile` to avoid duplicates or contradictions.
3. Call `update_guest_preferences` with only the changed fields; write notes in plain words.
4. Confirm back what was saved in a single line, and ask the guest to correct it if wrong.
5. Allergies and medical diets need explicit consent and a note on severity.
6. Contact channel changes require confirming the new phone or email by sending a test with `send_sms`.
7. Never store payment data in notes.

Escalate when: the guest asks to delete their data.
Never: save a guess; save only what the guest said.
