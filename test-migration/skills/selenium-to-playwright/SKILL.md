---
name: selenium-to-playwright
description: Migrate a Selenium test suite to Playwright — repo inventory, phased conversion, and assertion-level parity verification. Use this skill whenever the user mentions converting, migrating, porting, or rewriting Selenium tests to Playwright, or asks how WebDriver, Selenium Grid, PageFactory, ExpectedConditions, or explicit waits map onto Playwright. Also use it when the user pastes Selenium test code and wants the Playwright version, even for a single file or a single pattern, and when they ask why a migrated test is flaky or whether a converted test still checks the same thing.
---

# Selenium → Playwright Migration

Convert a Selenium suite into a Playwright suite that keeps the same coverage, is
measurably less flaky, and reads like it was written in Playwright from the start.

The failure mode this skill exists to prevent: a mechanical line-by-line translation
that preserves every `WebDriverWait`, retry loop, and stale-element guard, and produces
a suite that is slower and flakier than the Selenium one it replaced. Migrate intent,
not syntax.

## Stance

Work as a test automation architect who has done this migration before at scale. That
means two habits in particular:

- **Delete more than you translate.** Wait helpers, driver factories, `WebDriverManager`
  setup, custom `ExpectedConditions`, and stale-element retry wrappers mostly do not have
  Playwright equivalents because Playwright already does that work. A 40-line Selenium
  method often becomes 4 lines. That is the migration succeeding, not you cutting corners.
- **Stop and ask rather than guess.** One sharp question beats 400 lines of plausible code
  built on an assumption about a selector or a helper you have never seen.

## Non-negotiables

These override the instinct to be fast or agreeable.

1. **Never invent a selector.** If the original locator or the DOM is not visible to you,
   port it verbatim and mark it `// TODO(migration): selector unverified`. Do not guess at
   a `getByRole` name.
2. **Never silently drop a test.** Anything that cannot be migrated goes in a **Deferred**
   list with a reason — including tests that were already disabled or skipped.
3. **Flag every behavior change.** Playwright's strict mode and auto-waiting will change
   what some tests actually verify. The user needs to know which ones and why.
4. **Ask before architecting.** Fixture design, auth strategy, config shape, and test-data
   approach affect every file downstream. Propose 2–3 options with trade-offs and get a
   decision before building on one.
5. **Stay in scope.** Do not rename tests to taste, refactor product code, or add
   assertions the original did not have. Note improvements separately instead.

## Workflow

Announce which phase you are in at the top of each response. Do not skip ahead — the
whole point of the phasing is to find scaffolding mistakes after 5 files rather than 60.

### Phase 0 — Intake and inventory

Read `references/intake.md`. Gather the project context, then build the inventory.

If you have filesystem access to the repo, do the inventory yourself rather than asking
the user to describe it: find the test files, the page objects, the shared utilities, the
build config, and the CI config, and read enough of them to classify each one. If you do
not have repo access, ask for files in priority order — shared base classes and wait
helpers first, since those shape everything downstream.

Deliver:
- File-by-file inventory: source path → proposed target path → complexity
  (Trivial / Standard / Complex / Needs Human Decision).
- Cross-cutting decisions that need the user's input, each with options and trade-offs.
- A dependency map of shared utilities, marking which ones die in the migration.
- A recommended **pilot slice**: 3–5 tests covering the riskiest patterns *this* suite
  actually contains — auth, iframes, uploads, dynamic tables, whatever is present.
- The top 3 risks specific to this codebase.

Then stop for approval.

### Phase 1 — Scaffolding

Build `playwright.config.ts` (projects per browser, `retries` on CI only,
`trace: 'on-first-retry'`, base URL from env), the folder structure, base fixtures, the
auth setup project, and the CI workflow. Stop for review.

### Phase 2 — Pilot slice

Migrate the approved pilot tests end to end. This is what validates the scaffolding
against real complexity. Encourage the user to actually run these before Phase 3.

### Phase 3 — Bulk migration

Batches of 3–5 files, grouped by feature area so page objects move with their tests.
Stop after each batch. Before writing code in a batch, call out anything that contradicts
an earlier decision, any locator that will hit strict mode, and any test that depends on
another test's state.

### Phase 4 — Parity verification

Read `references/parity-audit.md` and run the audit. Do not let the user delete the
Selenium suite before this passes.

### Phase 5 — Decommission

What to delete from the Selenium project, in what order, and what stays until the new
suite has proven itself over a few CI cycles. Include the Selenium Grid teardown if there
is one — Playwright does not need it.

## Migration doctrine

Read `references/migration-map.md` before migrating any file. It holds the pattern-by-pattern
mapping for waits, locators, structure, lifecycle, API surface, assertions, and infrastructure,
plus notes for non-TypeScript targets.

The four rules that matter most, if you read nothing else:

- Every wait you **port instead of delete** needs a one-line justification.
- DOM assertions become web-first assertions: `await expect(locator).toHaveText('X')`,
  never `expect(await locator.textContent()).toBe('X')`. Only the first form retries,
  and that difference is most of the flake reduction.
- Locator priority: `getByRole` → `getByLabel` → `getByPlaceholder` → `getByText` →
  `getByTestId` → CSS → XPath.
- Strict mode: any locator that matched multiple elements will now throw where Selenium's
  `findElement` silently took the first. These are the migration's most common surprise.

## Output contract

For every file migrated, produce exactly this:

````
### `<original/path/File.java>` → `<new/path/file.spec.ts>`
**Complexity:** Standard | **Tests migrated:** 6 of 7 (1 deferred)

```ts
<complete file — no ellipses, no "rest unchanged", no placeholders except
 explicitly marked TODO(migration) items>
```

**What changed and why**
| Original | New | Reason |
|---|---|---|
| `WebDriverWait ... elementToBeClickable` (L34–37) | removed | auto-waiting covers this |
| `//table//tr[2]/td[3]` (L51) | `getByRole('row').filter(...)` | brittle positional XPath |

**Behavior differences** (write "None" if none)
- `productLink` matched 3 elements; Selenium took the first, strict mode will throw.
  Scoped to `.results` — confirm that is the intended element.

**Deferred**
- `testLegacyFlashUpload` — depends on a component removed from the app. Recommend deletion.

**Questions blocking full confidence**
- `TestUtils.waitForGridLoad()` is not in what I have seen. What does it wait on?
````

At the end of each batch, append a running **Migration Log**: files done, files remaining,
open questions outstanding, decisions made. Long migrations span sessions; the log is what
keeps settled decisions from being re-litigated.

## Banned in committed output

If any of these appear in code you are about to hand over, rewrite it:

- `page.waitForTimeout()` — no exceptions in committed tests.
- `expect(await locator.isVisible()).toBe(true)` and its siblings (`isEnabled`,
  `textContent`, `innerText`) — these do not retry.
- `page.waitForSelector()` where a web-first assertion does the job.
- `page.$` / `page.$$` — deprecated ElementHandle API.
- try/catch used as flow control to swallow flake.
- Conditional logic that lets a test pass either way.
- Tests that depend on execution order or another test's side effects.
- Ported sleep-based retry loops in any disguise.

Run the checker over generated code before presenting a batch:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/selenium-to-playwright/scripts/check_antipatterns.py <path-to-migrated-tests>
```

Run it directly with the Bash tool — do not ask the user to run it. It exits non-zero
and prints file:line for each violation. Fix what it finds rather than explaining it away —
every rule it enforces exists because that pattern silently reintroduces the flake the
migration was supposed to remove.

## Reference files

- `references/intake.md` — Phase 0 questionnaire, inventory format, decisions to surface early.
- `references/migration-map.md` — the full pattern mapping; read before migrating any file.
- `references/parity-audit.md` — Phase 4 audit format and the pre-decommission checklist.
- `${CLAUDE_PLUGIN_ROOT}/skills/selenium-to-playwright/scripts/check_antipatterns.py` —
  deterministic lint for the banned list above.
