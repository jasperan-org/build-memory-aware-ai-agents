# Translation for Foreign Guests

Use this skill when the guest writes in another language or the venue must communicate with a guest who speaks one.

1. Detect the language from the message and confirm with the guest; save it with `update_guest_preferences`.
2. Reply in the guest language with `translate_text` and the tone friendly; formal for complaints and legal text.
3. Keep names, dates, times and amounts exactly as they are; do not translate the venue name.
4. For menus, call `get_restaurant_menu` with the `language` code and mark dishes that remain untranslated.
5. For staff, translate the guest request into the staff language and attach both versions to the booking.
6. Allergy and policy text must be double-checked: send a note that the translation is machine-made.

Never: translate allergy information without the safety check.
