"""Generate and optionally load synthetic memory for Lab 2.

The default generator is deterministic and offline so every attendee can produce
exactly the same artifact before connecting to Oracle or an LLM provider. Content
comes from curated pools per domain; a seed only decides which items are sampled
(without replacement) and in what order.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from . import use_utf8_output


@dataclass(frozen=True)
class SyntheticMessage:
    role: str
    content: str
    created_at: str


@dataclass(frozen=True)
class SyntheticThread:
    thread_key: str
    topic: str
    messages: list[SyntheticMessage]


@dataclass(frozen=True)
class SyntheticRecord:
    record_type: str
    subject_key: str
    content: str
    tags: list[str]


@dataclass(frozen=True)
class SyntheticSkill:
    name: str
    description: str
    body: str


@dataclass(frozen=True)
class SyntheticTool:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class SyntheticMemoryBundle:
    user_id: str
    agent_id: str
    domain: str
    generated_at: str
    threads: list[SyntheticThread]
    workflows: list[SyntheticRecord]
    entities: list[SyntheticRecord]
    knowledge: list[SyntheticRecord]
    skills: list[SyntheticSkill]
    tools: list[SyntheticTool]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


def _p(kind: str, description: str, **extra: Any) -> dict[str, Any]:
    """One JSON-schema property."""

    return {"type": kind, "description": description, **extra}


def _tool(name: str, description: str, required: list[str], **props: Any) -> tuple[str, str, dict]:
    schema = {"type": "object", "properties": props, "required": required}
    return name, description, schema


# ---------------------------------------------------------------------------
# Domain: restaurant concierge
# ---------------------------------------------------------------------------

_RESTAURANT_KNOWLEDGE = [
    ("deposits", "Parties of 6 or more need a card-backed deposit of $25 per guest, charged at booking and credited against the final bill."),
    ("cancellation-window", "Standard bookings cancel free of charge up to 24 hours before the reservation; inside that window the deposit is kept."),
    ("no-show-fee", "A no-show is charged $20 per guest from the card on file. The first no-show in a 12-month period is waived on request."),
    ("late-arrival", "Tables are held for 15 minutes past the booking time. After 30 minutes the table is released and the booking is treated as a no-show."),
    ("allergens-top-nine", "The kitchen tracks the nine major allergens in a matrix refreshed every Monday. Staff never promise a dish is allergen-free; they quote the matrix."),
    ("allergen-cross-contact", "Guests with severe nut or shellfish allergies are flagged to the chef 24 hours ahead so a separate prep station can be set up."),
    ("gluten-free", "Casa Brava has a dedicated gluten-free fryer. Harbor Table and Juniper Room can adapt dishes but share fryers, so celiac guests are warned."),
    ("vegan-menu", "Miso Lane serves a full vegan tasting menu at $58. It needs 48 hours notice on weekends."),
    ("accessibility-step-free", "Harbor Table and Northstar Grill are fully step-free. Juniper Room has a 3-step entrance with a ramp on the Maple Street side."),
    ("accessibility-seating", "Wheelchair users get a table with 90 cm clearance, and we remove a chair rather than ask the guest to move."),
    ("service-animals", "Service animals are welcome at every venue at any time. Emotional-support pets follow the pet policy and are limited to the terrace."),
    ("large-party-limit", "The dining room seats up to 12 at one table. Groups of 13 to 24 are split across two adjoining tables and need a manager's approval."),
    ("large-party-menu", "Parties of 8 or more choose from a fixed three-course menu at $62 per person, pre-ordered 72 hours ahead."),
    ("private-dining-minimum", "The Juniper Room private salon seats 18 with a $1,200 food and beverage minimum on weekdays and $1,800 on Fridays and Saturdays."),
    ("private-dining-deposit", "Private dining requires a 30% deposit and a signed contract; the deposit is refundable until 14 days before the event."),
    ("corkage", "Corkage is $35 per 750 ml bottle, limited to two bottles per table, and waived for any bottle not on our list when a guest also buys one from it."),
    ("dress-code", "Smart casual everywhere. Northstar Grill asks for collared shirts at dinner; sportswear and flip-flops are declined at the door."),
    ("kids-policy", "Children are welcome before 8:30 pm. High chairs and booster seats are available on request, and the kids menu is $14 for under-12s."),
    ("pets-terrace", "Well-behaved dogs are allowed on the terrace only, on a leash, with a water bowl provided. No pets in the dining room."),
    ("gift-card-validity", "Gift cards never expire, are not redeemable for cash, and can be used across all five venues."),
    ("gift-card-lost", "Lost gift cards are reissued within 2 business days when the purchaser can supply the order email and the last four digits of the payment card."),
    ("loyalty-earning", "The Table Club loyalty programme earns 1 point per $1 spent, excluding tax, tip, and service charge."),
    ("loyalty-tiers", "Silver starts at 500 points a year and gives priority waitlist. Gold at 1,500 points adds a complimentary dessert at each visit."),
    ("loyalty-expiry", "Loyalty points expire 18 months after they are earned, and guests get an email 30 days before any points lapse."),
    ("refund-vs-credit", "Refunds go back to the original card in 5 to 7 business days. A restaurant credit is issued instantly and valid for 12 months."),
    ("refund-disputes", "Food quality complaints reported within 24 hours qualify for a credit up to the dish price; anything larger goes to a manager."),
    ("weather-closure", "The terrace closes at wind speeds above 40 km/h or when heavy rain is forecast. Guests are moved inside or offered a free rebooking."),
    ("storm-closure", "If a venue closes for a storm warning, all deposits for that day are refunded in full without a fee."),
    ("waitlist", "The waitlist is ordered by request time, with Gold members moved up one place. Guests are texted when a table opens and have 10 minutes to confirm."),
    ("waitlist-parties", "The waitlist only covers parties of up to 6. Larger groups must book, because we can't free a large table at short notice."),
    ("holiday-hours", "On Christmas Eve, New Year's Eve, and Valentine's Day venues run a fixed menu with two seatings, at 6:00 pm and 8:45 pm."),
    ("holiday-deposit", "Holiday seatings need a $40 per guest deposit that is non-refundable inside 72 hours."),
    ("split-bills", "Bills can be split up to 6 ways at the table. Larger parties get one invoice, and splitting beyond 6 needs 24 hours notice."),
    ("service-charge", "A 12% service charge is added for parties of 6 or more, shown on the bill, and is distributed fully to staff."),
    ("terrace-seating", "The terrace holds 40 seats, is first come first served for walk-ins, and cannot be guaranteed on reservations before April."),
    ("terrace-heaters", "Terrace heaters run from October to March. Blankets are available, and a table can be moved inside at no cost if it turns cold."),
    ("birthday-celebrations", "Birthdays get a candle dessert at no charge if mentioned in the booking. Cakes brought from outside carry a $3 per person cutting fee."),
    ("anniversary-tables", "Anniversary bookings are given a booth or a window table when possible, and a handwritten card is placed on the table."),
    ("business-lunch", "Express business lunch is two courses in 60 minutes for $29 on weekdays, invoiced to the company on request."),
    ("quiet-tables", "Quiet tables are in the back room of Juniper Room and the mezzanine at Casa Brava, both away from the bar and kitchen pass."),
    ("booking-horizon", "Reservations open 60 days ahead at 10:00 am. Groups of 8 or more can book up to 120 days ahead through the concierge."),
    ("booking-changes", "A reservation can be moved to another date up to 6 times and the party size can change up to 2 hours before arrival."),
    ("walk-ins", "Each venue keeps about 20% of its tables for walk-ins, and the bar can be eaten at without a reservation."),
    ("photography", "Photos are fine in the dining room, but tripods, flash and drones are not allowed, and private events may restrict photography."),
    ("tasting-menu-timing", "Tasting menus last about 2 hours 30 minutes and must be ordered by the whole table."),
    ("breakfast-hours", "Harbor Table serves breakfast from 7:30 am to 11:00 am on weekdays and until 1:00 pm at weekends."),
    ("last-seating", "Last seating is 9:30 pm Sunday to Thursday and 10:15 pm on Fridays and Saturdays, and the kitchen closes 45 minutes after."),
    ("tipping", "Tips are never mandatory below 6 guests, and card tips are paid out to staff by the following week."),
    ("valet-parking", "Complimentary valet is available at Northstar Grill after 5:00 pm, and the other venues validate parking at the Pier Street garage for 2 hours."),
    ("invoices", "Company invoices are issued the same day with the guest's VAT number if it is provided before payment, and corrections within 30 days."),
    ("data-privacy", "Guest preferences and allergies are stored only with consent and can be erased on request within 30 days."),
    ("sommelier", "Wine pairings are $45 per person and the sommelier can adjust them for alcohol-free guests at $28."),
]

_RESTAURANT_WORKFLOWS = [
    ("allergy-booking", "To book for a guest with a severe allergy: record the allergen on the booking, tell the chef at least 24 hours ahead, confirm the menu with the guest by message, and flag the table at check-in."),
    ("deposit-collection", "To take a group deposit: confirm the party size, calculate $25 per guest, send the secure card-hold link, wait for payment, then mark the booking as confirmed and email the terms."),
    ("late-cancellation", "To handle a late cancellation: check the time against the 24-hour window, look up the deposit, offer a rebooking credit first, and only charge the fee if the guest declines."),
    ("refund-request", "To process a refund: find the booking, check the policy window, decide between card refund and credit, cap the amount at what was paid, and send a confirmation with the timeline."),
    ("private-event", "To plan a private event: gather date, headcount and budget, check the salon calendar, quote the minimum spend, draft the contract, and hold the date for 5 days awaiting the deposit."),
    ("waitlist-promotion", "To promote a waitlist entry: text the guest, wait 10 minutes for a confirmation, release the table to the next entry on silence, and log the outcome."),
    ("weather-closure", "To close the terrace for weather: list affected bookings, move them inside where possible, message the rest with a free rebooking link, and update the venue page."),
    ("birthday-setup", "To prepare a birthday: note the guest's age and name, order the candle dessert, check any allergies, tell the host about the booth and add a card."),
    ("gift-card-redemption", "To redeem a gift card: verify the code and balance, apply it before tip, keep any remainder on the card, and send the updated balance by email."),
    ("loyalty-adjustment", "To fix loyalty points: look up the visit, compare the bill to the points earned, post the missing points, and note the reason in the guest profile."),
    ("accessibility-prep", "To prepare for an accessibility need: record the need on the profile, choose a step-free venue or table, brief the floor team, and call the guest back to confirm the route."),
    ("complaint-recovery", "To recover from a complaint: apologise first, ask what went wrong, offer a credit up to the dish price, escalate to the manager when it is larger, and follow up in 48 hours."),
    ("vip-arrival", "To welcome a returning VIP: pull their profile, check favourite table and drinks, tell the host 30 minutes ahead, and greet them by name."),
    ("split-bill-setup", "To split a bill: ask how many ways at the start, add the service charge once, divide it equally unless itemised, and print separate receipts."),
    ("corporate-lunch", "To book a corporate lunch: collect the company and VAT number, offer the express menu, fix the end time, and invoice on the same day."),
    ("holiday-booking", "To take a holiday booking: offer the two seatings, collect the $40 deposit, explain the 72-hour rule, and send the fixed menu by email."),
]

_RESTAURANT_NAMES = [
    "Ava Hartley", "Niko Petrov", "Jun Watanabe", "Marta Ruiz", "Leila Haddad", "Sam Okafor",
    "Iris Lindqvist", "Noah Bergman", "Priya Nair", "Tomas Novak", "Chloe Dubois", "Mateo Silva",
    "Hana Kimura", "Oliver Grant", "Zoe Papadakis", "Rafael Costa", "Amara Mensah", "Lucas Weber",
    "Elena Rossi", "Daniel Cho", "Freya Larsen", "Omar Farouk", "Isabel Moreno", "Kenji Sato",
    "Nadia Volkova", "Ethan Brooks", "Sofia Marin", "Mei Tan", "Hugo Laurent", "Aisha Khan",
    "Viktor Hale", "Camila Reyes", "Theo Bennett", "Yara Saleh", "Peter Kowalski", "Lina Berg",
]
_RESTAURANT_DIETS = [
    "has a severe peanut allergy", "is vegan", "is celiac and needs gluten-free dishes",
    "is vegetarian and avoids eggs", "has a shellfish allergy", "is lactose intolerant",
    "eats halal only", "eats kosher only", "has no dietary restrictions", "avoids pork and alcohol",
    "has a tree-nut allergy", "is pescatarian",
]
_RESTAURANT_SEATING = [
    "a quiet back-room table", "a terrace table", "a booth", "a window table", "the bar counter",
    "a step-free table near the entrance", "a round table", "a table away from the kitchen",
]
_RESTAURANT_PARTIES = ["2 guests", "2 guests", "3 guests", "4 guests", "4 guests", "6 guests", "8 guests"]
_RESTAURANT_OCCASIONS = [
    "wedding anniversaries", "birthdays", "business lunches", "date nights", "family Sundays",
    "client dinners", "graduations", "book club evenings",
]
_RESTAURANT_VENUES = ["Harbor Table", "Juniper Room", "Miso Lane", "Casa Brava", "Northstar Grill"]

_RESTAURANT_THREADS = [
    ("peanut allergy booking", [
        ("user", "I'm booking Friday for four and my daughter has a severe peanut allergy."),
        ("assistant", "Noted. I'll flag the allergy and tell the chef 24 hours ahead so a clean prep station is ready."),
        ("user", "Great. Can you confirm that the satay starter is off the table for her?"),
        ("assistant", "The allergen matrix lists peanuts in the satay, so I'll suggest the grilled prawns instead."),
    ]),
    ("anniversary dinner", [
        ("user", "It's our tenth anniversary next Saturday, something quiet and special."),
        ("assistant", "Congratulations. I can offer a booth at Juniper Room's back room with a handwritten card."),
        ("user", "Perfect, book it for 8 pm."),
    ]),
    ("late cancellation fee", [
        ("user", "I need to cancel tonight's table for 6, a work emergency."),
        ("assistant", "That is inside the 24-hour window, so the $150 deposit would normally be kept."),
        ("user", "Could you move it to next week instead?"),
        ("assistant", "Yes, I can move the deposit to a new date, up to six changes are allowed."),
    ]),
    ("gift card balance", [
        ("user", "I got a gift card for Christmas, how much is left on it?"),
        ("assistant", "I need the code on the back and I can check the balance straight away."),
        ("user", "It's ending 4821."),
    ]),
    ("wheelchair access", [
        ("user", "My father uses a wheelchair, which of your restaurants works for him?"),
        ("assistant", "Harbor Table and Northstar Grill are fully step-free. Juniper Room has a ramp on Maple Street."),
        ("user", "Harbor Table then, a table for 4 on Sunday."),
    ]),
    ("private dining quote", [
        ("user", "We're planning a 16 person retirement dinner in March."),
        ("assistant", "The Juniper Room salon seats 18 with a $1,200 weekday minimum and a $1,800 weekend minimum."),
        ("user", "A Thursday then. What deposit do you need?"),
        ("assistant", "30% on signing, refundable until 14 days before the event."),
    ]),
    ("corkage question", [
        ("user", "Can we bring a bottle of champagne for my sister's birthday?"),
        ("assistant", "Yes, corkage is $35 per bottle, with a maximum of two per table."),
        ("user", "Fine, we'll bring one."),
    ]),
    ("vegan tasting menu", [
        ("user", "Two of us are vegan, any tasting menu?"),
        ("assistant", "Miso Lane has a vegan tasting menu at $58 and needs 48 hours notice on weekends."),
        ("user", "We'd like Saturday, so let's book it now."),
    ]),
    ("terrace in winter", [
        ("user", "Is the terrace open in January? I'd like to bring my dog."),
        ("assistant", "Dogs are welcome on the terrace, and heaters run through March with blankets on request."),
        ("user", "Lovely, a terrace table for 2 at noon."),
    ]),
    ("weather closure rebooking", [
        ("user", "You emailed that the terrace is closed because of wind. What now?"),
        ("assistant", "We can move you inside at the same time or rebook free of charge."),
        ("user", "Inside is fine, we just need the table to be quiet."),
    ]),
    ("split bill for ten", [
        ("user", "There will be ten of us and we want separate bills."),
        ("assistant", "Splits beyond six ways need 24 hours notice. I'll note it, and an itemised invoice will be ready."),
        ("user", "Good, thank you."),
    ]),
    ("loyalty points missing", [
        ("user", "My points from last Tuesday's dinner never showed up."),
        ("assistant", "Points are earned on the bill before tax, tip and service charge. Can you share the booking name?"),
        ("user", "Under Mateo Silva, the bill was $186."),
        ("assistant", "I've added 186 points and noted the correction on your profile."),
    ]),
    ("refund versus credit", [
        ("user", "Our event was cancelled, can I have my deposit back?"),
        ("assistant", "A refund goes to your card in 5 to 7 days, or you can take a credit now valid for 12 months."),
        ("user", "Refund please."),
    ]),
    ("kids and high chair", [
        ("user", "We're coming with a toddler on Sunday at 6, is that okay?"),
        ("assistant", "Yes, children are welcome before 8:30 pm and I'll set a high chair."),
        ("user", "Perfect."),
    ]),
    ("waitlist for saturday", [
        ("user", "Everything is full Saturday night, can you put us on the waitlist?"),
        ("assistant", "Yes, parties up to six. We'll text you when something opens and you get 10 minutes to confirm."),
        ("user", "Add us for 2 at Casa Brava."),
    ]),
    ("business lunch invoice", [
        ("user", "I need a quick lunch with a client, and an invoice for my company."),
        ("assistant", "The express lunch is two courses in an hour for $29, and I can invoice on the same day."),
        ("user", "Great, the VAT number is ES-B12345678."),
    ]),
    ("dress code query", [
        ("user", "Is a polo shirt fine at Northstar Grill?"),
        ("assistant", "Collared shirts are welcome there. Sportswear and flip-flops are the only things we decline."),
        ("user", "Good, thanks."),
    ]),
    ("holiday seating", [
        ("user", "I'd like a table for New Year's Eve."),
        ("assistant", "There are two seatings, at 6:00 pm and 8:45 pm, with a fixed menu and a $40 deposit per guest."),
        ("user", "The late one for 4, please."),
        ("assistant", "Done, and the deposit is non-refundable inside 72 hours."),
    ]),
    ("complaint about cold dish", [
        ("user", "My main arrived cold last night and nobody fixed it."),
        ("assistant", "I'm sorry about that. Because you're telling me within 24 hours, I can credit the dish price."),
        ("user", "A credit is fine, it was $34."),
    ]),
    ("birthday cake from outside", [
        ("user", "Can I bring my own cake for my mum's 70th?"),
        ("assistant", "Yes, with a $3 per person cutting fee, or we can supply a candle dessert at no charge."),
        ("user", "We'll take the free dessert."),
    ]),
    ("large party menu", [
        ("user", "We'll be 10 on Friday, can we order separately?"),
        ("assistant", "Parties of 8 or more choose from a fixed menu at $62, pre-ordered 72 hours ahead."),
        ("user", "Alright, send the menu."),
    ]),
]

_RESTAURANT_SKILLS = [
    ("concierge-allergy-safe-booking", "Book a table safely for guests with allergies or strict diets.",
     "the guest mentions an allergy, intolerance or strict diet",
     ["Record the allergen and its severity on the booking.", "Retrieve the allergen matrix for the chosen venue.", "Tell the chef at least 24 hours ahead for severe cases.", "Reply with the safe dishes and never promise allergen-free."]),
    ("concierge-large-party-intake", "Take bookings for parties of 8 or more.",
     "the party has 8 or more guests",
     ["Check the party size against the 12-seat table limit.", "Offer the fixed menu and pre-order deadline.", "Take the $25 per guest deposit.", "Escalate to a manager for 13 or more guests."]),
    ("concierge-deposit-and-cancellation", "Explain deposits and decide cancellation fees.",
     "the guest asks about a deposit, cancellation or no-show",
     ["Retrieve the booking and its deposit.", "Compare the cancellation time with the 24-hour window.", "Offer a move to a new date before charging a fee.", "State the outcome and the next step."]),
    ("concierge-celebration-planner", "Prepare birthdays, anniversaries and other celebrations.",
     "the guest mentions a birthday, anniversary or special occasion",
     ["Retrieve the guest profile for past occasions.", "Pick a booth, window or quiet table.", "Arrange the dessert and card.", "Confirm any outside cake and its cutting fee."]),
    ("concierge-weather-disruption", "Handle terrace and venue weather closures.",
     "a venue closes or may close for weather",
     ["List the affected bookings.", "Offer an inside table at the same time first.", "Offer a free rebooking if inside is declined.", "Refund deposits in full for storm closures."]),
    ("concierge-vip-recognition", "Recognise returning and loyalty-tier guests.",
     "the guest is a Silver or Gold member or has visited more than five times",
     ["Retrieve the loyalty tier and favourite venue.", "Apply the waitlist priority.", "Brief the host with favourite table and drinks.", "Mention earned benefits without reciting the full programme."]),
    ("concierge-gift-card-and-loyalty", "Resolve gift card and loyalty point issues.",
     "the guest asks about a gift card, balance or missing points",
     ["Verify the gift card code or booking.", "Check the balance or the bill.", "Post missing points or reissue the card.", "Email the updated balance."]),
    ("concierge-accessibility-arrangement", "Arrange step-free and mobility-friendly visits.",
     "the guest mentions a wheelchair, mobility need or step-free access",
     ["Choose a step-free venue or the ramp entrance.", "Reserve a table with 90 cm clearance.", "Brief the floor team.", "Confirm the arrival route with the guest."]),
    ("concierge-complaint-recovery", "Respond to dissatisfaction after a visit.",
     "the guest reports a problem with food or service",
     ["Apologise and ask for details.", "Check whether it was reported within 24 hours.", "Offer a credit up to the dish price.", "Escalate anything larger and follow up in 48 hours."]),
]

_RESTAURANT_TOOLS = [
    _tool("lookup_open_tables", "Check open tables at a venue for a date, time and party size.",
          ["venue", "date", "party_size"],
          venue=_p("string", "Venue name.", enum=_RESTAURANT_VENUES),
          date=_p("string", "ISO date, e.g. 2026-12-24.", format="date"),
          time=_p("string", "Preferred time, 24h HH:MM."),
          party_size=_p("integer", "Number of guests.", minimum=1, maximum=24)),
    _tool("place_card_hold", "Place a deposit hold on the guest's card for a booking.",
          ["booking_id", "amount"],
          booking_id=_p("string", "Booking identifier."),
          amount=_p("number", "Hold amount in dollars.", minimum=0),
          currency=_p("string", "ISO currency code.", enum=["USD", "EUR", "GBP"])),
    _tool("quote_cancellation_fee", "Work out the fee for cancelling a booking at a given time.",
          ["booking_id", "cancelled_at"],
          booking_id=_p("string", "Booking identifier."),
          cancelled_at=_p("string", "ISO timestamp of the cancellation.", format="date-time"),
          waive_first_no_show=_p("boolean", "Waive the fee if this is the first no-show.")),
    _tool("lookup_allergen_matrix", "Return which allergens are in each dish at a venue.",
          ["venue", "allergen"],
          venue=_p("string", "Venue name.", enum=_RESTAURANT_VENUES),
          allergen=_p("string", "Allergen to check.", enum=["peanut", "tree_nut", "shellfish", "gluten", "dairy", "egg", "soy", "sesame", "fish"]),
          dish=_p("string", "Optional dish name to narrow the result.")),
    _tool("request_private_dining_quote", "Create a quote for a private dining event.",
          ["date", "headcount"],
          date=_p("string", "ISO date of the event.", format="date"),
          headcount=_p("integer", "Number of guests.", minimum=6, maximum=18),
          budget_per_guest=_p("number", "Target spend per guest in dollars.")),
    _tool("redeem_gift_card", "Apply a gift card to a bill and return the remaining balance.",
          ["card_code", "bill_id"],
          card_code=_p("string", "Gift card code."),
          bill_id=_p("string", "Bill to apply it to."),
          amount=_p("number", "Amount to apply; defaults to the full bill.")),
    _tool("adjust_loyalty_points", "Add or remove Table Club points with a reason.",
          ["guest_id", "points", "reason"],
          guest_id=_p("string", "Guest identifier."),
          points=_p("integer", "Points to add (positive) or remove (negative)."),
          reason=_p("string", "Why the adjustment is made.")),
    _tool("check_waitlist_position", "Return a guest's current waitlist position and estimated wait.",
          ["waitlist_id"],
          waitlist_id=_p("string", "Waitlist entry identifier.")),
    _tool("preview_split_bill", "Preview how a bill splits across payers.",
          ["bill_id", "ways"],
          bill_id=_p("string", "Bill identifier."),
          ways=_p("integer", "Number of payers.", minimum=2, maximum=12),
          itemised=_p("boolean", "Split by items instead of equally.")),
    _tool("flag_accessibility_need", "Attach an accessibility need to a booking for the floor team.",
          ["booking_id", "need"],
          booking_id=_p("string", "Booking identifier."),
          need=_p("string", "Need type.", enum=["wheelchair", "step_free", "hearing", "visual", "mobility_aid", "service_animal"]),
          notes=_p("string", "Free-text notes for the host.")),
    _tool("notify_weather_closure", "Message every guest affected by a weather closure.",
          ["venue", "date"],
          venue=_p("string", "Venue name.", enum=_RESTAURANT_VENUES),
          date=_p("string", "ISO date of the closure.", format="date"),
          area=_p("string", "Closed area.", enum=["terrace", "whole_venue"]),
          offer_rebooking=_p("boolean", "Include a free rebooking link.")),
    _tool("schedule_table_card", "Order a handwritten card and dessert for a celebration table.",
          ["booking_id", "occasion"],
          booking_id=_p("string", "Booking identifier."),
          occasion=_p("string", "Occasion.", enum=["birthday", "anniversary", "graduation", "other"]),
          message=_p("string", "Text for the card.")),
    _tool("issue_restaurant_credit", "Issue a restaurant credit valid for 12 months.",
          ["guest_id", "amount"],
          guest_id=_p("string", "Guest identifier."),
          amount=_p("number", "Credit in dollars.", minimum=1),
          booking_id=_p("string", "Booking that caused the credit.")),
]

# ---------------------------------------------------------------------------
# Domain: support agent
# ---------------------------------------------------------------------------

_SUPPORT_KNOWLEDGE = [
    ("sla-enterprise", "Enterprise plans have a 1-hour first response for P1, 4 hours for P2 and next business day for P3."),
    ("sla-business", "Business plans get a 4-hour first response for P1, 1 business day for P2 and 3 business days for P3."),
    ("sla-free", "Free plans have no response SLA. Tickets are handled on best effort, typically within 5 business days."),
    ("severity-p1", "P1 means production is down for all users or data is at risk, and it pages the on-call engineer immediately."),
    ("severity-p2", "P2 means a major feature is degraded or a workaround exists, with a 4-hour update cadence until resolved."),
    ("business-hours", "Support hours are 08:00 to 20:00 CET Monday to Friday. P1 incidents are covered 24x7 on Enterprise plans."),
    ("refund-window", "Subscriptions can be refunded in full within 14 days of the first charge, pro rata for annual plans up to 30 days."),
    ("refund-approval", "Refunds under $500 can be approved by an agent. Larger refunds need approval from a billing lead within 1 business day."),
    ("service-credit", "An SLA breach earns a service credit of 5% of the monthly fee per full hour of breach, capped at 30%."),
    ("proration", "Upgrades are prorated to the day. Downgrades take effect at the next renewal with no refund of the difference."),
    ("invoice-corrections", "Invoice corrections for VAT or legal name are issued as credit notes within 3 business days of verification."),
    ("payment-retries", "Failed card payments retry on days 1, 3 and 7. The account moves to read-only on day 10."),
    ("api-rate-limits", "API limits are 600 requests per minute on Business and 3,000 on Enterprise. Responses over the limit return 429 with a Retry-After header."),
    ("api-key-rotation", "API keys can be rotated at any time and the old key keeps working for 24 hours. Rotation is recommended every 90 days."),
    ("api-versioning", "API versions are supported for 18 months after release, with deprecation emails sent at 12 and 3 months before."),
    ("webhook-retries", "Failed webhook deliveries retry 8 times over 24 hours with exponential backoff, then land in a dead letter list for 7 days."),
    ("webhook-signatures", "Webhook payloads are signed with HMAC-SHA256, and the timestamp tolerance is 5 minutes."),
    ("export-limits", "Data exports run asynchronously, are capped at 50 GB per job and 3 concurrent jobs per account, and links expire after 72 hours."),
    ("export-formats", "Exports are available as CSV, JSON lines or Parquet, and Parquet is recommended above 5 GB."),
    ("data-retention", "Event data is kept for 13 months on Business and 36 months on Enterprise, and deleted logs cannot be recovered."),
    ("gdpr-deletion", "Deletion requests under GDPR are completed within 30 days and confirmed by email, and backups are purged within 35 days."),
    ("sso-setup", "SSO via SAML 2.0 is available on Enterprise only, and metadata changes take effect within 15 minutes."),
    ("mfa-reset", "MFA resets need identity verification: the account owner's email plus a code sent to the company domain contact."),
    ("account-ownership", "Ownership transfers need written approval from the current owner, or a legal notice plus two weeks of silence."),
    ("seat-limits", "Business plans include 25 seats and Enterprise plans are unlimited. Extra seats on Business are $12 per month."),
    ("trial-extension", "Trials last 14 days and agents can extend once by 7 days. Further extensions go through sales."),
    ("status-page", "Incident updates are posted on the status page within 15 minutes of confirmation, and then every 30 minutes."),
    ("postmortems", "Postmortems for P1 incidents are shared with Enterprise customers within 5 business days."),
    ("maintenance-windows", "Planned maintenance happens on Sundays between 02:00 and 04:00 UTC with 7 days notice."),
    ("regions", "Data residency is available in eu-west, us-east and ap-south, and moving a region takes about 10 business days."),
    ("uptime-target", "The platform targets 99.95% monthly uptime for Business and 99.99% for Enterprise."),
    ("escalation-path", "Escalate to the duty manager when a P1 has no update for 60 minutes or when a customer asks twice."),
    ("vip-accounts", "Strategic accounts have a named technical account manager who must be copied on every escalation."),
    ("ticket-merging", "Duplicate tickets are merged into the oldest one and the customer is told which ticket survives."),
    ("ticket-reopen", "Resolved tickets can be reopened by the customer for 14 days, and after that a new ticket is created with a link."),
    ("csat-follow-up", "A satisfaction survey goes out 24 hours after resolution, and any score of 2 or lower triggers a lead review."),
    ("chat-hours", "Live chat is open from 09:00 to 18:00 CET and is available to Business and Enterprise customers."),
    ("phone-callbacks", "Callbacks are scheduled within 2 business hours for Enterprise and only in the customer's working hours."),
    ("security-reports", "Security vulnerability reports go to the security team, never to public tickets, and are acknowledged within 24 hours."),
    ("pen-test-requests", "Customers may pen-test with 10 business days notice and a signed scope document."),
    ("sandbox", "Every account gets a sandbox with its own API keys, rate limited to 60 requests per minute and reset monthly."),
    ("sdk-support", "Official SDKs exist for Python, Node, Java and Go, and community SDKs are not supported."),
    ("beta-features", "Beta features have no SLA and may change; support documents known issues but does not backport fixes."),
    ("billing-contacts", "Billing emails go only to the billing contact. Agents must not change it without the account owner's approval."),
    ("tax-ids", "VAT and tax IDs are validated against official registries, and a mismatch holds the invoice for 2 business days."),
    ("currency", "Plans can be billed in USD, EUR or GBP, and the currency is fixed per contract year."),
    ("contract-renewal", "Annual contracts renew automatically and a cancellation notice is needed 30 days before the renewal date."),
    ("discounts", "Agents cannot grant discounts. Requests go to the account executive, with at most 10% for multi-year terms."),
    ("language-support", "Support is available in English, Spanish, German and French, with other languages handled via translation."),
    ("attachments", "Ticket attachments are limited to 25 MB each and scanned, and files containing credentials are removed."),
    ("audit-logs", "Audit logs record admin actions for 12 months and are exportable by owners on Business and Enterprise plans."),
]

_SUPPORT_WORKFLOWS = [
    ("p1-incident", "To handle a P1 incident: confirm scope, page on-call, open a status page entry, tell the customer within the SLA, update every 30 minutes, and request the postmortem."),
    ("refund-approval", "To approve a refund: verify the charge date, check the refund window, approve directly below $500, otherwise send to a billing lead, and email the customer the timeline."),
    ("webhook-debug", "To debug failing webhooks: check delivery logs, test the signature secret, look at the endpoint's status codes, replay failed events, and confirm receipt."),
    ("key-rotation", "To rotate a compromised API key: verify the owner, issue a new key, set the old key to expire in 1 hour, and review audit logs for misuse."),
    ("data-export", "To run a large export: confirm the dataset and format, check the 3-job limit, start the job, share the link before the 72-hour expiry, and verify the row counts."),
    ("sla-breach", "To handle an SLA breach: compute the breach hours, calculate the service credit, get a lead's approval, post the credit, and apologise in writing."),
    ("mfa-reset", "To reset MFA: verify the owner's email, request a code from the company domain contact, reset the factor, and send a security notice."),
    ("ownership-transfer", "To transfer ownership: get written approval from the owner, verify the new owner's domain, make the change, and notify the billing contact."),
    ("gdpr-deletion", "To delete personal data: verify the requester, log the request, run the deletion job, wait for backup purge, and send the confirmation."),
    ("escalation", "To escalate a ticket: summarise the issue in three lines, attach logs, page the duty manager, copy the account manager, and tell the customer who owns it now."),
    ("duplicate-merge", "To merge duplicate tickets: find the oldest, merge the newer ones, copy unique details across, and tell the customer which ticket remains."),
    ("trial-extension", "To extend a trial: check it has not been extended, ask what is blocking evaluation, add 7 days, and set a reminder for day 5."),
    ("region-move", "To move a data region: confirm contract terms, schedule outside maintenance windows, back up the data, migrate, and verify after cutover."),
    ("sso-setup", "To set up SSO: confirm Enterprise plan, collect the SAML metadata, test with one user, then enforce and keep a break-glass admin."),
    ("failed-payment", "To handle failed payments: look at the retry schedule, ask the billing contact to update the card, extend the grace period once, and note it on the account."),
    ("security-report", "To handle a vulnerability report: acknowledge within 24 hours, move it to the security queue, remove it from public tickets, and keep the reporter updated."),
]

_SUPPORT_NAMES = [
    "Acme Labs", "Bluebird Health", "Northwind Traders", "Contoso Retail", "Globex Systems", "Initech Software",
    "Umbrella Logistics", "Stark Analytics", "Wayne Freight", "Hooli Cloud", "Pied Piper Media", "Soylent Foods",
    "Tyrell Robotics", "Cyberdyne Labs", "Wonka Confectionery", "Oscorp Biotech", "Aperture Education", "Gringotts Finance",
    "Vandelay Imports", "Dunder Paper", "Massive Dynamic", "Black Mesa Energy", "Nakatomi Trading", "Monarch Travel",
    "Prestige Worldwide", "Sterling Legal", "Lumon Industries", "Duff Beverages", "Rekall Studios", "Planet Express",
    "Bluth Homes", "Krusty Foods", "Zorg Industries", "Delos Hospitality", "Genco Imports", "Ollivander Crafts",
]
_SUPPORT_PLANS = ["Free", "Business", "Business", "Enterprise", "Enterprise"]
_SUPPORT_REGIONS = ["eu-west", "us-east", "ap-south"]
_SUPPORT_INTEGRATIONS = ["webhooks", "the REST API", "scheduled exports", "SAML SSO", "the Python SDK", "the Node SDK"]
_SUPPORT_CONTACTS = [
    "email", "phone callbacks", "live chat", "a shared Slack channel", "email with the account manager copied",
]
_SUPPORT_CONCERNS = [
    "missed webhook deliveries last quarter", "a disputed invoice", "a pending VAT correction",
    "an upcoming contract renewal", "a pen test planned next month", "a data export that timed out",
    "frequent 429 rate limit errors", "a GDPR deletion request in progress", "an SSO rollout",
]

_SUPPORT_THREADS = [
    ("webhook failures", [
        ("user", "Our webhooks stopped arriving about an hour ago."),
        ("assistant", "I can see 8 failed deliveries with 503 from your endpoint. I'll replay them once it's healthy."),
        ("user", "The endpoint is back, please replay."),
        ("assistant", "Replayed 8 events, all delivered with 200."),
    ]),
    ("refund within 14 days", [
        ("user", "We bought the Business plan 6 days ago and want a refund."),
        ("assistant", "That's inside the 14-day window, so a full refund is possible, and the amount is $480."),
        ("user", "Great, please go ahead."),
    ]),
    ("large refund approval", [
        ("user", "Refund our annual plan, we're cancelling after 20 days."),
        ("assistant", "That is pro rata, about $2,150, so I need a billing lead to approve it within a business day."),
        ("user", "Okay, keep me posted."),
    ]),
    ("compromised api key", [
        ("user", "A contractor pushed our API key to a public repo."),
        ("assistant", "Let's rotate it now. The old key will stop in 1 hour and I'll check the audit log."),
        ("user", "Thanks, new key received."),
        ("assistant", "Audit logs show no unfamiliar IPs in the last 48 hours."),
    ]),
    ("sla credit", [
        ("user", "Your outage lasted 3 hours last night, do we get a credit?"),
        ("assistant", "On Enterprise the credit is 5% per hour, so 15% of this month's fee, pending lead approval."),
        ("user", "That works."),
    ]),
    ("mfa lockout", [
        ("user", "I changed phones and can't get past MFA."),
        ("assistant", "I need to verify you. A code will be sent to your company domain contact."),
        ("user", "It's Dana at the IT desk."),
    ]),
    ("export timeout", [
        ("user", "My export of 80 GB keeps failing."),
        ("assistant", "Jobs are capped at 50 GB, so I'll split it into two Parquet exports."),
        ("user", "Perfect."),
    ]),
    ("rate limit 429", [
        ("user", "We get 429 errors all day since Monday."),
        ("assistant", "You're on Business with 600 requests per minute, and your peaks reach about 900."),
        ("user", "What are our options?"),
        ("assistant", "Enterprise has 3,000 per minute, or I can help with batching and backoff."),
    ]),
    ("gdpr deletion", [
        ("user", "A customer of ours asked for deletion of their data."),
        ("assistant", "I'll log the request. Deletion is done in 30 days and backups are purged in 35."),
        ("user", "Please send the confirmation to legal."),
    ]),
    ("sso rollout", [
        ("user", "We want SAML single sign-on for 400 users."),
        ("assistant", "SSO is Enterprise only. Do you want to test with one user first?"),
        ("user", "Yes, with mine, then everyone."),
    ]),
    ("failed payment", [
        ("user", "We got a notice that our account will go read-only."),
        ("assistant", "Your card failed on day 1 and 3, and the account becomes read-only on day 10."),
        ("user", "Our finance person will update the card today."),
    ]),
    ("ownership change", [
        ("user", "Our CTO left and we need a new account owner."),
        ("assistant", "I need written approval from the current owner, or a legal notice from your company."),
        ("user", "I'll send the legal notice."),
    ]),
    ("trial extension", [
        ("user", "Our trial ends tomorrow and the security review isn't done."),
        ("assistant", "I can extend by 7 days once. What is still blocking?"),
        ("user", "Pen test approval."),
    ]),
    ("data residency", [
        ("user", "We need our data stored in Europe."),
        ("assistant", "eu-west is available, and a region move takes about 10 business days."),
        ("user", "Start it after the quarter end."),
    ]),
    ("duplicate tickets", [
        ("user", "I opened three tickets about the same invoice."),
        ("assistant", "I'll merge them into the oldest, ticket 48213, and keep all your attachments."),
        ("user", "Thanks."),
    ]),
    ("invoice vat", [
        ("user", "Our invoice shows the wrong VAT number."),
        ("assistant", "I'll validate the correct number and issue a credit note within 3 business days."),
        ("user", "Number is DE123456789."),
    ]),
    ("pen test request", [
        ("user", "We'd like to pen-test our integration next month."),
        ("assistant", "That needs 10 business days notice and a signed scope document."),
        ("user", "Send me the template."),
    ]),
    ("vulnerability report", [
        ("user", "I found an authorization bypass in your export endpoint."),
        ("assistant", "Thank you. I'm moving this to the security team privately and you'll hear back within 24 hours."),
        ("user", "Understood."),
    ]),
    ("p1 outage", [
        ("user", "Everything is down for us, production is dead."),
        ("assistant", "I'm declaring a P1 and paging on-call now. First update in 30 minutes."),
        ("user", "Please copy our account manager."),
        ("assistant", "Done, she is on the thread and the status page entry is open."),
    ]),
    ("csat follow up", [
        ("user", "I gave a 2 on your survey, the fix took too long."),
        ("assistant", "I'm sorry. A lead will review this today, and I'll call back at a time that suits you."),
        ("user", "After 3 pm please."),
    ]),
]

_SUPPORT_SKILLS = [
    ("support-p1-incident-command", "Run the first hour of a P1 incident.",
     "a customer reports production down or data at risk",
     ["Confirm scope and severity with the customer.", "Page the on-call engineer.", "Post to the status page within 15 minutes.", "Update every 30 minutes until resolved."]),
    ("support-refund-decision", "Decide and process refund requests.",
     "a customer asks for money back",
     ["Retrieve the charge and plan.", "Check the 14-day or 30-day window.", "Approve below $500, otherwise ask a billing lead.", "State the amount and timeline."]),
    ("support-webhook-triage", "Find why webhooks fail and replay them.",
     "webhooks are missing, late or failing",
     ["Pull recent delivery logs.", "Check the endpoint status codes and signature secret.", "Replay failed events once healthy.", "Confirm receipt with the customer."]),
    ("support-credential-compromise", "Contain leaked or compromised credentials.",
     "an API key or password may have been exposed",
     ["Verify the account owner.", "Rotate the credential.", "Review audit logs for misuse.", "Recommend a 90-day rotation."]),
    ("support-sla-credit", "Calculate service credits after an outage.",
     "the customer asks for compensation for downtime",
     ["Retrieve the incident and plan.", "Compute breach hours.", "Apply 5% per hour up to 30%.", "Get lead approval and post the credit."]),
    ("support-data-requests", "Handle exports and deletion requests.",
     "the customer asks to export or delete data",
     ["Verify the requester.", "Check export limits and formats.", "Run the job and watch it.", "Confirm completion and retention."]),
    ("support-account-recovery", "Recover access to locked or orphaned accounts.",
     "the customer cannot sign in or the owner left",
     ["Verify identity through the company domain.", "Reset MFA or transfer ownership.", "Notify the billing contact.", "Send a security notice."]),
    ("support-escalation-handoff", "Escalate with a clean handoff.",
     "a ticket must move to a duty manager or specialist",
     ["Summarise the issue in three lines.", "Attach logs and ticket history.", "Copy the account manager.", "Tell the customer who owns it now."]),
    ("support-contract-and-billing", "Answer billing, VAT and renewal questions.",
     "the customer asks about invoices, taxes or renewals",
     ["Retrieve the invoice and contract.", "Validate the tax ID.", "Issue the credit note where needed.", "Remind them of the 30-day renewal notice."]),
]

_SUPPORT_TOOLS = [
    _tool("lookup_account_plan", "Return an account's plan, seats, region and contract dates.",
          ["account_id"],
          account_id=_p("string", "Account identifier or domain.")),
    _tool("check_sla_clock", "Show the time left on a ticket's SLA clock.",
          ["ticket_id"],
          ticket_id=_p("string", "Ticket identifier."),
          severity=_p("string", "Ticket severity.", enum=["P1", "P2", "P3"])),
    _tool("get_incident_status", "Fetch the current status page entry for an incident.",
          ["incident_id"],
          incident_id=_p("string", "Incident identifier."),
          include_updates=_p("boolean", "Include the update timeline.")),
    _tool("list_recent_tickets", "List an account's most recent tickets.",
          ["account_id"],
          account_id=_p("string", "Account identifier."),
          limit=_p("integer", "Max tickets to return.", minimum=1, maximum=50),
          status=_p("string", "Filter by status.", enum=["open", "pending", "resolved"])),
    _tool("page_duty_manager", "Page the duty manager with an escalation summary.",
          ["ticket_id", "summary"],
          ticket_id=_p("string", "Ticket identifier."),
          summary=_p("string", "Three-line summary."),
          severity=_p("string", "Severity.", enum=["P1", "P2"])),
    _tool("rotate_api_key", "Rotate an API key and set the old one to expire.",
          ["account_id", "key_id"],
          account_id=_p("string", "Account identifier."),
          key_id=_p("string", "Key to rotate."),
          grace_minutes=_p("integer", "Minutes the old key keeps working.", minimum=0, maximum=1440)),
    _tool("replay_webhook_deliveries", "Replay failed webhook deliveries for an endpoint.",
          ["endpoint_id", "since"],
          endpoint_id=_p("string", "Webhook endpoint identifier."),
          since=_p("string", "ISO timestamp to replay from.", format="date-time"),
          max_events=_p("integer", "Max events to replay.", minimum=1, maximum=1000)),
    _tool("start_data_export", "Start an asynchronous export job.",
          ["account_id", "dataset", "format"],
          account_id=_p("string", "Account identifier."),
          dataset=_p("string", "Dataset to export."),
          format=_p("string", "Output format.", enum=["csv", "jsonl", "parquet"])),
    _tool("calculate_service_credit", "Compute the service credit owed for an SLA breach.",
          ["monthly_fee", "breach_hours"],
          monthly_fee=_p("number", "Monthly fee in the billing currency.", minimum=0),
          breach_hours=_p("number", "Full hours of breach.", minimum=0),
          cap_percent=_p("number", "Maximum credit percentage.")),
    _tool("verify_identity_challenge", "Send an identity challenge to the account's domain contact.",
          ["account_id", "requester_email"],
          account_id=_p("string", "Account identifier."),
          requester_email=_p("string", "Email of the requester.", format="email"),
          channel=_p("string", "Delivery channel.", enum=["email", "sms"])),
    _tool("merge_tickets", "Merge duplicate tickets into the oldest one.",
          ["primary_ticket_id", "duplicate_ticket_ids"],
          primary_ticket_id=_p("string", "Ticket that survives."),
          duplicate_ticket_ids=_p("array", "Tickets to merge.", items={"type": "string"})),
    _tool("schedule_callback", "Schedule a support callback for a customer.",
          ["ticket_id", "slot"],
          ticket_id=_p("string", "Ticket identifier."),
          slot=_p("string", "ISO timestamp of the callback.", format="date-time"),
          phone=_p("string", "Number to call.")),
]

DOMAINS: dict[str, dict[str, Any]] = {
    "restaurant concierge": {
        "knowledge": _RESTAURANT_KNOWLEDGE,
        "workflows": _RESTAURANT_WORKFLOWS,
        "threads": _RESTAURANT_THREADS,
        "skills": _RESTAURANT_SKILLS,
        "tools": _RESTAURANT_TOOLS,
        "entity_names": _RESTAURANT_NAMES,
    },
    "support agent": {
        "knowledge": _SUPPORT_KNOWLEDGE,
        "workflows": _SUPPORT_WORKFLOWS,
        "threads": _SUPPORT_THREADS,
        "skills": _SUPPORT_SKILLS,
        "tools": _SUPPORT_TOOLS,
        "entity_names": _SUPPORT_NAMES,
    },
}


def _entity_text(domain: str, name: str, rng: random.Random) -> str:
    if domain == "support agent":
        return (
            f"{name} is on the {rng.choice(_SUPPORT_PLANS)} plan in {rng.choice(_SUPPORT_REGIONS)}. "
            f"Its main integration is {rng.choice(_SUPPORT_INTEGRATIONS)}, it prefers "
            f"{rng.choice(_SUPPORT_CONTACTS)}, and an open concern is {rng.choice(_SUPPORT_CONCERNS)}."
        )
    return (
        f"{name} {rng.choice(_RESTAURANT_DIETS)} and prefers {rng.choice(_RESTAURANT_SEATING)}. "
        f"Usually books for {rng.choice(_RESTAURANT_PARTIES)} and celebrates "
        f"{rng.choice(_RESTAURANT_OCCASIONS)} at {rng.choice(_RESTAURANT_VENUES)}."
    )


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _domain_parts(domain: str) -> dict[str, Any]:
    try:
        return DOMAINS[domain]
    except KeyError:
        raise ValueError(f"unknown domain {domain!r}; choose from {sorted(DOMAINS)}") from None


def _sample(rng: random.Random, pool: list[Any], count: int, label: str) -> list[Any]:
    if count > len(pool):
        raise ValueError(f"{label}: requested {count} but the maximum is {len(pool)}")
    return rng.sample(pool, count)


def _timestamp(base: datetime, offset: int) -> str:
    return (base + timedelta(minutes=offset)).isoformat()


def generate_bundle(
    *,
    user_id: str,
    agent_id: str,
    domain: str,
    thread_count: int,
    workflow_count: int,
    entity_count: int,
    knowledge_count: int,
    skill_count: int,
    tool_count: int,
    seed: int,
) -> SyntheticMemoryBundle:
    """Create a deterministic synthetic memory bundle (``generated_at`` aside).

    Every category is sampled without replacement from a curated pool, so no two
    items repeat. Asking for more than a pool holds raises ``ValueError``.
    """

    rng = random.Random(seed)
    parts = _domain_parts(domain)
    base = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)

    threads: list[SyntheticThread] = []
    for idx, (topic, turns) in enumerate(_sample(rng, parts["threads"], thread_count, "threads")):
        messages = [
            SyntheticMessage(role, text, _timestamp(base, idx * 10 + n))
            for n, (role, text) in enumerate(turns)
        ]
        threads.append(SyntheticThread(f"synthetic-thread-{idx + 1:02d}", topic, messages))

    workflows = [
        SyntheticRecord("workflow", f"workflow-{key}", text, ["procedural", "workflow", domain])
        for key, text in _sample(rng, parts["workflows"], workflow_count, "workflows")
    ]

    entities = [
        SyntheticRecord(
            "entity", f"entity-{_slug(name)}", _entity_text(domain, name, rng),
            ["entity", "preference", domain],
        )
        for name in _sample(rng, parts["entity_names"], entity_count, "entities")
    ]

    knowledge = [
        SyntheticRecord("knowledge", f"knowledge-{key}", text, ["semantic", "policy", domain])
        for key, text in _sample(rng, parts["knowledge"], knowledge_count, "knowledge")
    ]

    skills = []
    for name, description, when, steps in _sample(rng, parts["skills"], skill_count, "skills"):
        title = name.replace("-", " ").title()
        body = "\n".join(
            [f"# {title}", "", f"Use this playbook when {when}.", ""]
            + [f"{n}. {step}" for n, step in enumerate(steps, start=1)]
        )
        skills.append(SyntheticSkill(name, description, body))

    tools = [
        SyntheticTool(name, description, schema)
        for name, description, schema in _sample(rng, parts["tools"], tool_count, "tools")
    ]

    return SyntheticMemoryBundle(
        user_id=user_id,
        agent_id=agent_id,
        domain=domain,
        generated_at=datetime.now(timezone.utc).isoformat(),
        threads=threads,
        workflows=workflows,
        entities=entities,
        knowledge=knowledge,
        skills=skills,
        tools=tools,
    )


def write_bundle(bundle: SyntheticMemoryBundle, out_path: Path, *, write_skill_files: bool = False) -> None:
    """Write the JSON bundle and optionally each synthetic skill as Markdown."""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle.to_json_dict(), indent=2), encoding="utf-8")
    if write_skill_files:
        skills_dir = out_path.parent / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        for skill in bundle.skills:
            (skills_dir / f"{skill.name}.md").write_text(skill.body + "\n", encoding="utf-8")


def load_into_oamp(bundle: SyntheticMemoryBundle) -> dict[str, int]:
    """Load threads and memories into OAMP idempotently.

    Threads use their thread key as id and memories use ``synthetic-<subject_key>``;
    each is deleted before it is added, so a rerun replaces records.
    """

    from oracleagentmemory.apis.thread import Message
    from oracleagentmemory.core import OracleAgentMemory

    from .connection import connect
    from .onnx import oamp_embedder

    conn = connect()
    client = OracleAgentMemory(
        connection=conn,
        embedder=oamp_embedder(conn),
        extract_memories=False,
        schema_policy="create_if_necessary",
    )

    for fn, entity_id, information in [
        (client.add_user, bundle.user_id, f"Synthetic workshop user for {bundle.domain}."),
        (client.add_agent, bundle.agent_id, f"Synthetic workshop agent for {bundle.domain}."),
    ]:
        try:
            fn(entity_id, information)
        except ValueError as exc:
            if "already exists" not in str(exc):
                raise

    loaded = {"threads": 0, "memories": 0}
    for synthetic_thread in bundle.threads:
        client.delete_thread(synthetic_thread.thread_key)
        thread = client.create_thread(
            thread_id=synthetic_thread.thread_key, user_id=bundle.user_id, agent_id=bundle.agent_id
        )
        thread.add_messages(
            [Message(role=m.role, content=m.content) for m in synthetic_thread.messages]
        )
        loaded["threads"] += 1

    for record in [*bundle.workflows, *bundle.entities, *bundle.knowledge]:
        memory_id = f"synthetic-{record.subject_key}"
        client.delete_memory(memory_id)
        client.add_memory(
            f"[{record.record_type}] {record.content}",
            user_id=bundle.user_id,
            agent_id=bundle.agent_id,
            memory_id=memory_id,
        )
        loaded["memories"] += 1
    return loaded


def load_toolbox_skillbox(bundle: SyntheticMemoryBundle) -> dict[str, int]:
    """Best-effort load of synthetic tools and skills into the workshop registries."""

    from .connection import connect
    from .skillbox import upsert_skill
    from .toolbox import upsert_tool

    with connect() as conn:
        for tool in bundle.tools:
            upsert_tool(conn, tool.name, tool.description, tool.parameters, source="synthetic")
        for skill in bundle.skills:
            upsert_skill(conn, skill.name, skill.body, description=skill.description, metadata='{"source":"synthetic"}')
    return {"tools": len(bundle.tools), "skills": len(bundle.skills)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", default="restaurant concierge", choices=sorted(DOMAINS))
    parser.add_argument("--user-id", default="workshop_user")
    parser.add_argument("--agent-id", default="memory_agent")
    parser.add_argument("--threads", type=int, default=20)
    parser.add_argument("--workflows", type=int, default=15)
    parser.add_argument("--entities", type=int, default=30)
    parser.add_argument("--knowledge", type=int, default=50)
    parser.add_argument("--skills", type=int, default=5)
    parser.add_argument("--tools", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", type=Path, default=Path("generated/synthetic_memory.json"))
    parser.add_argument("--write-skill-files", action="store_true")
    parser.add_argument("--load-oamp", action="store_true", help="Load threads and records into OAMP.")
    parser.add_argument("--load-toolbox", action="store_true", help="Load tools and skills into Oracle registries.")
    return parser


def main(argv: list[str] | None = None) -> int:
    use_utf8_output()
    parser = build_parser()
    args = parser.parse_args(argv)
    from .connection import load_env

    load_env(Path.cwd() / ".env")
    try:
        bundle = generate_bundle(
            user_id=args.user_id,
            agent_id=args.agent_id,
            domain=args.domain,
            thread_count=args.threads,
            workflow_count=args.workflows,
            entity_count=args.entities,
            knowledge_count=args.knowledge,
            skill_count=args.skills,
            tool_count=args.tools,
            seed=args.seed,
        )
    except ValueError as exc:
        parser.error(str(exc))
    write_bundle(bundle, args.out, write_skill_files=args.write_skill_files)
    print(f"wrote {args.out}")
    print(
        json.dumps(
            {
                "threads": len(bundle.threads),
                "workflows": len(bundle.workflows),
                "entities": len(bundle.entities),
                "knowledge": len(bundle.knowledge),
                "skills": len(bundle.skills),
                "tools": len(bundle.tools),
            },
            indent=2,
        )
    )
    if args.load_oamp:
        print("OAMP load:", json.dumps(load_into_oamp(bundle), indent=2))
    if args.load_toolbox:
        print("toolbox/skillbox load:", json.dumps(load_toolbox_skillbox(bundle), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
