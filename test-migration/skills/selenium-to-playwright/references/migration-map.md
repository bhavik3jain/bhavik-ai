# Migration Map

Pattern-by-pattern mapping. Examples are TypeScript (`@playwright/test`); see
[Non-TypeScript targets](#non-typescript-targets) at the end for other bindings.

Where a rule conflicts with how the source code is structured, follow the rule and explain
the deviation in the changes table.

## Contents

- [Waiting](#waiting) — the core of the migration
- [Locators](#locators)
- [Structure and lifecycle](#structure-and-lifecycle)
- [API surface](#api-surface)
- [Assertions](#assertions)
- [Infrastructure](#infrastructure)
- [Non-TypeScript targets](#non-typescript-targets)

## Waiting

Most of the reliability gain in this migration comes from deleting wait code. Playwright's
actions perform actionability checks — visible, stable, enabled, receives events — and
retry until they pass or time out. Explicit waits before an action are redundant, and
sleeps are worse than redundant because they encode a guess about timing.

| Selenium | Playwright |
|---|---|
| `driver.manage().timeouts().implicitlyWait(...)` | Delete. Configure `expect.timeout` / `actionTimeout` in config instead. |
| `wait.until(ExpectedConditions.visibilityOf(el))` | Delete if an action follows. Otherwise `await expect(locator).toBeVisible()`. |
| `wait.until(elementToBeClickable(el)); el.click();` | `await locator.click()` |
| `wait.until(presenceOfElementLocated(by))` | Delete — locators resolve at use time. |
| `Thread.sleep(2000)` / `time.sleep(2)` | Delete. Replace with the assertion or event actually being waited for. |
| retry loop catching `StaleElementReferenceException` | Delete. Locators re-resolve on every use. |
| `wait.until(textToBePresentInElement(el, "Done"))` | `await expect(locator).toHaveText('Done')` |
| `wait.until(invisibilityOf(spinner))` | `await expect(spinner).toBeHidden()` — or better, `page.waitForResponse()` on the real request. |
| `wait.until(numberOfElementsToBe(by, 5))` | `await expect(locator).toHaveCount(5)` |
| `wait.until(urlContains("/dashboard"))` | `await expect(page).toHaveURL(/dashboard/)` |
| `wait.until(alertIsPresent())` | Register `page.on('dialog', ...)` before the trigger. |
| custom `FluentWait` with polling interval | Web-first assertion; polling is built in. |
| JS-executor readiness poll (`document.readyState`, jQuery `active === 0`) | Usually deletable. If the app has a genuine custom idle signal, use `page.waitForFunction()` and say why. |

**The one-line justification rule:** any wait you port instead of delete gets a comment
explaining what it waits on that auto-waiting does not cover. If you cannot write that
comment, the wait should not exist.

**Legitimate remaining waits** — these are real, do not over-delete:
- `page.waitForResponse()` / `waitForRequest()` for a specific network call
- `page.waitForEvent('download' | 'popup' | 'filechooser')`
- `page.waitForLoadState('networkidle')` — sparingly, and never as a general-purpose
  "wait for the page to settle"
- `page.waitForFunction()` for genuinely custom client-side state

## Locators

Priority order: `getByRole` → `getByLabel` → `getByPlaceholder` → `getByText` →
`getByTestId` → CSS → XPath.

- Rewrite brittle positional XPath (`//div[3]/span[2]`) into a semantic locator **only if**
  the source gives you enough information to do it correctly. Otherwise port it verbatim
  with `// TODO(migration): brittle XPath, needs semantic replacement`. A confidently wrong
  `getByRole` is worse than an honest ported XPath.
- `driver.findElements(...)` + index → chained locators, `.filter({ hasText })`, or `.nth()`.
  Prefer filtering over indexing; indexes encode DOM order that changes.
- `driver.findElements(...)` + loop over all → `locator.all()`, or better, a single
  assertion like `toHaveText([...])` over the collection.
- Selenium chained finds (`el.findElement(By...)`) → locator chaining
  (`parent.getByRole(...)`), which also scopes away strict-mode collisions.

**Strict mode.** Playwright throws when a locator resolves to more than one element;
Selenium's `findElement` silently returned the first. Every ambiguous locator in the source
is a latent behavior change. Flag each one and either scope it to a container or use an
explicit `.first()` with a comment saying that matching the first element was the original
behavior — do not sprinkle `.first()` everywhere to silence the error, because that hides
real ambiguity in the app.

**Text matching.** Selenium's `By.linkText` is exact; `partialLinkText` is substring.
Playwright's `getByText` defaults to substring and case-insensitive-ish normalization —
use `{ exact: true }` when the original was exact, or the test gets looser without anyone
noticing.

## Structure and lifecycle

| Selenium | Playwright |
|---|---|
| `@BeforeMethod` driver setup, `WebDriverManager.chromedriver().setup()` | Delete — the `page` fixture provides an isolated context per test. |
| `@AfterMethod driver.quit()` | Delete — contexts are disposed automatically. |
| `BasePage` holding `WebDriver driver` | Page object taking `page: Page`; locators as `readonly` fields set in the constructor. |
| `@FindBy` + `PageFactory.initElements` | `this.submit = page.getByRole('button', { name: 'Submit' })` in the constructor. |
| `BaseTest` with shared/static driver | Custom fixtures via `test.extend`. Static drivers are the single biggest source of breakage under parallel execution — flag them loudly. |
| login in `@BeforeMethod` | `storageState` from a setup project; log in once, reuse everywhere. |
| TestNG groups / JUnit tags | `test.describe` plus `@tag` annotations, filtered with `--grep`. |
| `@DataProvider` / `@Parameterized` | Loop over an array generating `test()` calls, or a parameterized fixture. |
| `dependsOnMethods`, `@FixMethodOrder`, `priority` | No equivalent by design. Merge dependent tests into one, or move the prerequisite into a fixture. Never emulate ordering. |
| `@Test(retryAnalyzer = ...)` | `retries` in config, CI-only, with `trace: 'on-first-retry'`. |
| ITestListener / TestWatcher for screenshots | Built in — `screenshot: 'only-on-failure'`, plus traces. |
| Cucumber step definitions | Either playwright-bdd, or collapse steps into plain tests. Decide in Phase 0. |

**Test independence is now enforced, not encouraged.** Files run in parallel by default,
tests within a file run in order but share nothing. Any shared mutable state — static
fields, singletons, a database record every test mutates, a shared user account — will
surface as flake. Inventory these during Phase 0 and treat each as a Needs Human Decision.

## API surface

| Selenium | Playwright |
|---|---|
| `new Select(el).selectByVisibleText("X")` | `locator.selectOption({ label: 'X' })` |
| `new Select(el).selectByValue("x")` | `locator.selectOption('x')` |
| `el.sendKeys("text")` | `locator.fill('text')` — use `pressSequentially()` only when per-keystroke handlers matter. |
| `el.clear(); el.sendKeys(...)` | `locator.fill(...)` — fill clears first. |
| `el.sendKeys(Keys.ENTER)` | `locator.press('Enter')` |
| `Actions.moveToElement(el).perform()` | `locator.hover()` |
| `Actions.dragAndDrop(a, b).perform()` | `a.dragTo(b)` |
| `Actions.contextClick(el)` | `locator.click({ button: 'right' })` |
| `Actions.doubleClick(el)` | `locator.dblclick()` |
| `driver.switchTo().frame(...)` | `page.frameLocator('#f').getByRole(...)` — chainable for nested frames. |
| `driver.switchTo().defaultContent()` | No equivalent needed; frame locators are scoped. |
| `driver.switchTo().alert().accept()` | `page.on('dialog', d => d.accept())`, registered **before** the trigger. |
| `driver.getWindowHandles()` + switch | `const [popup] = await Promise.all([context.waitForEvent('page'), trigger()])` |
| `((JavascriptExecutor) driver).executeScript(...)` | `page.evaluate(...)` — but first check whether it is needed at all. JS-executor clicks usually exist to work around a wait problem that no longer exists. |
| `el.sendKeys(filePath)` for upload | `locator.setInputFiles(path)` |
| upload via OS dialog / AutoIT / Robot | `page.waitForEvent('filechooser')` then `fileChooser.setFiles(...)` — a large simplification, call it out. |
| download via browser prefs + polling the FS | `const download = await page.waitForEvent('download'); await download.saveAs(...)` |
| `driver.manage().addCookie(...)` | `context.addCookies([...])`, or `storageState`. |
| `driver.getScreenshotAs(...)` | `page.screenshot()`, plus automatic failure screenshots and traces. |
| BrowserMob / WireMock / proxy mocking | `page.route()` — in-process, no proxy. Major simplification. |
| `driver.navigate().refresh()` | `page.reload()` |
| headless via ChromeOptions | `headless` in config, per project. |

## Assertions

The single highest-value substitution in the migration:

```ts
// Wrong — snapshots once, does not retry, reintroduces the flake you removed
expect(await locator.textContent()).toBe('Done');
expect(await locator.isVisible()).toBe(true);

// Right — retries until it passes or times out
await expect(locator).toHaveText('Done');
await expect(locator).toBeVisible();
```

| Selenium + framework assert | Playwright |
|---|---|
| `Assert.assertEquals(el.getText(), "X")` | `await expect(locator).toHaveText('X')` |
| `Assert.assertTrue(el.isDisplayed())` | `await expect(locator).toBeVisible()` |
| `Assert.assertTrue(el.isEnabled())` | `await expect(locator).toBeEnabled()` |
| `Assert.assertEquals(el.getAttribute("value"), "X")` | `await expect(locator).toHaveValue('X')` |
| `Assert.assertEquals(driver.getTitle(), "X")` | `await expect(page).toHaveTitle('X')` |
| `Assert.assertTrue(driver.getCurrentUrl().contains("x"))` | `await expect(page).toHaveURL(/x/)` |
| `Assert.assertEquals(els.size(), 5)` | `await expect(locator).toHaveCount(5)` |
| `SoftAssert` | `expect.soft(...)` |
| comparing two computed values, API fields | plain `expect(value).toBe(...)` — non-DOM assertions do not need the retrying form. |

**Implicit assertions count.** A Selenium test that calls `findElement` on a missing element
throws and fails — that is an assertion even though nobody wrote one. When migrating, make
sure the Playwright version still fails in that case. Usually it does (the action times out),
but note it in the parity audit rather than assuming.

## Infrastructure

**Selenium Grid.** Not needed. Playwright launches browsers in the CI container; parallelism
comes from `workers` locally and `--shard=1/4` across CI jobs. Plan the Grid teardown in
Phase 5 — but confirm first that the grid was not serving a need Playwright does not cover
(real devices, Safari on macOS, IE11).

**Browser coverage.** Playwright ships Chromium, Firefox, and WebKit. WebKit approximates
Safari but is not Safari; if the team has Safari-specific bugs in production, say so rather
than implying full parity. Playwright does not support IE11 at all — if the suite covers it,
that is a scope conversation, not a migration detail.

**Config shape** for `playwright.config.ts`:
- `projects` per browser, plus a `setup` project for auth that others depend on
- `retries: process.env.CI ? 2 : 0`
- `trace: 'on-first-retry'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'`
- `use.baseURL` from env, so tests use relative paths
- `fullyParallel: true` unless shared state forces otherwise — and if it does, that is a
  finding to report, not a setting to quietly flip

**Reporting.** The HTML reporter plus the trace viewer replaces most of what Allure and
ExtentReports were doing, and the trace viewer replaces almost all screenshot-on-failure
tooling. If Allure is a hard requirement, use `allure-playwright`.

## Non-TypeScript targets

TypeScript (`@playwright/test`) is the reference binding and gets features first. If the
target is another language, the doctrine above holds; the syntax changes:

**Python** — `pytest-playwright`. Sync API by default (no `await`); use the async API only
if the team already writes async. Assertions come from `playwright.sync_api.expect`:
`expect(locator).to_have_text("Done")`. Fixtures are pytest fixtures. Config lives in
`pytest.ini` / `pyproject.toml` plus CLI flags rather than a config file, so the "projects"
concept maps onto markers and CLI options — flag this as a real difference, not a cosmetic one.

**Java** — often the least disruptive target for a Java Selenium team, since JUnit5/TestNG
and the build stay put. Assertions: `assertThat(locator).hasText("Done")` from
`com.microsoft.playwright.assertions.PlaywrightAssertions`. No test-runner-level fixtures,
so setup stays in `@BeforeEach` with `Playwright`/`Browser`/`BrowserContext` lifecycle
managed explicitly. Parallelism is the runner's, not Playwright's.

**.NET** — `Microsoft.Playwright.NUnit` / `.MSTest`. Inherit from `PageTest` for a per-test
page. Assertions: `await Expect(locator).ToHaveTextAsync("Done")`.

**Recommend TypeScript when the team is willing.** The test runner, fixtures, projects,
sharding, trace viewer integration, and UI mode are all richest there, and a large part of
the promised reliability gain lives in the runner rather than the browser automation. But
this is the team's call, and "we will never maintain TypeScript" is a legitimate answer —
if they choose their existing language, do not relitigate it every phase.
