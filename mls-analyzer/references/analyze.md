# Analyze Workflow

Also load `references/metrics.md` and `references/scoring.md` before starting.

## Step 1: Fetch Each Listing

For each URL, use WebFetch. Extract:
- Address, asking price, property type, beds/baths, sqft, lot size, year built
- Gross annual income / rent (if provided)
- Annual property taxes, HOA fees (if any)
- Days on market, assessed value
- Description — note: recent updates, tenant status, lease expiry dates, system ages
- Flood zone, condo vs freehold, lead paint risk (flag if pre-1978)
- Photo/condition clues from description

If gross rent is not listed, note the gap and estimate from local market with a caveat.

## Step 2: Run the Numbers

Use formulas from `references/metrics.md`.

**Assumptions:**
- Down payment = min(profile `max_downpayment`, 25% of asking price)
- Closing costs = 3% of purchase price
- Total cash in = down payment + closing costs
- If expenses not listed: apply 50% rule (NOI = Gross Rent × 50%)
- Loan = asking price − down payment
- Monthly mortgage from amortization formula at profile's `underwriting_rate_pct`, 30-year term

**Calculate:**
1. GRM = Asking Price / Gross Annual Rent
2. Cap Rate = NOI / Asking Price × 100
3. Annual Debt Service = Monthly Mortgage × 12
4. Annual Cash Flow = NOI − Annual Debt Service
5. CoC = Annual Cash Flow / Total Cash In × 100
6. DSCR = NOI / Annual Debt Service
7. Price/sqft = Asking Price / Sqft
8. Price vs Assessed = Asking Price / Assessed Value × 100

## Step 3: Score the Property

Use rubric from `references/scoring.md`. Assign scores across all 6 dimensions and compute weighted total.

For **Location**: if not familiar with the area, do a quick web search for "[city/town] MA real estate market" to assess neighborhood quality.

## Step 4: Output

Use this structure for each listing:

---

## [Address] — $[Price]
**[Type]** | [Beds]BR/[Baths]BA | [Sqft] sqft | Built [Year] | [DOM] days on market

### The Numbers
| Metric | Value | Your Target | |
|---|---|---|---|
| Cap Rate | X.X% | ≥X.X% | ✅/⚠️/❌ |
| Cash-on-Cash | X.X% | ≥X.X% | ✅/⚠️/❌ |
| GRM | X.X | <10 | ✅/⚠️/❌ |
| DSCR | X.XX | ≥1.25 | ✅/⚠️/❌ |
| Price/sqft | $XXX | — | |
| Price vs Assessed | +X% | — | |

**Financing:** $[X]K down ([X]%) · $[X]K loan @ [X]% · $[X,XXX]/mo
**Annual Cash Flow:** $[X,XXX] · **Monthly:** $[XXX]

### Score: [X.X]/10 — [Strong Buy / Buy / Neutral / Pass / Hard Pass]
| Dimension | Score | Weight |
|---|---|---|
| Financial Returns | X/10 | 30% |
| Location | X/10 | 25% |
| Property Condition | X/10 | 20% |
| Deal Structure | X/10 | 15% |
| Risk Factors | X/10 | 10% |

### Green Flags 🟢
- [Specific positives]

### Red Flags 🔴
- [Specific risks]

### Verdict
[2–3 sentences: pursue or pass, what to negotiate, key questions to ask agent]

---

If multiple listings were analyzed, append a summary ranking table at the end:

| Rank | Address | Price | Cap Rate | CoC | Score | Verdict |
|---|---|---|---|---|---|---|
