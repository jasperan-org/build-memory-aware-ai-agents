# Feedback Collection

Use this skill when a guest has finished a visit and we want their rating or they volunteer a complaint or praise.

1. Ask once, within 24 hours of the visit, using `send_sms` or email; a single question rating 1 to 5.
2. Call `submit_guest_feedback` with the rating, a category and the comment in the guest's words.
3. Ratings of 1 or 2 set `follow_up_requested` true and trigger the service-recovery-comp skill.
4. Ratings of 5 may be asked to leave a public review, with the link, never with an incentive.
5. Thank the guest in one sentence and tell them what happens with the feedback.
6. Do not ask again for 30 days.

Never: argue with feedback or pressure for a higher rating.
