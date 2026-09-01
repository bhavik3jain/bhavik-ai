#!/usr/bin/env python3
"""Scan migrated Playwright tests for patterns that reintroduce flake.

Usage:
    python check_antipatterns.py <path> [<path> ...]
    python check_antipatterns.py tests/ --warnings-as-errors
    python check_antipatterns.py tests/ --json

Exits 1 if any ERROR-level finding is present, 0 otherwise. WARN findings are
printed but do not fail the run unless --warnings-as-errors is passed.

Every rule here exists because the pattern silently puts back the flakiness the
migration was supposed to remove, or because it is Selenium code that survived
the conversion.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

SCANNED_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".py", ".java", ".cs"}

SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", "target", "bin", "obj",
    "__pycache__", ".venv", "venv", "playwright-report", "test-results",
    ".pytest_cache", ".next", "coverage",
}

# Lines matching these are exempt — a rule may be deliberately suppressed with a
# reason, which is exactly the "one-line justification" the doctrine asks for.
SUPPRESSION = re.compile(r"(?:migration-lint:\s*allow|eslint-disable)", re.I)

# Pure comment lines are skipped: commented-out code does not run, and migration
# notes legitimately mention Selenium constructs by name ("replaced WebDriverWait
# with auto-waiting") without those constructs being present.
COMMENT_LINE = re.compile(r"^\s*(?://|#|\*|/\*)")


@dataclass
class Rule:
    id: str
    severity: str  # ERROR | WARN
    pattern: re.Pattern
    message: str
    fix: str


RULES: list[Rule] = [
    Rule(
        id="hard-sleep",
        severity="ERROR",
        pattern=re.compile(r"\b(?:wait_for_timeout|waitForTimeout)\s*\("),
        message="Hard-coded sleep",
        fix="Wait for the thing you actually mean: a web-first assertion, "
            "page.waitForResponse(), or a specific event.",
    ),
    Rule(
        id="selenium-sleep",
        severity="ERROR",
        pattern=re.compile(r"\b(?:Thread\.sleep|time\.sleep|System\.Threading\.Thread\.Sleep)\s*\("),
        message="Selenium-era sleep survived the migration",
        fix="Delete it. Replace with the assertion or event being waited on.",
    ),
    Rule(
        id="non-retrying-assertion",
        severity="ERROR",
        pattern=re.compile(
            r"(?:expect|Expect)\s*\(\s*await\b[^;]*?\.\s*"
            r"(?:isVisible|isHidden|isEnabled|isDisabled|isChecked|isEditable|"
            r"textContent|innerText|inputValue|getAttribute|allTextContents|count)"
            r"\s*\("
        ),
        message="Assertion snapshots a value instead of retrying",
        fix="Use the web-first form: await expect(locator).toBeVisible() / "
            ".toHaveText() / .toHaveValue() / .toHaveCount().",
    ),
    Rule(
        id="element-handle-api",
        severity="ERROR",
        pattern=re.compile(r"(?<![\w$])(?:page|frame|element|el)\s*\.\s*\$\$?\s*\("),
        message="Deprecated ElementHandle API ($ / $$)",
        fix="Use locators. They re-resolve on every use; handles go stale.",
    ),
    Rule(
        id="selenium-remnant",
        severity="ERROR",
        pattern=re.compile(
            r"\b(?:WebDriverWait|ExpectedConditions|implicitlyWait|implicitly_wait|"
            r"StaleElementReferenceException|PageFactory|FluentWait|DesiredCapabilities|"
            r"WebDriverManager)\b"
        ),
        message="Selenium construct left in migrated code",
        fix="This has no Playwright equivalent because Playwright already does it. "
            "Delete it rather than porting it.",
    ),
    Rule(
        id="empty-catch",
        severity="ERROR",
        pattern=re.compile(r"catch\s*(?:\([^)]*\))?\s*\{\s*(?://[^\n]*)?\s*\}"),
        message="Empty catch block — flake swallowed as control flow",
        fix="Let it fail. If the branch is genuinely optional, assert the "
            "condition explicitly instead of catching.",
    ),
    Rule(
        id="wait-for-selector",
        severity="WARN",
        pattern=re.compile(r"\b(?:waitForSelector|wait_for_selector)\s*\("),
        message="waitForSelector where an assertion is usually clearer",
        fix="await expect(locator).toBeVisible() states intent and appears in "
            "the report as an assertion.",
    ),
    Rule(
        id="network-idle",
        severity="WARN",
        pattern=re.compile(r"(?:waitForLoadState|wait_for_load_state)\s*\(\s*['\"]networkidle"),
        message="networkidle used as a general settle-wait",
        fix="Fine for a genuinely idle page; unreliable on apps with polling or "
            "analytics. Prefer waiting on the specific response.",
    ),
    Rule(
        id="serial-mode",
        severity="WARN",
        pattern=re.compile(r"describe\s*\.\s*serial\b"),
        message="Serial mode — tests depend on each other",
        fix="Usually a ported dependsOnMethods chain. Merge into one test or "
            "move the prerequisite into a fixture.",
    ),
    Rule(
        id="conditional-visibility",
        severity="WARN",
        pattern=re.compile(r"if\s*\(\s*await\b[^;{]*?\.\s*(?:isVisible|isHidden)\s*\("),
        message="Branching on element visibility",
        fix="Often a test that passes whether or not the feature works. "
            "Assert the expected state instead.",
    ),
]

TODO_PATTERN = re.compile(r"TODO\(migration\)")


@dataclass
class Finding:
    path: str
    line: int
    rule: str
    severity: str
    message: str
    fix: str
    text: str


def iter_files(roots: list[Path]):
    for root in roots:
        if root.is_file():
            yield root
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            yield path


def scan(paths: list[Path]) -> tuple[list[Finding], int, int]:
    findings: list[Finding] = []
    todos = 0
    scanned = 0

    for path in iter_files(paths):
        scanned += 1
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            print(f"warning: could not read {path}: {exc}", file=sys.stderr)
            continue

        for lineno, line in enumerate(lines, start=1):
            if TODO_PATTERN.search(line):
                todos += 1
            if SUPPRESSION.search(line) or COMMENT_LINE.match(line):
                continue
            for rule in RULES:
                if rule.pattern.search(line):
                    findings.append(
                        Finding(
                            path=str(path),
                            line=lineno,
                            rule=rule.id,
                            severity=rule.severity,
                            message=rule.message,
                            fix=rule.fix,
                            text=line.strip()[:160],
                        )
                    )

    return findings, todos, scanned


def report(findings: list[Finding], todos: int, scanned: int) -> None:
    errors = [f for f in findings if f.severity == "ERROR"]
    warns = [f for f in findings if f.severity == "WARN"]

    for group, label in ((errors, "ERROR"), (warns, "WARN")):
        if not group:
            continue
        print(f"\n{label}S ({len(group)})")
        print("=" * 60)
        current_rule = None
        for f in sorted(group, key=lambda x: (x.rule, x.path, x.line)):
            if f.rule != current_rule:
                current_rule = f.rule
                print(f"\n[{f.rule}] {f.message}")
                print(f"  fix: {f.fix}")
            print(f"  {f.path}:{f.line}")
            print(f"      {f.text}")

    print(f"\n{'-' * 60}")
    print(f"scanned {scanned} file(s): {len(errors)} error(s), {len(warns)} warning(s)")
    if todos:
        print(f"{todos} unresolved TODO(migration) marker(s) — resolve before decommissioning")
    if not findings:
        print("clean")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--warnings-as-errors", action="store_true", help="fail on WARN findings too"
    )
    args = parser.parse_args()

    missing = [p for p in args.paths if not p.exists()]
    if missing:
        for p in missing:
            print(f"error: no such path: {p}", file=sys.stderr)
        return 2

    findings, todos, scanned = scan(args.paths)

    if args.json:
        print(json.dumps(
            {
                "scanned": scanned,
                "todos": todos,
                "findings": [asdict(f) for f in findings],
            },
            indent=2,
        ))
    else:
        report(findings, todos, scanned)

    failing = [
        f for f in findings
        if f.severity == "ERROR" or (args.warnings_as_errors and f.severity == "WARN")
    ]
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
