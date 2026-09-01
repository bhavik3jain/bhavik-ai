# test-migration

Migrate test suites between frameworks without losing coverage.

## Skills

### `selenium-to-playwright`

Converts a Selenium suite to Playwright through a phased workflow that keeps a human in
the loop at each checkpoint.

**Triggers on:** converting/migrating/porting Selenium to Playwright, questions about how
WebDriver / Grid / PageFactory / ExpectedConditions map onto Playwright, pasted Selenium
code that needs a Playwright version, and "why is my migrated test flaky."

**What it does:**

| Phase | Output |
|---|---|
| 0 — Intake | Repo inventory, complexity bands, cross-cutting decisions, pilot slice |
| 1 — Scaffolding | `playwright.config.ts`, fixtures, auth setup project, CI workflow |
| 2 — Pilot | 3–5 hardest tests migrated end to end to validate the scaffolding |
| 3 — Bulk | Batches of 3–5 files with a per-file changes table and behavior-diff callouts |
| 4 — Parity audit | Assertion-level old-vs-new comparison with verdicts |
| 5 — Decommission | Ordered teardown of the Selenium suite and Grid |

**Bundled:**

- `references/intake.md` — Phase 0 questionnaire and inventory format
- `references/migration-map.md` — waits, locators, lifecycle, API, assertions, infra;
  plus notes for Python / Java / .NET targets
- `references/parity-audit.md` — audit format and pre-decommission checklist
- `scripts/check_antipatterns.py` — lints migrated code for patterns that reintroduce flake

## Manual invocation

```
/test-migration:selenium-to-playwright
```

The skill also triggers automatically from natural phrasing — you rarely need the slash form.

## Running the linter standalone

```bash
python skills/selenium-to-playwright/scripts/check_antipatterns.py tests/
python skills/selenium-to-playwright/scripts/check_antipatterns.py tests/ --json
python skills/selenium-to-playwright/scripts/check_antipatterns.py tests/ --warnings-as-errors
```

Exits non-zero on ERROR findings, so it drops into CI as a gate. Suppress a justified line
with a trailing `// migration-lint: allow` comment.

**ERROR rules:** hard sleeps, surviving Selenium sleeps, non-retrying assertions,
deprecated `$`/`$$` ElementHandle API, leftover Selenium constructs, empty catch blocks.
**WARN rules:** `waitForSelector`, `networkidle` as a settle-wait, serial mode,
branching on element visibility.

## Adding another migration

The phased workflow, output contract, and parity audit are framework-agnostic — only
`references/migration-map.md` is Selenium-specific. To add Cypress → Playwright, copy the
skill directory, swap the map, and adjust the description triggers.
