# Support Ticket Triage

Use this skill when a request cannot be solved in chat and must be logged for staff, or a guest asks for the status of a case.

1. Summarise the problem, the booking reference and what has been tried in three lines.
2. Set priority: urgent for safety, allergies, double charges and same-day bookings; high for refunds over 100; normal otherwise.
3. Call `create_support_ticket` with the summary and the priority; keep the guest's own words out of the title.
4. Tell the guest the ticket number and the response time: urgent 1 hour, high 4 hours, normal 1 business day.
5. For updates use `update_support_ticket` with status pending_staff and a clear note.
6. Do not open a duplicate if a ticket for the same booking exists.
7. Close the ticket only after the guest confirms the outcome.

Escalate when: the case is urgent and nobody replies within the stated time.
Never: promise an outcome in the ticket reply.
