---
name: trade-setup
description: Deep dive analysis on a specific stock ticker with full trade setup — technical levels, options chain analysis, entry/exit/stop, and thesis. Use this skill whenever the user mentions a specific ticker and wants analysis, a trade plan, or asks "what do you think about $XYZ", "analyze $XYZ", "set up a trade on $XYZ", "is $XYZ a good buy", "options on $XYZ", or any request focused on a single stock. Always give a complete trade plan, not just commentary.
---

# Trade Setup

Do a complete analysis of a specific ticker and produce a full, ready-to-execute trade plan. This is the most detailed output — treat it like a professional trading desk note.

## Step 1: Gather Data (Run These in Parallel)

Fetch all of the following before writing anything:

**Price & Technical Data**:
- `https://finviz.com/quote.ashx?t={TICKER}` — price, volume, moving averages, RSI, technical rating
- Search "[TICKER] stock price today technical analysis"

**Fundamental Data**:
- `https://finance.yahoo.com/quote/{TICKER}` — P/E, market cap, 52-week range, earnings date
- Search "[TICKER] earnings revenue growth"

**News & Sentiment**:
- Search "[TICKER] news today"
- Search "[TICKER] analyst price target upgrade downgrade"
- Search "[TICKER] earnings date next quarter"

**Options Data**:
- Search "[TICKER] options implied volatility"
- Search "[TICKER] options unusual activity"

**Macro Context**:
- Search "[TICKER] sector performance" to understand headwinds/tailwinds

## Step 2: Write the Trade Setup Report

Use this exact structure:

---

## Trade Setup: $[TICKER] — [Company Name]
*[Date] | [Sector] | Market Cap: $[X]B*

### Snapshot
| Metric | Value |
|--------|-------|
| Current Price | $[XX.XX] |
| 52-Week Range | $[XX] – $[XX] |
| Today's Change | [+/-X]% |
| Volume vs Avg | [X]x average (above/below) |
| RSI (14) | [XX] ([overbought/oversold/neutral]) |
| vs 50-Day MA | [X]% [above/below] |
| vs 200-Day MA | [X]% [above/below] |
| Next Earnings | [Date] (in [X] weeks) |
| IV Rank | [XX]% ([high/low/normal] — [buy/sell options]) |

### Technical Picture
[2-3 sentences describing the chart setup. Where is price relative to key levels? Is there a pattern forming (flag, cup & handle, head & shoulders)? What does the trend look like on daily and weekly?]

**Key Levels**:
- Strong Support: $[XX.XX] and $[XX.XX]
- Strong Resistance: $[XX.XX] and $[XX.XX]
- Breakout Level: $[XX.XX] (above this = momentum accelerates)
- Breakdown Level: $[XX.XX] (below this = thesis breaks)

### Fundamental Picture
[2-3 sentences on the business. Revenue growth trend, margins, valuation vs peers. Is this cheap, fair, or expensive?]

**Key Stats**:
- Revenue growth (YoY): [X]%
- P/E ratio: [X]x (sector avg: [X]x)
- Analyst consensus: [Buy/Hold/Sell] | Avg target: $[XX.XX] ([X]% upside)

### Catalyst Map
| Catalyst | Date | Directional Impact |
|----------|------|-------------------|
| Earnings | [Date] | [Bullish/Bearish/Binary] |
| [Event 2] | [Date] | [Impact] |
| [Macro risk] | [Date] | [Impact] |

### News & Sentiment
- **Recent news**: [Most important 2-3 headlines and their implications]
- **Analyst activity**: [Recent upgrades/downgrades/price target changes]
- **Institutional flow**: [Any notable institutional buying/selling or unusual options activity]

---

## Stock Trade Plan

### Directional View: [Bullish / Bearish / Neutral with Conditions]

**Thesis** (3-4 sentences):
[Clear statement of the trade thesis. What's the setup. What needs to happen. What's the edge.]

### Entry Strategy
- **Ideal entry**: $[XX.XX] – $[XX.XX]
- **Aggressive entry** (chase if strong): Above $[XX.XX] on volume
- **Patient entry** (wait for pullback): $[XX.XX] or below

### Targets
- **Target 1** (conservative): $[XX.XX] (+[X]%) — take partial profits here
- **Target 2** (full thesis): $[XX.XX] (+[X]%) — hold if momentum strong
- **Extended target**: $[XX.XX] (+[X]%) — only if macro supports

### Stop Loss
- **Stop**: $[XX.XX] (-[X]%) — close position if price closes below this
- **Thesis stop**: Also exit if [specific fundamental condition changes]

### Time Horizon: [X days / X weeks / X months]

---

## Options Trade Plan

### Recommended Options Strategy: [e.g., Long Call / Bull Call Spread / Long Put / Iron Condor]

**Why this strategy**: [1-2 sentences — why this fits current IV and directional view]

#### Primary Play:
**Contract**: $[TICKER] $[Strike][C/P] exp [MM/DD/YY]
**Entry**: ~$[X.XX] per contract ($[XXX] per 1 contract)
**Target exit**: ~$[X.XX] per contract (+[X]% on premium)
**Stop**: ~$[X.XX] per contract (-[X]% on premium)
**Max risk**: $[XXX] per contract (premium paid)

#### Alternative (Lower Risk):
**Contract**: [Spread or different structure]
**Net debit/credit**: ~$[X.XX] ($[XXX] per spread)
**Max profit**: $[XXX] | **Max loss**: $[XXX] | **Breakeven**: $[XX.XX]

### Options Considerations
- **IV Rank [XX]%**: [High → consider spreads to reduce vega risk / Low → single leg buys make sense]
- **Earnings in [X] weeks**: [Flag if within 2 weeks — earnings creates IV risk for option buyers]
- **Greeks to watch**: Delta ~[X.XX], Theta decay ~$[X]/day

---

## Risk Assessment

**Bull case** (probability: [X]%): $[XX.XX] target — [what needs to happen]
**Base case** (probability: [X]%): $[XX.XX] target — [most likely scenario]
**Bear case** (probability: [X]%): $[XX.XX] target — [what could go wrong]

**Top risks to this trade**:
1. [Risk 1 — be specific]
2. [Risk 2 — be specific]
3. [Macro risk if relevant]

---

## Step 3: Final Recommendation

End with a clear, one-paragraph summary:

> **Bottom line**: [1-2 sentences on overall view — bullish/bearish and why]. [Recommended action — stock vs options, which setup to use]. [Most important thing to watch.]

## Formatting Notes

- Always populate every field with real data — don't leave placeholders
- If options data is unavailable, note it and focus on the stock trade plan
- If the ticker is unfamiliar or thinly traded, flag it and adjust options recommendations accordingly
- Keep the tone like a sharp trading desk note — direct, specific, no fluff
