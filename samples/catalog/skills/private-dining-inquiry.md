# Private Dining Inquiry

Use this skill when the guest asks about a private room, a buyout or a semi-private area for a celebration or business dinner.

1. Collect date, headcount, occasion, budget per head and whether audio or visual equipment is needed.
2. Call `request_private_dining` with the room type and budget; the events team replies within 1 business day.
3. Meanwhile call `quote_event_package` for the closest package so the guest sees a number now.
4. Check `check_accessibility_options` if any guest uses a wheelchair, because many private rooms are on upper floors.
5. Explain typical minimum spend: weekday 1,500, Friday and Saturday 3,000, peak season more.
6. Do not take a deposit yet; the events team confirms availability first, and then the event-deposit steps apply.
7. Summarise the request by `send_followup_email` for the guest to forward.

Escalate when: the guest asks for a date within 7 days or a full buyout.
Never: guarantee a room before the events team confirms.
