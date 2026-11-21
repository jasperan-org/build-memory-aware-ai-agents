# Loyalty Points Redemption

Use this skill when the guest wants to know their points or spend them on a reward.

1. Call `get_loyalty_balance` and report points, tier and nearest expiry.
2. Typical values: 100 points equals 1 in bill credit, a free dessert costs 250 points, priority booking costs 500 points.
3. Suggest the best reward for the balance, not the largest redemption.
4. Call `redeem_loyalty_points` with the reward type and the booking id when the reward applies to a booking.
5. Confirm the new balance after redemption.
6. Points that expire within 30 days should be mentioned first.
7. Rewards cannot be combined with gift card payments on the same item.

Escalate when: the balance looks wrong or is missing points from a recent visit.
Never: redeem points without the guest saying which reward they want.
