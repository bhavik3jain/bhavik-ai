# Interview Workflow

Conduct a friendly, conversational interview to build or update the investor profile. Save results to `mls-investor-profile.json` in CWD.

If the file already exists, load it first and offer to update specific fields rather than starting from scratch.

## Interview — 3 Rounds

Ask each round as a group. Wait for answers before moving to the next round.

### Round 1: Financial Capacity
1. What's the maximum cash you're comfortable putting into a single deal? (downpayment + closing costs + initial repairs)
2. Is there a top-end purchase price you won't go above?
3. How are you planning to finance? (conventional, DSCR loan, cash, hard money, or deal-dependent)
4. What interest rate are you underwriting deals at? (or should I use current market rates?)

### Round 2: Return Requirements
5. What's the minimum cash-on-cash return you'd accept?
6. Do you have a minimum cap rate floor?
7. What's your primary strategy? (buy-and-hold LTR, short-term rental/Airbnb, BRRRR, flip)
8. Target hold period? (long-term 5–10+ years, short-term flip/BRRRR, flexible)

### Round 3: Property Preferences
9. Are you focused on specific cities, towns, or zip codes?
10. What property types interest you? (SFH, 2–4 unit, 5+ unit, mixed-use, condo)
11. How much rehab are you willing to take on? (turnkey only, light cosmetic, full gut)
12. Any absolute dealbreakers? (e.g., no HOA, no pre-1978 buildings, no flood zones, must cash flow day 1)

### Round 4: Portfolio Context (offer to skip)
13. How many investment properties do you currently own?
14. Any other context I should keep in mind when analyzing deals?

## Confirmation

Show a clean summary and ask: "Does this look right? I'll save it now."

```
Financial Capacity
- Max downpayment: $X
- Max purchase price: $X (or none)
- Financing: [type] at [rate]%

Return Requirements
- Min cash-on-cash: X%
- Min cap rate: X%
- Strategy: [LTR / STR / BRRRR / flip]
- Hold period: [X years / flexible]

Property Preferences
- Target markets: [list or "any"]
- Property types: [list]
- Rehab tolerance: [turnkey / light / any]
- Dealbreakers: [list or "none"]
```

## Save Profile

Write `mls-investor-profile.json` to CWD:

```json
{
  "version": 1,
  "last_updated": "YYYY-MM-DD",
  "financial_capacity": {
    "max_downpayment": 0,
    "max_purchase_price": null,
    "financing_preference": "conventional",
    "underwriting_rate_pct": 7.0
  },
  "return_requirements": {
    "min_coc_pct": 0,
    "min_cap_rate_pct": 0,
    "strategy": "LTR",
    "target_hold_years": null
  },
  "property_preferences": {
    "target_markets": [],
    "property_types": [],
    "max_rehab": "light",
    "dealbreakers": []
  },
  "portfolio_context": {
    "existing_properties": 0,
    "notes": ""
  }
}
```

Use `null` for any values the user skipped. Confirm the file was saved and tell the user they can now share MLS listing URLs to analyze them.
