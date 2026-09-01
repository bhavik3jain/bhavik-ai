# Phase 0 — Intake and Inventory

## Context to establish

Fill these in before writing any test code. If you have repo access, answer as many as you
can yourself and bring the user only the gaps — arriving with "I found 62 page objects and
a `BaseTest` with a static WebDriver; here are the three things I can't tell from the code"
is far better than handing them a blank questionnaire.

**Stack**
- Source language and Selenium version (Java 17 + Selenium 4.x, Python + Selenium 4, C#, JS)
- Source test runner (TestNG, JUnit 4/5, pytest, NUnit, MSTest, Mocha)
- Source build tool (Maven, Gradle, poetry, dotnet)
- Target language — `@playwright/test` (TypeScript) is the default and the most complete
  binding; only pick Python/Java/.NET if the team has a reason
- Target package manager

**Suite shape**
- Test count and page-object count
- Design pattern in use (POM with `@FindBy`/PageFactory, POM with explicit finders,
  keyword-driven, BDD via Cucumber, or no pattern at all)
- Test data strategy (hardcoded, Excel/CSV, DB seeding, API setup, faker)
- Authentication (form login, SSO redirect, API token, MFA)
- Environments and how base URLs are configured
- Required browser coverage, including mobile viewports
- CI system, and whether there is a Selenium Grid / Selenoid / cloud provider
  (BrowserStack, Sauce Labs, LambdaTest) in the picture
- Current reporting (Allure, ExtentReports, TestNG HTML, surefire)

**Reality check**
- App under test: SPA or MPA, framework, and the parts that make testing hard —
  nested iframes, canvas, infinite scroll, third-party widgets, file downloads,
  server-rendered partial updates
- Known pain points, with numbers if they have them ("checkout fails ~15% of runs",
  "80 calls to `Thread.sleep`")
- Non-negotiable constraints — must keep Allure, must run on existing agents, cannot add
  `data-testid` attributes to the app, must run against IE/legacy Edge (which Playwright
  does not support — surface this immediately if it comes up)

## Whether BDD survives

If the suite uses Cucumber/SpecFlow/behave, this is a decision, not a detail. Ask early:
keep the Gherkin layer (playwright-bdd, or Cucumber calling Playwright) or collapse the
step definitions into plain Playwright tests. Teams that adopted BDD for non-technical
stakeholder buy-in usually keep it; teams where only engineers ever read the features
usually collapse it and are happier. Do not decide this silently.

## Inventory format

```
| Source | Target | Complexity | Notes |
|---|---|---|---|
| src/test/java/tests/LoginTest.java | tests/auth/login.spec.ts | Trivial | 3 tests, form login |
| src/test/java/pages/CheckoutPage.java | pages/checkout.page.ts | Complex | 3 nested iframes, 11 waits |
| src/test/java/utils/WaitHelper.java | — | Delete | replaced by auto-waiting |
| src/test/java/base/BaseTest.java | fixtures/base.ts | Needs Human Decision | static driver, shared state |
```

Complexity bands:
- **Trivial** — direct mapping, no custom waits, stable selectors.
- **Standard** — routine waits and page-object structure; the bulk of most suites.
- **Complex** — iframes, popups, downloads, uploads, drag-and-drop, canvas, custom JS
  execution, or heavy conditional logic.
- **Needs Human Decision** — shared mutable state, test interdependence, ambiguous intent,
  or something that suggests the test is testing the framework rather than the app.

## Decisions to surface before Phase 1

Present each with 2–3 options and a recommendation. These are expensive to change later:

1. **Fixture layer.** What gets a custom fixture (authenticated page, seeded test data,
   API client) versus what stays in `beforeEach`.
2. **Auth strategy.** Almost always: log in once in a setup project, save `storageState`,
   reuse everywhere. Quantify the win — a suite that logs in through the UI 340 times is
   spending most of its runtime on login.
3. **Page object shape.** Locators as readonly fields set in the constructor; methods that
   perform user actions and return nothing (or the next page object). Whether to keep a
   `BasePage` at all — often it exists only to hold the driver and wait helpers, both of
   which are now gone.
4. **Test data.** Whether Excel/CSV fixtures move as-is, become JSON/TS fixtures, or get
   replaced by API-based setup.
5. **Test independence.** If TestNG `dependsOnMethods` or ordered execution exists, it must
   go. Options: merge dependent tests into one, or move the prerequisite into a fixture.
6. **Reporting.** HTML reporter + trace viewer covers most of what Allure/Extent was doing.
   If Allure is contractual, use `allure-playwright`.
7. **Grid and cloud providers.** Playwright runs browsers in the CI container; parallelism
   comes from `workers` and `--shard`. If they are paying for a grid or a cloud device farm,
   flag it as a cost line that may disappear — but check whether they need it for real-device
   or Safari-on-macOS coverage first.

## Pilot slice selection

Pick 3–5 tests that between them exercise the riskiest patterns present in this suite.
Justify each pick. Typical strong slice:

- One auth flow (validates the `storageState` setup end to end)
- One test with the suite's worst wait logic (validates the delete-don't-port doctrine)
- One structurally hard test — iframe, popup, upload, or download
- One data-driven test (validates the parameterization approach)

Bad pilot slice: five easy login tests. It proves nothing and the scaffolding breaks in
Phase 3 instead.
