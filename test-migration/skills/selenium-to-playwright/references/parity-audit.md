# Phase 4 — Parity Audit

The audit exists because "it compiles and passes" is not evidence that coverage survived.
A migrated suite can be green and check less than it used to. Nobody finds out until the
bug it used to catch ships.

Do not let the Selenium suite be deleted before this passes.

## Audit table

One row per **original** test method — driven from the old suite, not the new one, so
anything dropped shows up as a missing row rather than being invisible.

| Original test | New test | Assertions old → new | Verdict |
|---|---|---|---|
| `LoginTest.testValidLogin` | `auth/login.spec.ts:valid credentials` | 3 → 3 | EQUIVALENT |
| `CartTest.testRemoveItem` | `cart/cart.spec.ts:removes an item` | 4 → 3 | WEAKER |

Verdicts:

- **EQUIVALENT** — same behavior verified. Only use this after an actual line-by-line
  comparison. Do not use it as a default for tests you have not re-read.
- **STRONGER** — the new test verifies more. Usually because a web-first assertion replaced
  a bare action, or an implicit check became explicit. Still worth a note.
- **WEAKER** — verifies less. Needs a paragraph: what coverage was lost, why, and whether
  it matters.
- **CHANGED** — verifies something different. Most often caused by strict-mode scoping
  landing on a different element than Selenium's silent first-match.
- **DEFERRED** — not migrated yet, with the blocker named.
- **DROPPED** — intentionally not migrated, with the reason and the user's sign-off.

## Counting rules

- Count assertions literally, including framework asserts and `expect` calls.
- **Count implicit assertions.** A Selenium test that calls `findElement` on an element that
  might not exist fails when it is missing. That is coverage. State explicitly whether the
  Playwright version still fails in that case — usually the action times out and it does,
  but confirm rather than assume.
- A single web-first assertion replacing a wait *and* an assert is 2 → 1 in raw count but
  not weaker. Note it as EQUIVALENT with an explanation rather than letting the numbers
  imply a regression.
- Negative assertions deserve extra scrutiny. `assertFalse(el.isDisplayed())` in Selenium
  often passed because the element was not there *yet*. `expect(locator).toBeHidden()`
  waits, so it can legitimately fail where the old test passed — that is the new test being
  correct and the old one being accidentally green. Flag these; they are the most common
  source of "the migration broke our tests" complaints that are actually the migration
  working.

## Closing summary

End the audit with:

1. **Coverage delta** — totals by verdict, and a one-sentence honest read on whether
   coverage went up, down, or sideways.
2. **Top 5 manual verifications** — the specific things a human should click through before
   the Selenium suite is deleted. Prioritize anything marked CHANGED or WEAKER, anything
   involving money, auth, or permissions, and anything where you had to guess a selector.
3. **Outstanding `TODO(migration)` markers** — grouped by file, since unverified selectors
   are the debt this migration leaves behind.
4. **Flake baseline** — recommend running the new suite 10–20 times in CI before
   decommissioning, and record the pass rate. The migration's central claim is improved
   reliability; that claim should have a number attached.

## Pre-decommission checklist

Before Phase 5, confirm all of these:

- [ ] Every original test appears in the audit table with a verdict.
- [ ] No WEAKER or CHANGED row lacks an explanation and a user decision.
- [ ] `check_antipatterns.py` passes clean across the whole new suite.
- [ ] No `TODO(migration)` markers remain on selectors in critical-path tests.
- [ ] The suite has run green repeatedly in CI, not just locally, and the pass rate is recorded.
- [ ] The suite has been run with `--repeat-each=3` at least once to surface order-dependence
      and shared-state issues that a single run hides.
- [ ] CI runs the new suite in parallel/sharded configuration, not serially — parallelism is
      where shared-state bugs appear.
- [ ] Reporting is wired up and someone other than you has looked at a report.
- [ ] The team knows how to open a trace file. This is the single highest-value habit the
      migration gives them, and it is the one most often left untaught.
