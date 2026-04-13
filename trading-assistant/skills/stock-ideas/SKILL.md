---
name: stock-ideas
description: Generate specific US stock trade ideas with entry prices, targets, and stop losses for both short-term and long-term trades. Use this skill whenever the user wants stock picks, a watchlist, investment ideas, sector plays, momentum trades, or asks "what should I buy/watch/trade". Triggers on: "stock ideas", "stock picks", "what should I buy", "give me ideas", "watchlist", "long term plays", "short term trades", "momentum stocks", "value plays", "growth stocks", "what to trade", "stock recommendations". Always include specific price levels — never vague direction only.
---

# Stock Ideas

Generate a curated list of specific stock trade ideas — both short-term trades and long-term positions — with exact entry, target, and stop levels.

## Step 1: Build Market Context

Before picking stocks, gather:
1. Search "best performing stocks today" and "top stock movers [date]"
2. Search "stock market outlook this week" for near-term catalysts
3. Note which sectors are leading (from market-pulse if available)
4. Search "analyst upgrades downgrades today" for institutional activity

This takes 2-3 searches. Do them in parallel.

## Step 2: Find Ideas Across Time Horizons

### Short-Term Ideas (days to 2-3 weeks)
Look for:
- **Momentum breakouts**: Stocks making 52-week highs on volume
- **Earnings runners**: Stocks that beat earnings and are still moving
- **News catalysts**: FDA approvals, contract wins, analyst upgrades
- **Technical setups**: Stocks bouncing off key support or breaking resistance

Search: "momentum stocks today", "52 week high breakouts", "stocks with bullish momentum"

### Long-Term Ideas (months to 1-2 years)
Look for:
- **Sector tailwinds**: AI/data centers, defense, energy transition, healthcare
- **Undervalued quality**: Strong companies beaten down by macro, not fundamentals
- **Earnings growth**: Companies with accelerating revenue and margin expansion
- **Institutional accumulation**: Stocks with rising analyst targets

Search: "best long term stocks [current year]", "undervalued growth stocks", "institutional buying stocks"

## Step 3: Validate Each Idea

For each stock you're considering, quickly check:
- Fetch `https://finviz.com/quote.ashx?t=TICKER` for technical snapshot
- Current price vs 50-day and 200-day moving averages
- Recent earnings trend (beat/miss)
- Any near-term risk events (earnings date, FDA decision, etc.)

## Step 4: Present Ideas

Present **3-4 short-term** and **3-4 long-term** ideas using this format:

---

## Short-Term Trades (Days to Weeks)

### [#]. $[TICKER] — [Company Name] | [Bullish/Bearish]

**Current Price**: $[XX.XX]
**Entry Zone**: $[XX.XX] – $[XX.XX] (buy on pullback to this range, or chase if breaking out above $[XX])
**Target**: $[XX.XX] (+[X]%)
**Stop Loss**: $[XX.XX] (-[X]%)
**Time Horizon**: [X days / X weeks]

**Thesis**: [2-3 sentences. What's the specific catalyst or setup. Why now. What needs to happen.]

**Catalyst**: [e.g., "Earnings next Tuesday, expected beat based on strong sector data"]
**Risk**: [e.g., "Market selloff would take this down with it despite strong fundamentals"]

---

## Long-Term Positions (Months to Years)

### [#]. $[TICKER] — [Company Name] | [Bullish/Bearish]

**Current Price**: $[XX.XX]
**Entry Zone**: $[XX.XX] – $[XX.XX] (consider scaling in over 2-3 weeks)
**12-Month Target**: $[XX.XX] (+[X]%)
**Stop Loss / Thesis Invalidation**: $[XX.XX] (-[X]%) or if [specific fundamental condition changes]
**Time Horizon**: [X months / X years]

**Investment Thesis**: [3-4 sentences. Why this company wins long term. What's the structural tailwind. What the market is missing or underpricing.]

**Key Metrics**:
- Revenue growth: [X]% YoY
- P/E or P/S: [X]x (vs sector avg [X]x)
- Next earnings: [Date]

**Risks**: [1-2 key risks to the thesis]

---

## Step 5: Add a Watchlist

After the ideas, add a quick watchlist of 3-5 additional tickers worth monitoring:

### On My Radar
| Ticker | Why Watching | Trigger to Buy |
|--------|-------------|----------------|
| $XXXX | [Brief reason] | [Specific condition] |
| $XXXX | [Brief reason] | [Specific condition] |

## Presentation Tips

- Lead with the highest-conviction idea
- Be direct about timeframe — "this is a 2-week trade" vs "this is a 12-month hold"
- If the market is bearish overall, include at least 1-2 short/bearish ideas
- If the user specifies a sector or theme, weight ideas toward that
- Flag any earnings dates within the next 2 weeks for short-term ideas — these are binary events

## Position Sizing Guidance

Add a brief note at the end:

> **Position sizing**: For short-term trades, consider risking no more than 1-2% of your portfolio per idea. For long-term positions, 3-5% per position is reasonable. Never size so large that a stop-out materially hurts your portfolio.
