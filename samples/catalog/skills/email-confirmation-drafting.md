# Email Confirmation Drafting

Use this skill when a booking, change, refund or policy decision needs a written record by email.

1. Collect the reference, date, time, venue, party size and any money amounts before writing.
2. Check `lookup_customer_profile` for language; use `translate_text` with tone formal if the guest uses another one.
3. Write a subject with the reference code and the status, such as Booking confirmed.
4. Body: three short paragraphs at most: what was done, what the guest must do next, and how to reach us.
5. Call `send_followup_email` and tell the guest it was sent to the address on file.
6. For refunds, include the amount, the method and the 5 to 7 business day window.

Never: attach internal notes or staff comments.
