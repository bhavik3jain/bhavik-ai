---
name: mls-analyzer
description: "Personal real estate investment analysis suite for evaluating MLS listings. Fetches listing data from mlspin.com and other MLS portals, runs investment math (cap rate, cash-on-cash return, GRM, DSCR), scores properties against a saved investor profile, and delivers buy/pass recommendations. Four modes: (1) interview - set up or update investor profile saved as mls-investor-profile.json in CWD; (2) analyze - evaluate one or more listing URLs; (3) compare - rank multiple listings side by side; (4) calculate - what-if scenario modeling and BRRRR analysis. Triggers on: any MLS listing URL being shared, 'analyze this listing', 'is this a good investment', 'run the numbers on this property', 'mls interview', 'set up my investor profile', 'update my criteria', 'compare these listings', 'what if I put X down', 'model this scenario', 'BRRRR analysis'."
---

# MLS Analyzer

Personal real estate investment toolkit. All modes read/write `mls-investor-profile.json` in the **current working directory**.

## Routing

Determine the mode from user intent, then read the corresponding reference file:

| Mode | Triggers | Reference |
|---|---|---|
| **interview** | "set up my profile", "update my criteria", first-time user | `references/interview.md` |
| **analyze** | MLS URL(s) shared, "analyze this listing" | `references/analyze.md` |
| **compare** | "compare these", "rank these listings" | `references/compare.md` |
| **calculate** | "what if", "model this", "BRRRR", "scenario" | `references/calculate.md` |

## Profile Check

Before running **analyze**, **compare**, or **calculate**: check if `mls-investor-profile.json` exists in CWD.
- If missing → tell the user to run the **interview** mode first, then stop.
- If present → load it and use it to personalize all analysis.

## Shared References

Load these when needed — do not load both upfront:
- `references/metrics.md` — cap rate, CoC, GRM, DSCR formulas and benchmarks (load during analyze/calculate)
- `references/scoring.md` — 6-dimension scoring rubric (load during analyze/compare)
