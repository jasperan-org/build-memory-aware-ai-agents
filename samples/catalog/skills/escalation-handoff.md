# Escalation Handoff to a Human

Use this skill when the request involves a policy exception, a safety concern, a legal threat, a large amount or an angry guest.

1. Stop trying to solve it and tell the guest that a person will take over, with the time to expect.
2. Gather what the staff member needs: who, what, when, amounts, what was promised and what the guest wants.
3. Call `escalate_to_human` with a short reason and the transcript.
4. Create or update the ticket with `update_support_ticket` priority high or urgent.
5. Send the guest a message with the ticket number via `send_sms` or email.
6. Stay available for new information but do not make decisions on the case.
7. Thresholds: money above 200, any injury or reaction, and any chargeback.

Never: tell the guest the outcome before the human has decided.
