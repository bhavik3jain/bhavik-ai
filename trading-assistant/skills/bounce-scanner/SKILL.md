---
name: bounce-scanner
description: Mean-reversion swing trade scanner. Finds S&P 500 stocks oscillating between highs and lows over 5 days, filters for liquid options, and uses VIX sentiment to rank the top 10 most likely to bounce up the next session. Use this skill when the user wants bounce plays, mean-reversion setups, "what's about to bounce", "oscillating stocks", "stocks going up and down", "next-day bounce", "swing trade ideas", or "short-term options plays based on price action". Always runs the scraper first, then performs analysis.
---

# Bounce Scanner

Identify S&P 500 stocks oscillating between highs and lows over the past 5 days, filter for liquid options, and use VIX market sentiment to surface the 10 stocks most likely to bounce up the next session.

This skill has two phases:
1. **Scraper** — Python script pulls raw OHLC + VIX data and scores oscillation amplitude. Run this first; it outputs `bounce_data.json`.
2. **Analysis** — Read the JSON, apply VIX sentiment overlay, rank candidates, surface the top 10 with specific options recommendations.

---

## Phase 1: Run the Scraper

Run the scraper using the Bash tool. Do not ask the user to do this — execute it directly.

**First, ensure dependencies are installed:**
```bash
pip install yfinance pandas numpy -q
```

**Then run the scraper:**
```bash
python trading-assistant/skills/bounce-scanner/scraper.py --out /tmp/bounce_data.json
```

For a faster scan (first 100 tickers, ~45s), use:
```bash
python trading-assistant/skills/bounce-scanner/scraper.py --top 100 --out /tmp/bounce_data.json
```

**Timeout**: Allow up to 5 minutes for the full S&P 500 scan. Tell the user it's running and approximately how long it will take before starting.

Once the script exits successfully and `/tmp/bounce_data.json` exists, proceed to Phase 2.

---

## Phase 2: Load and Analyze the Data

Read `bounce_data.json` from the working directory. The structure is:

```json
{
  "generated_at": "ISO timestamp",
  "universe_size": 500,
  "vix": {
    "level": 18.4,
    "regime": "normal",          // low_vol | normal | elevated | high_fear | extreme_fear
    "sentiment": "neutral",      // risk_on | neutral | cautious | risk_off
    "trend": "falling",          // falling | rising
    "favors_buying_premium": true
  },
  "candidates": [
    {
      "ticker": "AAPL",
      "current_price": 192.50,
      "day_change_pct": -1.2,
      "close_prices_5d": [195.0, 188.0, 196.0, 185.0, 192.5],
      "oscillation": {
        "score": 62.4,           // 0–100, higher = more bounce candidate
        "amplitude_pct": 5.9,    // (5d high - 5d low) / low
        "reversals": 3,          // direction changes in 5d window
        "high_5d": 196.0,
        "low_5d": 185.0
      },
      "options": {
        "liquid": true,
        "nearest_expiry": "2024-01-12",
        "atm_strike": 192.5,
        "oi": 12400,
        "bid": 2.10,
        "ask": 2.20,
        "spread_pct": 4.7,
        "iv": 28.4
      }
    }
  ]
}
```

---

## Phase 2A: VIX Sentiment Filter

First, assess the VIX regime and determine how it shapes the analysis:

| VIX Regime | What It Means | Bounce Play Adjustment |
|------------|---------------|----------------------|
| `low_vol` (< 15) | Risk-on, complacency | Strong bounce signal needed — too easy to get trapped in low-vol drift |
| `normal` (15–20) | Balanced market | Standard scoring — bounces are most reliable here |
| `elevated` (20–25) | Cautious | Favor stocks with the sharpest downward leg (most oversold) |
| `high_fear` (25–35) | Risk-off | Only take bounces with 3+ reversals AND highest amplitude — market is choppy |
| `extreme_fear` (> 35) | Panic | Do not run bounce plays — put the risk warning at the top of the output |

**VIX trend modifier:**
- VIX **falling** → market calming, bounce plays have tailwind → boost scores by 10%
- VIX **rising** → market deteriorating, bounce plays face headwind → discount scores by 15%

---

## Phase 2B: Candidate Scoring and Ranking

For each candidate in the JSON where `options.liquid == true`:

**Base score** = `oscillation.score` from the scraper (0–100)

**Apply modifiers:**

| Condition | Score Modifier |
|-----------|----------------|
| Stock closed DOWN on the most recent day (`day_change_pct < -1%`) | +15 (oversold into bounce) |
| Stock closed DOWN on both of the last 2 days | +10 (additional downward pressure) |
| Current price is within 2% of the 5d low | +20 (sitting at support) |
| Most recent close is above the 5d midpoint (`(high+low)/2`) | -10 (already bounced, less upside) |
| OI > 5,000 | +5 (very liquid, tight execution) |
| IV < 25% | +5 (cheap premium to buy) |
| IV > 50% | -10 (expensive premium, reduces edge) |
| VIX falling (applied globally from 2A) | +10% to all scores |
| VIX rising (applied globally from 2A) | -15% to all scores |

**Rank all liquid candidates by final score descending. Take the top 10.**

---

## Phase 2C: Supplement with Live Data

For the top 10 candidates, fetch live data to validate and enrich:

```
https://query1.finance.yahoo.com/v8/finance/chart/TICKER?interval=1d&range=5d
https://query1.finance.yahoo.com/v7/finance/options/TICKER
https://query2.finance.yahoo.com/v10/finance/quoteSummary/TICKER?modules=defaultKeyStatistics,calendarEvents,financialData,recommendationTrend
```

**Also run a targeted web search for each top-5 ticker:**
- `"[TICKER] stock news today [current date]"` — recent catalyst or catalyst absence
- `"[TICKER] analyst rating [current date]"` — recent upgrade/downgrade

Pull live VIX to confirm the scraped figure is still valid:
```
https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d
```

---

## Phase 2D: Output Format

Start with a VIX context block, then present the top 10.

---

### Market Sentiment — [Date]

**VIX**: [XX.X] ([↑/↓ X% from open]) — [Regime label]
**VIX Trend (5d)**: [Rising/Falling] ([week_start] → [current])
**Bounce Play Environment**: [One sentence — e.g., "VIX falling from elevated levels — mean-reversion plays have a tailwind today" or "VIX rising and in high-fear territory — size down and require 3+ reversals"]
**Strategy Bias**: [Buy short-dated calls / Buy debit call spreads / Avoid bounce plays]

---

### Top 10 Bounce Candidates — [Date]

Rank | Ticker | Score | 5d Amplitude | Days Down | Price vs 5d Low | Options Liquidity
-----|--------|-------|-------------|-----------|-----------------|------------------
1 | $XXXX | XX.X | X.X% | X | X.X% above | ✅ OI: X,XXX
2 | $XXXX | ...

---

Then for each of the top 10, present a full card:

---

### #[Rank] — $[TICKER] | [Company Name] | Score: [XX.X]

**5-Day Price Action**: [low] → [high] → [low] → ... → [current] *(show the actual 5 closes)*
**Amplitude**: [X.X%] swing | **Reversals**: [X] | **Today's Move**: [+/-X.X%]
**Position vs Range**: [X.X%] above 5d low — [e.g., "sitting at the floor" / "mid-range" / "near top"]

**VIX Context**: [One sentence connecting VIX regime to this specific ticker's setup]

**Recent News/Catalyst**: [What drove the oscillation if found — or "No major catalyst; technical oscillation only"]

**Options Setup** (next expiry: [date]):
- ATM Strike: $[XX] | Bid/Ask: $[X.XX] / $[X.XX] | Mid: ~$[X.XX]
- OI: [X,XXX] | Volume: [XXX] | IV: [XX]%
- Spread: [X.X%] of mid — [Tight ✅ / Moderate ⚠️ / Wide ❌]
- Cost per contract: ~$[XXX]

**Recommended Trade**:
- **Strategy**: [Long Call / Bull Call Spread] — chosen based on IV level
  - If IV < 30%: Long Call (cheap enough to buy outright)
  - If IV 30–50%: Bull Call Spread (reduce premium paid)
  - If IV > 50%: Flag as expensive; still present but note the premium risk
- **Contract**: $[TICKER] $[Strike]C exp [MM/DD/YY]
- **Entry**: ~$[X.XX] (mid price)
- **Max Profit**: $[XXX] | **Max Loss**: $[XXX] | **Breakeven**: $[XX.XX]

**Bounce Thesis** (2–3 sentences): Why this stock is likely to bounce tomorrow. Reference the specific price action pattern, where it is relative to its range, and what the VIX environment adds to the thesis.

**Exit Plan**:
- Take profit: 2–3x premium paid (e.g., if you paid $0.28, exit at $0.84–$1.10)
- Stop loss: Let it go to zero or exit at 50% loss if thesis breaks pre-market
- Time stop: This is a next-session play — exit by end of next trading day regardless

**Risk Level**: [Low / Medium / High]
**Conviction**: [⭐ / ⭐⭐ / ⭐⭐⭐] — based on score, VIX alignment, and news context

---

*(repeat for all 10)*

---

### Bounce Scanner Summary

**Best Setup Today**: $[TICKER] — [one sentence why]
**VIX Tailwind/Headwind**: [One sentence on whether market context helps or hurts]
**Avoid if**: [One sentence on conditions that would invalidate all bounce plays today — e.g., "major macro event pre-market tomorrow (FOMC, CPI) would override the technical bounce setup"]

---

## Data Quality Rules

- **Never fabricate prices** — if yfinance fetch fails, note "live data unavailable" and use scraper data only
- **Liquidity is a hard gate** — if `options.liquid == false`, do not present a trade for that ticker (can mention in a watchlist)
- **Scraper data freshness** — check `generated_at` timestamp; if data is more than 4 hours old, warn the user to re-run the scraper
- **Earnings gate** — always check next earnings date; if earnings fall before or on the next session, flag prominently (earnings binary risk overrides the bounce thesis)
- **VIX extreme_fear** — if regime is `extreme_fear`, open the output with a risk warning and do not present bounce plays as high-conviction trades

---

## Upgrade Path Note (Internal)

The scraper currently uses `yfinance`. When upgrading to **Polygon.io**:
- OHLC data: `GET /v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}?apiKey=KEY`
- Options chain: `GET /v3/reference/options/{underlyingAsset}?apiKey=KEY`
- VIX equivalent: use `GET /v2/aggs/ticker/I:VIX1D/range/1/day/...`
- Benefits: real-time quotes, cleaner options data, no rate limiting issues on large universes

Only one file changes: `scraper.py`. The skill logic (this file) is data-source agnostic.
