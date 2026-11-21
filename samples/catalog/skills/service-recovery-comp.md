# Service Recovery and Comp

Use this skill when a guest had a bad experience such as a long wait, a wrong dish or rude service and expects a remedy.

1. Listen and restate the problem in one sentence; apologise once and without excuses.
2. Look up the visit with `query_order_status` and similar past feedback in `fetch_reviews`.
3. Choose the remedy by size: under 15 minutes late, an apology; a wrong dish, comp that dish; a ruined event, up to 25 percent of the bill.
4. Apply with `issue_store_credit` or `issue_refund`, within the 50 unit agent limit.
5. Record the case with `submit_guest_feedback` and follow up by `send_followup_email` within 24 hours.
6. Offer a priority booking for the next visit.

Escalate when: the remedy exceeds 50, there was a safety issue, or the guest asks for a manager.
Never: blame staff or the kitchen in front of the guest.
