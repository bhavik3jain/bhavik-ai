# Calculate Workflow

Also load `references/metrics.md`.

Use profile defaults from `mls-investor-profile.json` for any inputs the user doesn't specify.

## Mode Detection

| User says | Mode |
|---|---|
| Specific inputs provided | Single Scenario |
| "Show me at different down payments / rates / rents" | Sensitivity Table |
| "What rent do I need to hit X% CoC?" / "Max price for X% cap rate?" | Solve Backwards |
| Mentions BRRRR, rehab, ARV | BRRRR Analysis |

---

## Mode 1: Single Scenario

**Collect inputs** (ask for any not provided):
- Purchase price, gross annual rent
- Down payment ($ or %)
- Interest rate (default: profile rate), loan term (default: 30yr)
- Annual taxes (default: 1.2% of price), annual insurance (default: 0.5% of price)
- Management fee (default: 8% of rent), vacancy rate (default: 5%)
- Maintenance reserve (default: 8% of rent), CapEx reserve (default: 5% of rent)
- Closing costs (default: 3% of price), rehab budget (default: $0)

**Output:**

```
Inputs Used
  Purchase Price:     $X
  Down Payment:       $X (X%)
  Interest Rate:      X%
  Gross Annual Rent:  $X

Monthly Income
  Gross Rent:         $X,XXX
  Vacancy (X%):      -$XXX
  Effective Income:   $X,XXX

Monthly Expenses
  Mortgage (P&I):    -$X,XXX
  Property Tax:      -$XXX
  Insurance:         -$XXX
  Management (X%):   -$XXX
  Maintenance:       -$XXX
  CapEx Reserve:     -$XXX
  Total Expenses:    -$X,XXX

Monthly Cash Flow:   $XXX
Annual Cash Flow:    $X,XXX

Key Metrics
  Cap Rate:   X.X%  (target ≥X%)  ✅/❌
  CoC:        X.X%  (target ≥X%)  ✅/❌
  GRM:        X.X   (target <10)  ✅/❌
  DSCR:       X.XX  (target ≥1.25) ✅/❌
  Cash In:    $XX,XXX

Break-even rent (at $0 cash flow): $X,XXX/mo
Break-even occupancy: XX%
```

---

## Mode 2: Sensitivity Table

Pick one variable to range across. Show CoC and Cap Rate at each value. Mark which scenarios hit profile minimums (✅).

Example — down payment sensitivity:
| Down Payment | Cash In | Monthly CF | CoC | Cap Rate |
|---|---|---|---|---|
| 10% | $X | $X | X% | X% |
| 15% | $X | $X | X% | X% |
| 20% | $X | $X | X% ✅ | X% ✅ |
| 25% | $X | $X | X% ✅ | X% ✅ |

---

## Mode 3: Solve Backwards

State the algebraic solution clearly:

- "To hit X% CoC at $[price] with $[down] down → you need $X,XXX/mo in rent"
- "To hit X% cap rate with $[rent] income → max purchase price is $X"

Show the formula used and a 1-line explanation.

---

## Mode 4: BRRRR Analysis

Inputs: purchase price, rehab cost, ARV, refi LTV (default 75%), refi rate.

```
Total Into Deal:      $X (purchase + rehab)
ARV:                  $X
Refi Proceeds (75%):  $X
Money Left In Deal:   $X

If $0 left in deal → infinite CoC return ✅
If money left in → CoC = Annual Cash Flow / Money Left In × 100
```

Flag whether this qualifies as a true BRRRR (≤$0 left in deal after refi).
