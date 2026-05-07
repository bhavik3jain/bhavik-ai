#!/usr/bin/env python3
"""
Bounce Scanner — S&P 500 mean-reversion data scraper.

Pulls 5-day OHLC for all S&P 500 stocks + VIX and scores each ticker for
oscillation amplitude and options liquidity. Outputs JSON for the skill.

Usage:
    python scraper.py                  # full S&P 500 scan
    python scraper.py --top 50         # quick test on first 50 tickers
    python scraper.py --out custom.json

Future upgrade path:
    Replace yfinance calls with Polygon.io REST API (polygon.io/docs).
    Each yf.download() call maps to GET /v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}
    Each options chain call maps to GET /v3/reference/options/{underlying}
"""

import argparse
import json
import sys
from datetime import datetime, timedelta

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError:
    print("Missing dependencies. Run: pip install yfinance pandas numpy")
    sys.exit(1)

SP500_TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","BRK-B","LLY","AVGO","TSLA",
    "JPM","WMT","UNH","V","XOM","ORCL","MA","COST","HD","PG","JNJ","ABBV",
    "BAC","NFLX","CRM","CVX","KO","AMD","MRK","ADBE","PEP","TMO","WFC","ACN",
    "LIN","MCD","CSCO","ABT","GE","DHR","IBM","INTU","CAT","GS","PM","TXN",
    "ISRG","SPGI","AMGN","AXP","RTX","BKNG","MS","BLK","PFE","NOW","VRTX",
    "DE","AMAT","SYK","ADI","GILD","SCHW","C","MMC","PLD","MDT","ADP","REGN",
    "CB","PANW","ZTS","HCA","BSX","MO","SO","ELV","CME","ICE","TJX","USB",
    "NOC","ITW","EOG","COP","BMY","MMM","LRCX","DUK","SHW","MPC","PSX","HUM",
    "APH","KLAC","FTNT","CDNS","MCK","AMT","PXD","MCO","ECL","WELL","EMR",
    "WM","PYPL","CEG","DXCM","RSG","CTAS","MAR","MSI","STZ","NSC","O","CARR",
    "GWW","ORLY","AZO","HES","EW","IDXX","ROP","ODFL","FI","FAST","CTSH",
    "MTD","BDX","BIIB","ROST","PCAR","PWR","EFX","DOW","DD","PPG","ETN","IQV",
    "VRSK","A","KEYS","ANSS","XYL","WAB","STE","TDY","IEX","CPRT","FDS",
    "TRMB","MKTX","RMD","TER","AKAM","CSGP","BR","CHD","FMC","MAS","PKG",
    "ARE","POOL","SWK","NUE","MLM","BRO","CINF","LHX","L","PNR","OTIS",
    "ZBRA","TYL","EPAM","HBAN","RF","CFG","FITB","KEY","ZION","CMA","MTB",
    "SIVB","PBCT","SNV","FHN","FULT","UMBF","WTFC","IBOC","SFNC","SASR",
    "CVBF","BANR","GBCI","CTBI","NBTB","SBCF","NBT","TOWN","FFIN","WSBC",
]

# Deduplicate while preserving order
seen = set()
SP500_TICKERS = [t for t in SP500_TICKERS if not (t in seen or seen.add(t))]


def fetch_vix(period_days: int = 10) -> dict:
    vix = yf.Ticker("^VIX")
    hist = vix.history(period=f"{period_days}d")
    if hist.empty:
        return {"level": None, "trend": "unknown", "regime": "unknown"}

    latest = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else latest
    week_ago = float(hist["Close"].iloc[0])

    if latest < 15:
        regime = "low_vol"
        sentiment = "risk_on"
    elif latest < 20:
        regime = "normal"
        sentiment = "neutral"
    elif latest < 25:
        regime = "elevated"
        sentiment = "cautious"
    elif latest < 35:
        regime = "high_fear"
        sentiment = "risk_off"
    else:
        regime = "extreme_fear"
        sentiment = "risk_off"

    return {
        "level": round(latest, 2),
        "prev_close": round(prev, 2),
        "week_start": round(week_ago, 2),
        "day_change_pct": round((latest - prev) / prev * 100, 2),
        "week_change_pct": round((latest - week_ago) / week_ago * 100, 2),
        "regime": regime,
        "sentiment": sentiment,
        # Falling VIX = risk-on (good for call buying); rising = risk-off
        "trend": "falling" if latest < week_ago else "rising",
        "favors_buying_premium": latest <= 20 or latest < week_ago,
    }


def score_oscillation(prices: list[float]) -> dict:
    """
    Score how much a stock is bouncing between highs and lows.
    Returns amplitude score 0-100 and supporting stats.
    """
    if len(prices) < 3:
        return {"score": 0, "amplitude_pct": 0, "reversals": 0}

    arr = np.array(prices)
    high = arr.max()
    low = arr.min()
    amplitude_pct = (high - low) / low * 100

    # Count direction reversals (up-down-up or down-up-down)
    deltas = np.diff(arr)
    reversals = int(np.sum(np.diff(np.sign(deltas)) != 0))

    # Score: weighted combo of amplitude and reversal frequency
    # High amplitude + frequent reversals = high mean-reversion candidate
    amplitude_score = min(amplitude_pct / 15 * 60, 60)  # max 60 pts
    reversal_score = min(reversals / (len(prices) - 2) * 40, 40)  # max 40 pts
    score = amplitude_score + reversal_score

    return {
        "score": round(score, 1),
        "amplitude_pct": round(amplitude_pct, 2),
        "reversals": reversals,
        "high_5d": round(float(high), 2),
        "low_5d": round(float(low), 2),
    }


def check_options_liquidity(ticker: str) -> dict:
    """Check if nearest-expiry ATM options are liquid enough to trade."""
    try:
        t = yf.Ticker(ticker)
        expirations = t.options
        if not expirations:
            return {"liquid": False, "reason": "no_options_chain"}

        # Use nearest expiry
        chain = t.option_chain(expirations[0])
        calls = chain.calls
        current_price = t.fast_info.get("lastPrice", 0)

        if calls.empty or current_price == 0:
            return {"liquid": False, "reason": "empty_chain"}

        # Find ATM strike (closest to current price)
        calls = calls.copy()
        calls["dist"] = abs(calls["strike"] - current_price)
        atm = calls.loc[calls["dist"].idxmin()]

        oi = int(atm.get("openInterest", 0) or 0)
        bid = float(atm.get("bid", 0) or 0)
        ask = float(atm.get("ask", 0) or 0)
        mid = (bid + ask) / 2 if bid > 0 and ask > 0 else 0
        spread_pct = ((ask - bid) / mid * 100) if mid > 0 else 999

        liquid = oi >= 500 and spread_pct < 20

        return {
            "liquid": liquid,
            "nearest_expiry": expirations[0],
            "atm_strike": float(atm["strike"]),
            "oi": oi,
            "bid": round(bid, 2),
            "ask": round(ask, 2),
            "spread_pct": round(spread_pct, 1),
            "iv": round(float(atm.get("impliedVolatility", 0) or 0) * 100, 1),
        }
    except Exception as e:
        return {"liquid": False, "reason": str(e)[:60]}


def scan_tickers(tickers: list[str], verbose: bool = False) -> list[dict]:
    results = []

    # Batch download 5 days of daily OHLC for all tickers at once (much faster)
    if verbose:
        print(f"Downloading 5d OHLC for {len(tickers)} tickers...", flush=True)

    end = datetime.today()
    start = end - timedelta(days=10)  # extra buffer for weekends/holidays

    try:
        raw = yf.download(
            tickers,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception as e:
        print(f"Batch download failed: {e}", file=sys.stderr)
        return []

    close = raw["Close"] if "Close" in raw else raw.xs("Close", axis=1, level=0)

    for ticker in tickers:
        try:
            if ticker not in close.columns:
                continue
            series = close[ticker].dropna()
            if len(series) < 3:
                continue

            prices = series.tail(5).tolist()
            current_price = prices[-1]
            prev_close = prices[-2] if len(prices) >= 2 else current_price
            day_change_pct = (current_price - prev_close) / prev_close * 100

            osc = score_oscillation(prices)

            results.append({
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "day_change_pct": round(day_change_pct, 2),
                "close_prices_5d": [round(p, 2) for p in prices],
                "oscillation": osc,
                # Options liquidity filled in next pass for top candidates only
                "options": None,
            })
        except Exception:
            continue

    return results


def main():
    parser = argparse.ArgumentParser(description="Bounce Scanner data scraper")
    parser.add_argument("--top", type=int, default=0, help="Only scan first N tickers (for testing)")
    parser.add_argument("--out", default="bounce_data.json", help="Output JSON file path")
    parser.add_argument("--min-score", type=float, default=25.0, help="Min oscillation score to check options on")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    tickers = SP500_TICKERS[:args.top] if args.top else SP500_TICKERS

    print(f"[1/3] Fetching VIX...")
    vix = fetch_vix()
    print(f"      VIX: {vix['level']} | Regime: {vix['regime']} | Trend: {vix['trend']}")

    print(f"[2/3] Scanning {len(tickers)} tickers for 5-day oscillation...")
    candidates = scan_tickers(tickers, verbose=args.verbose)
    candidates.sort(key=lambda x: x["oscillation"]["score"], reverse=True)

    # Only check options liquidity on top oscillators (saves time + API calls)
    top_oscillators = [c for c in candidates if c["oscillation"]["score"] >= args.min_score]
    print(f"      Found {len(top_oscillators)} tickers above oscillation score {args.min_score}")

    print(f"[3/3] Checking options liquidity on top {len(top_oscillators)} candidates...")
    liquid_count = 0
    for i, c in enumerate(top_oscillators):
        if args.verbose:
            print(f"      [{i+1}/{len(top_oscillators)}] {c['ticker']}...", flush=True)
        c["options"] = check_options_liquidity(c["ticker"])
        if c["options"].get("liquid"):
            liquid_count += 1

    output = {
        "generated_at": datetime.now().isoformat(),
        "universe_size": len(tickers),
        "vix": vix,
        "candidates": top_oscillators,
        "liquid_options_count": liquid_count,
    }

    with open(args.out, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone. {len(top_oscillators)} candidates, {liquid_count} with liquid options.")
    print(f"Output: {args.out}")


if __name__ == "__main__":
    main()
