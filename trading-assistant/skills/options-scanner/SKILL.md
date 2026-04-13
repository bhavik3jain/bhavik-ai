---
name: options-scanner
description: Find specific US options trade ideas with exact strikes, expirations, and premiums. Use this skill whenever the user asks about options trades, earnings plays, calls/puts, spreads, straddles, unusual options activity, IV crush plays, or any options strategy. Triggers on: "options play", "options ideas", "earnings trade", "call options", "put options", "IV play", "options strategy", "what options should I buy", "options scanner", "unusual activity", "credit spread", "iron condor", "covered call", "wheel strategy". Be specific — always give ticker, strike, expiration, and approximate cost.
---

# Options Scanner

Find and present specific, actionable options trades. Every recommendation must include the exact contract details — no vague suggestions.

## Step 1: Assess Market Context

Before scanning, check:
1. Current VIX level (search if not already known)
2. Market direction today (up/down/flat)
3. Upcoming earnings this week (search "earnings calendar this week")
4. Upcoming macro events (Fed, CPI, jobs report)

This context determines what strategies make sense:
- **High VIX (>25)**: Favor selling options (collect elevated premium), avoid buying single legs
- **Low VIX (<15)**: Options are cheap — buying calls/puts or debit spreads makes sense
- **Earnings week**: Earnings straddles/strangles, directional plays on reporting companies
- **Trending market**: Momentum calls/puts; **Choppy market**: Iron condors, credit spreads

## Step 2: Scan for Ideas

Search for the following to find current opportunities:

**Unusual Options Activity**:
- Search "unusual options activity today" or "options flow today"
- Large block trades often signal smart money positioning

**Earnings Plays**:
- Search "earnings this week [current date]"
- Look for: high IV before earnings (sell premium), or clear directional setups (buy)

**High IV Rank Stocks**:
- Search "high IV rank stocks today" or "elevated implied volatility stocks"
- IV Rank >50% = expensive options → sell; <30% = cheap → buy

**Technical Setups** (search for news + check chart via Finviz):
- Stocks breaking out of consolidation → momentum calls
- Stocks at key support → bull put spreads
- Stocks rejecting resistance → bear call spreads

## Step 3: Present Trade Ideas

Present **3-5 specific options trades** using this template for each:

---

### Trade [#]: [Bullish/Bearish/Neutral] — $[TICKER]

**Strategy**: [e.g., Long Call / Bull Call Spread / Short Put / Earnings Straddle / Iron Condor]

**Contract**: $[TICKER] [Strike][C/P] exp [MM/DD/YY]
- *For spreads*: Buy [Strike]C / Sell [Strike]C exp [MM/DD/YY]

**Entry**: ~$[X.XX] per contract (≈ $[X]XX for 1 contract = 100 shares)

**Max Profit**: $[XXX] | **Max Loss**: $[XXX] | **Breakeven**: $[XXX]

**Thesis** (2-3 sentences max):
[Why this trade makes sense RIGHT NOW. What's the catalyst. What needs to happen for this to work.]

**Exit Plan**:
- Take profit at: [50-75% of max profit for spreads / specific price target for long options]
- Stop loss at: [25-50% loss on premium paid / specific level]
- Time stop: Exit by [X days before expiration] if thesis not playing out

**Risk Level**: [Low / Medium / High]

---

## Step 4: Add Strategy Context

After the trades, add a brief section:

### Current Options Environment
- **VIX**: [value] → [Strategy bias: buying vs selling]
- **Best strategies right now**: [e.g., "VIX at 28 favors selling premium — credit spreads and iron condors have edge"]
- **Watch out for**: [e.g., "FOMC next Wednesday — avoid short gamma positions going into it"]

## Options Strategy Quick Reference

Use the right strategy for the situation:

| Scenario | Strategy |
|----------|----------|
| Strong bullish conviction | Long call or bull call spread |
| Mildly bullish | Bull put spread (sell put spread) |
| Strong bearish conviction | Long put or bear put spread |
| Mildly bearish | Bear call spread (sell call spread) |
| Expecting big move, unsure direction | Long straddle/strangle |
| Expecting small move / range-bound | Iron condor, short strangle |
| Bullish on stock, want income | Covered call or cash-secured put |
| Before earnings (high IV) | Consider selling (IV crush after) |
| After earnings (IV dropped) | Consider buying (cheap premium) |

## Important Notes

- Always specify **monthly or weekly** expiration clearly
- For earnings plays, note whether the trade is **before** or **after** the report
- Flag if a stock has upcoming binary events (FDA decision, earnings, court ruling) that add risk
- Remind user that options can expire worthless — size positions appropriately
