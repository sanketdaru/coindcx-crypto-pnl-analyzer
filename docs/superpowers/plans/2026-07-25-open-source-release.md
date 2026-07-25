# Open Source Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish this crypto tax calculator as a properly licensed, liability-limited, discoverable open source project.

**Architecture:** Pure additive change — no P&L logic is modified except adding a runtime disclaimer. Legal and community documents are plain Markdown at the repo root. The landing page is a single self-contained HTML file in `site/`, deployed to GitHub Pages by an Actions workflow. Repository metadata is set through the `gh` CLI.

**Tech Stack:** Python 3.13, `uv`, pytest, plain HTML/CSS (no framework, no CDN), GitHub Actions, `gh` CLI.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-25-open-source-release-design.md`
- Repository after rename: `sanketdaru/india-crypto-tax-calculator`
- Canonical site URL: `https://sanketdaru.github.io/india-crypto-tax-calculator/`
- Copyright line, verbatim: `Copyright 2026 Sanket Daru`
- License: Apache License 2.0 (SPDX `Apache-2.0`)
- Default branch: `master`
- Working branch: `chore/open-source-release`
- Python: 3.13. Test command is always `uv run pytest`.
- **Tests must never read `crypto_transactions.xlsx`, `crypto_transactions_mar2026.xlsx`, or any generated report.** These are gitignored real personal data and are absent in CI. Tests that need a workbook must build one in `tmp_path`.
- The site must be fully self-contained: no CDN, no external fonts, no analytics, no remote images. Inline CSS and an inline SVG favicon only.
- Never publish a personal email address in any file.
- "CoinDCX" appears only as a factual description of the file format read, never as branding. Every document that names it must be reachable from a non-affiliation notice.
- Existing 24 tests in `tests/test_crypto_pnl_calculator.py` must stay green throughout.

---

### Task 1: License, NOTICE and repository rename

**Files:**
- Create: `LICENSE`
- Create: `NOTICE`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: nothing.
- Produces: the repo name `india-crypto-tax-calculator` and the canonical URL `https://sanketdaru.github.io/india-crypto-tax-calculator/`, both used by every later task.

- [ ] **Step 1: Fetch the canonical Apache 2.0 text**

Do not transcribe it by hand — a mistyped license is a defective license.

```bash
curl -sSL https://www.apache.org/licenses/LICENSE-2.0.txt -o LICENSE
```

- [ ] **Step 2: Verify the license file is intact**

```bash
wc -l LICENSE && grep -c "Limitation of Liability" LICENSE && tail -n 5 LICENSE
```

Expected: about 202 lines, at least one match for "Limitation of Liability", and the file ends with the boilerplate appendix. If `curl` failed, `LICENSE` will be empty or an HTML error page — stop and retry rather than continuing.

- [ ] **Step 3: Append the copyright line**

The canonical text ends with an appendix containing bracketed placeholders. Replace the placeholder line so the copyright is asserted.

```bash
python3 - <<'PY'
from pathlib import Path
p = Path('LICENSE')
text = p.read_text()
old = "   Copyright [yyyy] [name of copyright owner]"
assert old in text, "placeholder line not found; inspect LICENSE manually"
p.write_text(text.replace(old, "   Copyright 2026 Sanket Daru"))
print("copyright set")
PY
```

- [ ] **Step 4: Create `NOTICE`**

```text
India Crypto Tax Calculator
Copyright 2026 Sanket Daru

This product is licensed under the Apache License, Version 2.0.
See the LICENSE file for the full terms.

This software is NOT tax, legal or financial advice, and is provided
without warranty of any kind. See DISCLAIMER.md before using it for
anything that affects a tax return.

This project is not affiliated with, endorsed by, or sponsored by
CoinDCX or Neblio Technologies Private Limited. "CoinDCX" is used only
to identify the trade report file format this software reads. All
trademarks are the property of their respective owners.
```

- [ ] **Step 5: Update `pyproject.toml`**

Replace the `[project]` table's `name` and `description`, and add license, keywords and URLs. Keep `requires-python`, `dependencies` and `dependency-groups` exactly as they are.

```toml
[project]
name = "india-crypto-tax-calculator"
version = "0.2.0"
description = "Turn CoinDCX trade exports into FIFO profit and loss reports for Indian crypto tax under Section 115BBH of the Income Tax Act, 1961."
readme = "README.md"
license = "Apache-2.0"
license-files = ["LICENSE", "NOTICE"]
keywords = [
    "crypto-tax",
    "india",
    "section-115bbh",
    "vda",
    "fifo",
    "capital-gains",
    "income-tax",
    "cryptocurrency",
    "coindcx",
]
requires-python = ">=3.13"
dependencies = [
    "openpyxl>=3.1.5",
    "pandas>=3.0.1",
]

[project.urls]
Homepage = "https://sanketdaru.github.io/india-crypto-tax-calculator/"
Repository = "https://github.com/sanketdaru/india-crypto-tax-calculator"
Issues = "https://github.com/sanketdaru/india-crypto-tax-calculator/issues"
```

- [ ] **Step 5a: Verify the environment still resolves**

```bash
uv sync && uv run pytest -q
```

Expected: sync succeeds, 24 passed. If `license-files` or the SPDX `license` string is rejected by the installed `uv`, fall back to `license = { text = "Apache-2.0" }` and drop `license-files`, then re-run.

- [ ] **Step 6: Commit the local changes before renaming**

```bash
git add LICENSE NOTICE pyproject.toml uv.lock
git commit -m "Add Apache 2.0 license and NOTICE, rename project

Licensing the project under Apache 2.0 rather than MIT: its explicit
Disclaimer of Warranty and Limitation of Liability sections matter for
a tool whose output goes on a tax return.

Rename to india-crypto-tax-calculator, dropping the CoinDCX trademark
from the project identity. CoinDCX is still named in prose where it
factually describes the export format read."
```

- [ ] **Step 7: Rename the GitHub repository**

```bash
gh repo rename india-crypto-tax-calculator --repo sanketdaru/coindcx-crypto-pnl-analyzer --yes
```

GitHub permanently redirects the old URL, so existing clones and links keep working.

- [ ] **Step 8: Point the local remote at the new name and verify**

```bash
git remote set-url origin git@github.com:sanketdaru/india-crypto-tax-calculator.git
git remote -v
gh repo view sanketdaru/india-crypto-tax-calculator --json name,visibility,licenseInfo
```

Expected: remote shows the new name; `gh repo view` returns `"name": "india-crypto-tax-calculator"`. `licenseInfo` may still be `null` until the license commit reaches `master` — that is expected at this stage.

---

### Task 2: DISCLAIMER.md and the runtime notice

**Files:**
- Create: `DISCLAIMER.md`
- Modify: `crypto_pnl_calculator.py`
- Test: `tests/test_disclaimer.py`

**Interfaces:**
- Consumes: the repo URL from Task 1.
- Produces: module-level constant `DISCLAIMER` (a `str`) and function `print_disclaimer() -> None` in `crypto_pnl_calculator.py`. Task 7 links to `DISCLAIMER.md`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_disclaimer.py`. The second test builds its own workbook in `tmp_path` — it must not touch the real gitignored exports.

```python
"""The disclaimer must survive refactors: it is the only copy a user cannot skip."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import crypto_pnl_calculator  # noqa: E402
from crypto_pnl_calculator import DISCLAIMER, print_disclaimer  # noqa: E402


REQUIRED_PHRASES = [
    'NOT TAX ADVICE',
    'no warranty',
    'qualified tax professional',
    'You alone are responsible',
    'DISCLAIMER.md',
]


@pytest.mark.parametrize('phrase', REQUIRED_PHRASES)
def test_disclaimer_text_contains_required_phrase(phrase):
    assert phrase in DISCLAIMER


def test_print_disclaimer_writes_to_stdout(capsys):
    print_disclaimer()
    assert 'NOT TAX ADVICE' in capsys.readouterr().out


def _write_workbook(path: Path) -> None:
    """Build a minimal CoinDCX-shaped workbook: 8 filler rows, then headers."""
    instant = pd.DataFrame([
        {
            'Transaction ID': 'a1',
            'Crypto': 'BTC',
            'Transaction time': '2025-04-01 10:00:00',
            'Side (Buy/Sell)': 'Buy',
            'Avg Buying/Selling Price(in INR)': 5_000_000.0,
            'Quantity': 0.001,
            'Gross Amount Paid/Received by the user(in INR)': 5000.0,
            'Fees(in INR)': 29.5,
            'Net Amount Paid/Received by the user(in INR)': 5029.5,
            '**TDS(in INR)': None,
        },
    ])
    spot = pd.DataFrame(columns=[
        'Order ID', 'Trade ID', 'Crypto Pair', 'Base currency',
        'Trade Completion time', 'Side (Buy/Sell)',
        'Avg Buying/Selling Price(in base currency)', 'Quantity',
        'Gross Amount Paid/Received by the user(in base currency)',
        'Fees(in base currency)',
        'Net Amount Paid/Received by the user(in base currency)',
        '*Net Amount Paid/Received by the user (in INR)',
        '**TDS(in base currency)', '**TDS (in INR)',
    ])
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        for name, frame in (('Instant Orders', instant), ('Spot Orders', spot)):
            frame.to_excel(writer, sheet_name=name, index=False, startrow=8)


def test_run_prints_disclaimer_before_the_report(tmp_path, capsys):
    source = tmp_path / 'transactions.xlsx'
    _write_workbook(source)

    calculator = crypto_pnl_calculator.CryptoPnLCalculator(str(source))
    calculator.run(str(tmp_path / 'report.xlsx'))

    out = capsys.readouterr().out
    assert 'NOT TAX ADVICE' in out
    assert out.index('NOT TAX ADVICE') < out.index('CRYPTO ASSET P&L CALCULATOR')
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run pytest tests/test_disclaimer.py -v
```

Expected: collection error — `ImportError: cannot import name 'DISCLAIMER' from 'crypto_pnl_calculator'`.

- [ ] **Step 3: Add the constant and function to `crypto_pnl_calculator.py`**

Insert directly below the `KNOWN_QUOTE_CURRENCIES` constant near the top of the module.

```python
DISCLAIMER = """\
================================================================================
  NOT TAX ADVICE - READ BEFORE USING THIS OUTPUT
================================================================================
  This software is provided as-is, with no warranty, and its author is not a
  tax professional. Its output is a starting point, not a filing.

  Verify every figure with a qualified tax professional before you file.
  You alone are responsible for what you file and for any tax, interest or
  penalty arising from it.

  Limitations, in full: DISCLAIMER.md
  https://github.com/sanketdaru/india-crypto-tax-calculator/blob/master/DISCLAIMER.md
================================================================================
"""


def print_disclaimer() -> None:
    """Print the disclaimer. Called on every run - a user cannot skip past it."""
    print(DISCLAIMER)
```

- [ ] **Step 4: Call it at the top of `CryptoPnLCalculator.run()`**

Find the first three lines of the `run()` body and put the call above them.

```python
    def run(self, output_file: Optional[str] = None) -> str:
        """Main execution flow"""
        print_disclaimer()

        print("=" * 80)
        print("CRYPTO ASSET P&L CALCULATOR - FIFO METHOD (Section 115BBH)")
        print("=" * 80)
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
uv run pytest -q
```

Expected: 31 passed (24 existing + 7 new — the parametrized phrase test contributes 5).

- [ ] **Step 6: Create `DISCLAIMER.md`**

```markdown
# Disclaimer

**Read this before using any output from this software in a tax return.**

## This is not professional advice

This software and its documentation are **not** tax, legal, accounting or
financial advice.

The author is not a chartered accountant, a registered tax practitioner, or a
lawyer. Nothing here creates an advisor-client, accountant-client or
attorney-client relationship. No one has reviewed your particular circumstances.

## Verify before you file

Treat the output as a **starting point for a conversation with a qualified tax
professional**, not as a finished computation. Reconcile every figure against
your own records and your exchange statements before relying on it.

## You are responsible

You alone are responsible for the accuracy and completeness of everything you
file, and for any tax, interest, penalty, prosecution or other consequence
arising from it. That responsibility does not transfer to the author of this
software by your use of it.

## No warranty

This software is licensed under the Apache License 2.0 and is provided on an
"AS IS" BASIS, **WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND**, either express
or implied. See sections 15 and 16 of [LICENSE](LICENSE) for the controlling
legal text. In plain language: it may contain errors, it may produce wrong
numbers, and the author is not liable for any damages arising from its use.

## The law and the file format both change

Section 115BBH, its rate, the TDS provisions of Section 194S, and the reporting
requirements around Virtual Digital Assets may be amended at any time. The
CoinDCX export format has already changed at least once. This software may
become silently wrong without any warning. Check that it reflects current law
before each use.

## What this software does not handle

The calculator reads only the **Instant Orders** and **Spot Orders** sheets of a
CoinDCX trade report. It does not know about anything else. In particular, it
does **not** handle:

- Airdrops, staking rewards, mining income, hard forks, or referral bonuses
- Gifts of virtual digital assets, given or received
- P2P trades, OTC deals, or crypto received as payment for goods or services
- Futures, margin, leverage, lending or liquidity provision
- Deposits, withdrawals, or transfers between exchanges and wallets
- Any activity on any exchange other than CoinDCX

Additional limitations you must understand:

- **Cost basis comes only from purchases present in the file.** If an asset you
  sold was bought before the export's date range, or acquired anywhere else, the
  calculator either reports an error or - if you supply a partial history -
  understates your cost and **overstates your taxable gain**.
- **FIFO only.** No other cost-basis method is offered.
- Per Section 115BBH, no expenditure other than cost of acquisition is deducted,
  and **no set-off or carry-forward of losses is computed**. Losses shown
  per-asset are informational.
- TDS figures are reported for reference only. Reconcile them against your Form
  26AS / AIS.

## Jurisdiction

Written with Indian income tax law in mind. It is not useful for, and makes no
attempt to comply with, the tax rules of any other country.

## No affiliation

This project is **not affiliated with, endorsed by, sponsored by, or connected
to CoinDCX or Neblio Technologies Private Limited** in any way.

"CoinDCX" is used solely to identify the trade report file format that this
software reads, which is nominative use. All trademarks, service marks and trade
names are the property of their respective owners.
```

- [ ] **Step 7: Commit**

```bash
git add DISCLAIMER.md crypto_pnl_calculator.py tests/test_disclaimer.py
git commit -m "Add disclaimer, printed on every run

Documents what the tool does not handle - airdrops, staking, transfers
between exchanges, missing purchase history - because an honest list of
limitations protects users better than broad boilerplate.

Printing it at runtime is deliberate: it is the only copy a user cannot
skip past. A test asserts it stays there."
```

---

### Task 3: Community and support documents

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `SUPPORT.md`
- Create: `CODE_OF_CONDUCT.md`

**Interfaces:**
- Consumes: `DISCLAIMER.md` from Task 2 (linked from `SUPPORT.md`).
- Produces: files that GitHub surfaces automatically in the issue and PR UI.

- [ ] **Step 1: Create `CONTRIBUTING.md`**

```markdown
# Contributing

Thanks for considering a contribution.

## Before you open an issue or PR

> **Never attach a real CoinDCX export, a generated report, or a screenshot of
> either.** Those files contain your name, email address, PAN, and your complete
> trading history. Once posted in a public issue they cannot be fully deleted.
>
> Reduce your problem to a few fabricated rows before sharing it.

## Setup

```bash
uv sync
source .venv/bin/activate
```

## Running the tests

```bash
uv run pytest
```

All tests must pass before you open a pull request. CI runs the same command.

## Writing tests

Tests must **never** read a real export from the repository root. Those files are
gitignored and absent in CI. Build the workbook you need inside `tmp_path`, or
construct a `DataFrame` directly and hand it to the parser — see
`tests/test_crypto_pnl_calculator.py` for both patterns.

## What makes a good pull request

- One change per pull request.
- A failing test first, then the fix. Tax software without a regression test for
  a bug is how the same bug comes back.
- If you change how a figure is computed, explain the tax reasoning in the commit
  message, ideally with a reference to the relevant section.
- Keep the parser tolerant of CoinDCX header variants and intolerant of rows it
  cannot read. Silently skipping a row understates cost basis and overstates
  someone's taxable gain.

## Licensing of contributions

By submitting a pull request you agree that your contribution is licensed under
the [Apache License 2.0](LICENSE), the same terms as the rest of the project.

## No obligation

This is a personal project maintained on a best-effort basis. The maintainer may
decline any contribution, for any reason, without detailed explanation. Please
do not take it personally.
```

- [ ] **Step 2: Create `SECURITY.md`**

```markdown
# Security Policy

## Reporting a vulnerability

Report privately through GitHub's
[Security Advisories](https://github.com/sanketdaru/india-crypto-tax-calculator/security/advisories/new)
form. Please do **not** open a public issue for a security problem.

Do not include a real export, report, or any personal data in your report.

## What to expect

This is a personal project maintained on a best-effort basis. There is **no
response time commitment and no SLA**. Reports are read and acted on when the
maintainer has time. If a fix is warranted it will be released as a normal
commit with credit to the reporter, unless you ask otherwise.

## Scope

The calculator runs entirely on your own machine. It opens no network
connections, requires no account or API key, and transmits nothing anywhere. The
realistic threat model is therefore narrow:

**In scope**

- Anything causing the tool to write, log or transmit your transaction data
  outside the output file you asked for
- Malicious content in a crafted `.xlsx` leading to code execution
- A dependency with a known vulnerability that this project actually reaches

**Out of scope**

- Incorrect P&L figures. Those are bugs — open a normal issue.
- Anything requiring an attacker to already have access to your machine.
```

- [ ] **Step 3: Create `SUPPORT.md`**

```markdown
# Support

## Before asking

- [README](README.md) — installation, usage, input file format, troubleshooting
- [DISCLAIMER](DISCLAIMER.md) — what this tool deliberately does not handle

Most reports turn out to be an unsupported transaction type or an export that
does not cover the full purchase history of an asset. Both are covered there.

## Bugs and feature requests

Open an [issue](https://github.com/sanketdaru/india-crypto-tax-calculator/issues).

> **Redact first.** Never paste a real export, a generated report, or a
> screenshot of either. They contain your name, email, PAN and full trading
> history, and a public issue is public forever. Reproduce with fabricated
> numbers instead.

## What support means here

This is a personal project maintained in spare time and offered free of charge.

- Best-effort only. **No SLA, no response time commitment.**
- No guarantee that any issue is ever fixed, or that any pull request is merged.
- No private or paid support channel.

## What this is not a channel for

**Tax questions.** How to treat a particular transaction, what you owe, what to
put in which ITR schedule, whether a set-off applies — all of these need a
qualified tax professional who can see your full circumstances. The maintainer
is not one and cannot answer them. See [DISCLAIMER.md](DISCLAIMER.md).
```

- [ ] **Step 4: Fetch Contributor Covenant 2.1**

```bash
curl -sSL https://www.contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md -o CODE_OF_CONDUCT.md
grep -c "Contributor Covenant" CODE_OF_CONDUCT.md
```

Expected: at least one match. If the file is empty or an HTML error page, stop and retry.

- [ ] **Step 5: Set the enforcement contact**

The template has a placeholder for a contact method. Point it at GitHub private reporting rather than an email address, per the constraint against publishing one.

```bash
python3 - <<'PY'
from pathlib import Path
p = Path('CODE_OF_CONDUCT.md')
text = p.read_text()
old = '[INSERT CONTACT METHOD]'
assert old in text, "placeholder not found; open CODE_OF_CONDUCT.md and set the contact manually"
new = ('GitHub\'s private reporting form at '
       'https://github.com/sanketdaru/india-crypto-tax-calculator/security/advisories/new')
p.write_text(text.replace(old, new))
print("contact set")
PY
```

- [ ] **Step 6: Verify no personal email leaked into any new file**

```bash
grep -rn "sankda1309\|@gmail\|@googlemail" CONTRIBUTING.md SECURITY.md SUPPORT.md CODE_OF_CONDUCT.md DISCLAIMER.md NOTICE || echo "clean: no personal email published"
```

Expected: `clean: no personal email published`.

- [ ] **Step 7: Commit**

```bash
git add CONTRIBUTING.md SECURITY.md SUPPORT.md CODE_OF_CONDUCT.md
git commit -m "Add contributing, security, support and conduct docs

Support docs state plainly that this is best-effort with no SLA, that
tax questions belong with a professional, and that a real export must
never be attached to an issue.

Security reports route through GitHub private advisories so no personal
email address is published."
```

---

### Task 4: GitHub templates and CI

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `SUPPORT.md` and `DISCLAIMER.md` from Tasks 2–3 (linked from `config.yml`).
- Produces: a CI workflow named `CI` whose badge Task 7 embeds in the README.

- [ ] **Step 1: Create `.github/ISSUE_TEMPLATE/bug_report.yml`**

The redaction checkbox is `required: true`. GitHub blocks submission until it is ticked. This is the single highest-value control in the whole release.

```yaml
name: Bug report
description: A wrong figure, a crash, or a parsing failure
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        ## Redact before you post

        **Never attach a real CoinDCX export, a generated report, or a screenshot
        of either.** They contain your name, email, PAN and complete trading
        history. A public issue is public forever and cannot be fully deleted.

        Reproduce the problem with fabricated numbers instead.

  - type: checkboxes
    id: redaction
    attributes:
      label: Personal data
      options:
        - label: I have removed all personal data from this report — name, email, PAN, transaction IDs, and real amounts.
          required: true

  - type: textarea
    id: what-happened
    attributes:
      label: What happened
      description: What did you expect, and what did you get instead?
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: Steps to reproduce
      description: Include the fabricated rows needed to trigger it, if relevant.
      placeholder: |
        1. Instant Orders row: BUY 0.001 BTC, gross 5000, fees 29.5
        2. Spot Orders row: SELL ...
        3. Run: python crypto_pnl_calculator.py transactions.xlsx
    validations:
      required: true

  - type: textarea
    id: output
    attributes:
      label: Console output
      description: Paste the error or warning. Redact any real figures.
      render: shell

  - type: input
    id: version
    attributes:
      label: Version
      description: "Output of: git rev-parse --short HEAD"
    validations:
      required: true

  - type: input
    id: python
    attributes:
      label: Python version
      description: "Output of: python --version"
    validations:
      required: true

  - type: checkboxes
    id: acknowledgements
    attributes:
      label: Before submitting
      options:
        - label: I have read DISCLAIMER.md and confirmed this is not one of the transaction types the tool deliberately does not handle.
          required: true
        - label: I understand this project is maintained on a best-effort basis with no SLA.
          required: true
```

- [ ] **Step 2: Create `.github/ISSUE_TEMPLATE/feature_request.yml`**

```yaml
name: Feature request
description: Suggest a capability or an improvement
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: The problem
      description: What are you unable to do today?
    validations:
      required: true

  - type: textarea
    id: proposal
    attributes:
      label: Proposed solution
    validations:
      required: true

  - type: textarea
    id: tax-basis
    attributes:
      label: Tax reasoning
      description: >
        If this changes how a figure is computed, cite the section or rule it
        follows. Requests that change tax treatment without a citation are
        unlikely to be accepted.

  - type: checkboxes
    id: acknowledgements
    attributes:
      label: Before submitting
      options:
        - label: I understand the maintainer may decline this without detailed explanation.
          required: true
```

- [ ] **Step 3: Create `.github/ISSUE_TEMPLATE/config.yml`**

```yaml
blank_issues_enabled: false
contact_links:
  - name: Tax questions
    url: https://github.com/sanketdaru/india-crypto-tax-calculator/blob/master/DISCLAIMER.md
    about: This project cannot answer tax questions. Please consult a qualified tax professional.
  - name: Usage help and support policy
    url: https://github.com/sanketdaru/india-crypto-tax-calculator/blob/master/SUPPORT.md
    about: Read this first — most reports are covered by the documented limitations.
  - name: Report a security vulnerability
    url: https://github.com/sanketdaru/india-crypto-tax-calculator/security/advisories/new
    about: Report privately. Do not open a public issue.
```

- [ ] **Step 4: Create `.github/PULL_REQUEST_TEMPLATE.md`**

```markdown
## What this changes

<!-- One or two sentences. -->

## Why

<!-- If this changes how a figure is computed, cite the tax rule it follows. -->

## Checklist

- [ ] `uv run pytest` passes locally
- [ ] A test covers the change, and it failed before the fix
- [ ] No real export, report, screenshot or personal data is included in this PR
- [ ] No test reads a gitignored spreadsheet from the repository root
- [ ] I agree my contribution is licensed under the Apache License 2.0
```

- [ ] **Step 5: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [master]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  test:
    name: Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.13

      - name: Install dependencies
        run: uv sync --all-groups

      - name: Run tests
        run: uv run pytest -v

      - name: Assert no spreadsheet is tracked
        run: |
          if git ls-files '*.xlsx' '*.xls' '*.xlsm' '*.csv' | grep .; then
            echo "::error::A spreadsheet is tracked in git. These files contain personal data."
            exit 1
          fi
          echo "No spreadsheet tracked."
```

The final step is a standing guard: it fails CI if anyone ever commits a real export.

- [ ] **Step 6: Verify the YAML parses**

```bash
uv run python -c "
import yaml, pathlib, sys
for p in sorted(pathlib.Path('.github').rglob('*.yml')):
    yaml.safe_load(p.read_text())
    print('ok', p)
" 2>/dev/null || python3 -c "
import pathlib
for p in sorted(pathlib.Path('.github').rglob('*.yml')):
    print('present', p)
"
```

Expected: every file listed. If `yaml` is unavailable the fallback just confirms the files exist; GitHub validates them on push either way.

- [ ] **Step 7: Commit**

```bash
git add .github
git commit -m "Add issue templates, PR template and CI

The bug report form makes the redaction confirmation a required
checkbox. The most likely privacy incident for this project is a user
pasting their own PAN into a public issue, not a git leak.

CI runs the test suite and fails if any spreadsheet is ever tracked."
```

---

### Task 5: Landing page

**Files:**
- Create: `site/index.html`
- Create: `site/robots.txt`
- Create: `site/sitemap.xml`
- Test: `tests/test_site.py`

**Interfaces:**
- Consumes: the canonical URL from Task 1.
- Produces: `site/` as the Pages publish directory, consumed by Task 6.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_site.py`. Uses only the standard library plus pytest — no HTML parsing dependency.

```python
"""The landing page carries the SEO payload; these assert it stays intact."""

import json
import re
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1] / 'site'
INDEX = SITE / 'index.html'
CANONICAL = 'https://sanketdaru.github.io/india-crypto-tax-calculator/'


@pytest.fixture(scope='module')
def html() -> str:
    return INDEX.read_text(encoding='utf-8')


def _json_ld_blocks(html: str):
    pattern = re.compile(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        re.DOTALL | re.IGNORECASE,
    )
    return [json.loads(m.group(1)) for m in pattern.finditer(html)]


def test_site_files_exist():
    for name in ('index.html', 'robots.txt', 'sitemap.xml'):
        assert (SITE / name).is_file(), f'missing site/{name}'


def test_title_is_present_and_reasonably_sized(html):
    match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    assert match, 'no <title>'
    title = match.group(1).strip()
    assert 'Crypto Tax' in title
    assert len(title) <= 65, f'title too long for search results: {len(title)}'


def test_meta_description_is_present_and_within_snippet_length(html):
    match = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.DOTALL
    )
    assert match, 'no meta description'
    description = match.group(1).strip()
    assert 50 <= len(description) <= 160, f'description length {len(description)}'


def test_canonical_url_is_correct(html):
    assert f'<link rel="canonical" href="{CANONICAL}"' in html


def test_open_graph_and_twitter_cards_present(html):
    for tag in ('og:title', 'og:description', 'og:url', 'og:type', 'twitter:card'):
        assert tag in html, f'missing {tag}'


def test_json_ld_blocks_are_valid_json(html):
    blocks = _json_ld_blocks(html)
    assert len(blocks) >= 2, 'expected SoftwareApplication and FAQPage blocks'
    for block in blocks:
        assert block.get('@context') == 'https://schema.org'
        assert '@type' in block


def test_software_application_schema(html):
    app = next(b for b in _json_ld_blocks(html) if b['@type'] == 'SoftwareApplication')
    assert app['applicationCategory'] == 'FinanceApplication'
    assert app['offers']['price'] == '0'
    assert app['license'].endswith('Apache-2.0')


def test_faq_schema_answers_are_not_empty(html):
    faq = next(b for b in _json_ld_blocks(html) if b['@type'] == 'FAQPage')
    assert len(faq['mainEntity']) >= 6, 'FAQ schema is the main SEO lever; keep it substantial'
    for entry in faq['mainEntity']:
        assert entry['@type'] == 'Question'
        assert entry['name'].strip()
        assert len(entry['acceptedAnswer']['text'].strip()) > 40


def test_page_is_self_contained(html):
    """No CDN, no external fonts, no remote images, no analytics."""
    remote = re.findall(r'(?:src|href)=["\'](https?://[^"\']+)["\']', html)
    allowed_prefixes = (CANONICAL, 'https://github.com/sanketdaru/', 'https://schema.org')
    for url in remote:
        assert url.startswith(allowed_prefixes), f'external asset or link not allowed: {url}'


def test_disclaimer_appears_above_the_fold(html):
    body = html[html.index('<body'):]
    assert 'NOT TAX ADVICE' in body.upper()
    # It must come before the feature copy, not be buried in a footer.
    assert body.upper().index('NOT TAX ADVICE') < body.index('id="install"')


def test_sitemap_lists_the_canonical_url():
    sitemap = (SITE / 'sitemap.xml').read_text(encoding='utf-8')
    assert CANONICAL in sitemap


def test_robots_allows_crawling_and_points_to_sitemap():
    robots = (SITE / 'robots.txt').read_text(encoding='utf-8')
    assert 'Disallow:\n' in robots or 'Disallow: \n' in robots or 'Allow: /' in robots
    assert 'sitemap.xml' in robots.lower()
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run pytest tests/test_site.py -v
```

Expected: every test fails — `site/index.html` does not exist.

- [ ] **Step 3: Create `site/index.html`**

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>India Crypto Tax Calculator — FIFO P&amp;L for Section 115BBH</title>
<meta name="description" content="Free open-source tool that turns CoinDCX exports into FIFO P&amp;L reports for Indian crypto tax (Section 115BBH). Runs locally — your data stays private.">
<link rel="canonical" href="https://sanketdaru.github.io/india-crypto-tax-calculator/">
<meta name="theme-color" content="#0d1117" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta property="og:type" content="website">
<meta property="og:title" content="India Crypto Tax Calculator — FIFO P&amp;L for Section 115BBH">
<meta property="og:description" content="Turn CoinDCX exports into FIFO profit and loss reports for Indian crypto tax. Open source, runs entirely on your own machine.">
<meta property="og:url" content="https://sanketdaru.github.io/india-crypto-tax-calculator/">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="India Crypto Tax Calculator">
<meta name="twitter:description" content="FIFO P&amp;L reports for Indian crypto tax under Section 115BBH. Open source, runs locally.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ctext y='26' font-size='26'%3E%E2%82%B9%3C/text%3E%3C/svg%3E">
<style>
:root{--bg:#fff;--fg:#1a1a1a;--muted:#5c6370;--line:#e3e6ea;--card:#f6f8fa;--accent:#0b5ed7;--warnbg:#fff4e5;--warnfg:#7a4100;--warnline:#f0b37e}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--line:#30363d;--card:#161b22;--accent:#6cb0ff;--warnbg:#2b1d0e;--warnfg:#f0c68a;--warnline:#7a5320}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
main{max-width:52rem;margin:0 auto;padding:0 1.25rem 5rem}
h1{font-size:2.25rem;line-height:1.2;margin:0 0 .5rem}
h2{font-size:1.5rem;margin:3rem 0 .75rem;padding-top:.5rem}
h3{font-size:1.05rem;margin:1.75rem 0 .35rem}
p{margin:0 0 1rem}
a{color:var(--accent)}
header{border-bottom:1px solid var(--line);padding:4rem 0 3rem;margin-bottom:0}
.tagline{font-size:1.15rem;color:var(--muted);margin-bottom:1.75rem}
.cta{display:inline-block;padding:.6rem 1.15rem;border-radius:6px;text-decoration:none;font-weight:600;margin:0 .5rem .5rem 0}
.cta-primary{background:var(--accent);color:#fff}
.cta-secondary{border:1px solid var(--line);color:var(--fg)}
.warn{background:var(--warnbg);color:var(--warnfg);border:1px solid var(--warnline);border-radius:8px;padding:1.1rem 1.25rem;margin:2rem 0}
.warn strong{display:block;margin-bottom:.35rem;letter-spacing:.04em}
pre{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:1rem;overflow-x:auto}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em}
p code,li code{background:var(--card);padding:.12em .35em;border-radius:4px}
ul{padding-left:1.25rem}
li{margin-bottom:.4rem}
.grid{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:1.1rem}
.card h3{margin-top:0}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.86rem;min-width:34rem}
th,td{text-align:right;padding:.45rem .7rem;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{font-weight:600;color:var(--muted)}
details{border-bottom:1px solid var(--line);padding:.85rem 0}
summary{cursor:pointer;font-weight:600}
details p{margin:.6rem 0 0;color:var(--muted)}
footer{border-top:1px solid var(--line);margin-top:4rem;padding-top:1.5rem;color:var(--muted);font-size:.9rem}
.sample-note{color:var(--muted);font-size:.85rem}
</style>
</head>
<body>
<main>

<header>
  <h1>India Crypto Tax Calculator</h1>
  <p class="tagline">Turn a CoinDCX trade export into a FIFO profit-and-loss report for Indian Virtual Digital Asset taxation under Section 115BBH.</p>
  <a class="cta cta-primary" href="#install">Get started</a>
  <a class="cta cta-secondary" href="https://github.com/sanketdaru/india-crypto-tax-calculator">View on GitHub</a>
</header>

<div class="warn">
  <strong>NOT TAX ADVICE</strong>
  This is free software provided with no warranty, written by someone who is not a tax professional. Its output is a starting point for a conversation with a qualified professional, not a finished computation. You alone are responsible for what you file. <a href="https://github.com/sanketdaru/india-crypto-tax-calculator/blob/master/DISCLAIMER.md">Read the full disclaimer and the list of what it does not handle</a>.
</div>

<h2>What it does</h2>
<p>Indian tax on Virtual Digital Assets is charged at a flat 30% on gains under Section 115BBH of the Income Tax Act, 1961, with no deduction other than cost of acquisition and no set-off of losses. Working that out by hand across a year of trades is tedious and easy to get wrong.</p>
<p>This tool reads the Excel trade report you download from CoinDCX and produces a multi-sheet report: a full transaction log, a per-asset summary, and headline totals.</p>

<div class="grid">
  <div class="card">
    <h3>FIFO cost basis</h3>
    <p>Oldest holdings are disposed first, lot by lot, with the cost basis of each disposal tracked back to the purchase that funded it.</p>
  </div>
  <div class="card">
    <h3>USDT pairs handled properly</h3>
    <p>Buying ETH with USDT is a disposal of USDT and a separate acquisition of ETH. Both legs are recorded, and the USDT gain is not silently lost.</p>
  </div>
  <div class="card">
    <h3>Gross figures, per the section</h3>
    <p>Fees are tracked for reference but excluded from cost basis and proceeds, as Section 115BBH requires. TDS is reported separately.</p>
  </div>
  <div class="card">
    <h3>Fails loudly</h3>
    <p>A row it cannot read stops the run and names the sheet and row. It will not quietly drop a purchase and overstate your gain.</p>
  </div>
</div>

<h2>Your data never leaves your machine</h2>
<p>Every commercial crypto tax service asks you to upload a file containing your name, your PAN and your complete trading history to a server you do not control.</p>
<p>This tool does not. It is a Python script that runs on your own computer. It opens no network connections, has no account, no API key, no telemetry and no analytics. The input file is read from your disk and the report is written back to your disk. Nothing is transmitted anywhere, and you can read the source to confirm that.</p>

<h2 id="install">Install and run</h2>
<p>You need <a href="https://github.com/sanketdaru/india-crypto-tax-calculator#requirements">uv</a> and Python 3.13.</p>
<pre><code>git clone https://github.com/sanketdaru/india-crypto-tax-calculator.git
cd india-crypto-tax-calculator
uv sync
source .venv/bin/activate</code></pre>
<p>Download your trade report from CoinDCX, save it as <code>crypto_transactions.xlsx</code> in the project folder, then run:</p>
<pre><code>python crypto_pnl_calculator.py</code></pre>
<p>Or name the files explicitly:</p>
<pre><code>python crypto_pnl_calculator.py my_trades.xlsx my_report.xlsx</code></pre>

<h2>What the output looks like</h2>
<p>The per-asset summary sheet, with the transaction log and headline totals alongside it:</p>
<div class="scroll">
<table>
<thead><tr><th>Crypto</th><th>Qty bought</th><th>Qty sold</th><th>Purchase cost</th><th>Cost of sold</th><th>Proceeds</th><th>P&amp;L</th><th>Holdings</th></tr></thead>
<tbody>
<tr><td>USDT</td><td>REDACTED</td><td>REDACTED</td><td>REDACTED</td><td>REDACTED</td><td>REDACTED</td><td>REDACTED</td><td>REDACTED</td></tr>
<tr><td>BTC</td><td>0.0046</td><td>0.0000</td><td>REDACTED</td><td>0.00</td><td>0.00</td><td>0.00</td><td>0.0046</td></tr>
<tr><td>ETH</td><td>REDACTED</td><td>0.0000</td><td>REDACTED</td><td>0.00</td><td>0.00</td><td>0.00</td><td>REDACTED</td></tr>
<tr><td>SOL</td><td>REDACTED</td><td>0.0000</td><td>REDACTED</td><td>0.00</td><td>0.00</td><td>0.00</td><td>REDACTED</td></tr>
</tbody>
</table>
</div>
<p class="sample-note">Sample data, shown for illustration only.</p>

<h2>Frequently asked questions</h2>

<details>
<summary>Is this tax advice?</summary>
<p>No. It is free software with no warranty, written by someone who is not a chartered accountant or a tax practitioner. Using it creates no advisor-client relationship. Verify every figure with a qualified professional before you file, because you alone carry the consequences of what you file.</p>
</details>

<details>
<summary>What is Section 115BBH?</summary>
<p>Section 115BBH of the Income Tax Act, 1961 taxes income from the transfer of Virtual Digital Assets at a flat 30%, plus applicable surcharge and cess. No deduction is allowed other than the cost of acquisition, and losses from VDAs cannot be set off against any other income or carried forward. A separate 1% TDS applies under Section 194S.</p>
</details>

<details>
<summary>What is FIFO and why does it matter?</summary>
<p>First In, First Out means that when you sell part of a holding, the oldest units you bought are treated as the ones sold. Since those usually have a different purchase price from your most recent buys, the method you choose changes your cost basis and therefore your taxable gain. This tool uses FIFO throughout and offers no alternative method.</p>
</details>

<details>
<summary>How are USDT trading pairs handled?</summary>
<p>They are correctly treated as two taxable events. Buying ETH with USDT is a disposal of USDT, which realises a gain or loss on that USDT, and separately an acquisition of ETH at the INR value of the trade. Tools that ignore the first leg understate your taxable income.</p>
</details>

<details>
<summary>Is my data uploaded anywhere?</summary>
<p>No. The tool runs entirely on your own machine. It opens no network connections, requires no account or API key, and sends no telemetry. Your export is read from disk and the report is written back to disk. The source is open, so you can verify this yourself.</p>
</details>

<details>
<summary>Which exchanges are supported?</summary>
<p>Only CoinDCX trade report exports, specifically their Instant Orders and Spot Orders sheets. This project is not affiliated with or endorsed by CoinDCX. Support for other exchanges would require a parser for each one's export format.</p>
</details>

<details>
<summary>What does it not handle?</summary>
<p>Airdrops, staking rewards, mining income, hard forks, gifts, P2P trades, futures, margin and lending are all out of scope, as are deposits, withdrawals and transfers between exchanges or wallets. Cost basis is derived only from purchases present in your file, so an incomplete export will overstate your gain. The full list is in the disclaimer.</p>
</details>

<details>
<summary>Is it free?</summary>
<p>Yes. It is open source under the Apache License 2.0, free to use, modify and redistribute, including commercially. There is no paid tier and no support contract.</p>
</details>

<footer>
<p>Open source under the <a href="https://github.com/sanketdaru/india-crypto-tax-calculator/blob/master/LICENSE">Apache License 2.0</a> · <a href="https://github.com/sanketdaru/india-crypto-tax-calculator">Source</a> · <a href="https://github.com/sanketdaru/india-crypto-tax-calculator/blob/master/DISCLAIMER.md">Disclaimer</a> · <a href="https://github.com/sanketdaru/india-crypto-tax-calculator/issues">Issues</a></p>
<p>Not affiliated with, endorsed by or sponsored by CoinDCX or Neblio Technologies Private Limited. All trademarks belong to their respective owners.</p>
</footer>

</main>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "India Crypto Tax Calculator",
  "description": "Open source tool that turns CoinDCX trade exports into FIFO profit and loss reports for Indian Virtual Digital Asset taxation under Section 115BBH.",
  "applicationCategory": "FinanceApplication",
  "operatingSystem": "Windows, macOS, Linux",
  "url": "https://sanketdaru.github.io/india-crypto-tax-calculator/",
  "codeRepository": "https://github.com/sanketdaru/india-crypto-tax-calculator",
  "programmingLanguage": "Python",
  "license": "https://spdx.org/licenses/Apache-2.0",
  "isAccessibleForFree": true,
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "INR"
  }
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Is this tax advice?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. It is free software with no warranty, written by someone who is not a chartered accountant or a tax practitioner. Using it creates no advisor-client relationship. Verify every figure with a qualified professional before you file, because you alone carry the consequences of what you file."
      }
    },
    {
      "@type": "Question",
      "name": "What is Section 115BBH?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Section 115BBH of the Income Tax Act, 1961 taxes income from the transfer of Virtual Digital Assets at a flat 30 percent, plus applicable surcharge and cess. No deduction is allowed other than the cost of acquisition, and losses from VDAs cannot be set off against any other income or carried forward. A separate 1 percent TDS applies under Section 194S."
      }
    },
    {
      "@type": "Question",
      "name": "What is FIFO and why does it matter for crypto tax?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "First In, First Out means that when you sell part of a holding, the oldest units you bought are treated as the ones sold. Since those usually have a different purchase price from your most recent buys, the method you choose changes your cost basis and therefore your taxable gain. This tool uses FIFO throughout and offers no alternative method."
      }
    },
    {
      "@type": "Question",
      "name": "How are USDT trading pairs handled?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "They are correctly treated as two taxable events. Buying ETH with USDT is a disposal of USDT, which realises a gain or loss on that USDT, and separately an acquisition of ETH at the INR value of the trade. Tools that ignore the first leg understate your taxable income."
      }
    },
    {
      "@type": "Question",
      "name": "Is my crypto transaction data uploaded anywhere?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. The tool runs entirely on your own machine. It opens no network connections, requires no account or API key, and sends no telemetry. Your export is read from disk and the report is written back to disk. The source is open, so you can verify this yourself."
      }
    },
    {
      "@type": "Question",
      "name": "Which exchanges are supported?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Only CoinDCX trade report exports, specifically their Instant Orders and Spot Orders sheets. This project is not affiliated with or endorsed by CoinDCX. Support for other exchanges would require a parser for each one's export format."
      }
    },
    {
      "@type": "Question",
      "name": "What transactions does this calculator not handle?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Airdrops, staking rewards, mining income, hard forks, gifts, P2P trades, futures, margin and lending are all out of scope, as are deposits, withdrawals and transfers between exchanges or wallets. Cost basis is derived only from purchases present in your file, so an incomplete export will overstate your gain."
      }
    },
    {
      "@type": "Question",
      "name": "Is this crypto tax calculator free?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. It is open source under the Apache License 2.0, free to use, modify and redistribute, including commercially. There is no paid tier and no support contract."
      }
    }
  ]
}
</script>

</body>
</html>
```

- [ ] **Step 4: Create `site/robots.txt`**

```text
User-agent: *
Allow: /

Sitemap: https://sanketdaru.github.io/india-crypto-tax-calculator/sitemap.xml
```

- [ ] **Step 5: Create `site/sitemap.xml`**

`lastmod` is a fixed date, not generated — it should change only when the page's content actually changes.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://sanketdaru.github.io/india-crypto-tax-calculator/</loc>
    <lastmod>2026-07-25</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
```

- [ ] **Step 6: Run the tests to verify they pass**

```bash
uv run pytest tests/test_site.py -v
```

Expected: all pass. If `test_page_is_self_contained` fails, an external URL crept in — either remove it or add it to `allowed_prefixes` only if it is a plain hyperlink rather than a loaded asset.

- [ ] **Step 7: Run the whole suite**

```bash
uv run pytest -q
```

Expected: 43 passed (24 + 7 + 12).

- [ ] **Step 8: Commit**

```bash
git add site tests/test_site.py
git commit -m "Add landing page with structured data

Single self-contained page: no CDN, no fonts, no analytics. Carries
SoftwareApplication and FAQPage JSON-LD; the FAQ schema is the main
lever for ranking on questions people actually search.

Leads with the disclaimer above the fold and with the fact that the
tool runs locally, which is the real differentiator against hosted
crypto tax services.

Tests assert the schema stays valid and that no external asset creeps
in."
```

---

### Task 6: Pages deployment and repository metadata

**Files:**
- Create: `.github/workflows/pages.yml`

**Interfaces:**
- Consumes: `site/` from Task 5, CI workflow name from Task 4.
- Produces: a live site at the canonical URL.

- [ ] **Step 1: Create `.github/workflows/pages.yml`**

```yaml
name: Deploy site

on:
  push:
    branches: [master]
    paths:
      - 'site/**'
      - '.github/workflows/pages.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Commit and push the branch**

```bash
git add .github/workflows/pages.yml
git commit -m "Add GitHub Pages deployment workflow

Publishes site/ via Actions rather than the /docs folder source, so the
published site stays separate from docs/ which holds internal specs."
git push -u origin chore/open-source-release
```

- [ ] **Step 3: Merge to master and push**

Pages and CI only run from `master`, so the workflows must land there before anything deploys.

```bash
git checkout master
git merge --ff-only chore/open-source-release
git push origin master
```

- [ ] **Step 4: Set the Pages source to GitHub Actions**

```bash
gh api -X POST repos/sanketdaru/india-crypto-tax-calculator/pages \
  -f build_type=workflow 2>&1 || echo "API call failed - set it manually in Settings > Pages > Source: GitHub Actions"
```

If this returns an error, it is a manual step for the user. Record it and continue.

- [ ] **Step 5: Verify the deployment**

```bash
gh run list --workflow="Deploy site" --limit 3
gh api repos/sanketdaru/india-crypto-tax-calculator/pages --jq '.html_url, .status' 2>&1
```

Expected: a completed run and a live URL. First deployment can take a couple of minutes.

- [ ] **Step 6: Set repository description, homepage and topics**

```bash
gh repo edit sanketdaru/india-crypto-tax-calculator \
  --description "Free open-source crypto tax calculator for India. Turns CoinDCX trade exports into FIFO profit and loss reports for Virtual Digital Asset taxation under Section 115BBH. Runs locally." \
  --homepage "https://sanketdaru.github.io/india-crypto-tax-calculator/" \
  --add-topic crypto-tax \
  --add-topic crypto-tax-india \
  --add-topic india \
  --add-topic income-tax \
  --add-topic section-115bbh \
  --add-topic vda \
  --add-topic fifo \
  --add-topic pnl-calculator \
  --add-topic capital-gains \
  --add-topic itr \
  --add-topic cryptocurrency \
  --add-topic coindcx \
  --add-topic tax-calculator \
  --add-topic python
```

- [ ] **Step 7: Enable private vulnerability reporting**

```bash
gh api -X PUT repos/sanketdaru/india-crypto-tax-calculator/private-vulnerability-reporting 2>&1 \
  || echo "API call failed - enable manually in Settings > Code security > Private vulnerability reporting"
```

`SECURITY.md` links to the private advisory form, so this must be on or that link 404s.

- [ ] **Step 8: Verify the metadata took**

```bash
gh repo view sanketdaru/india-crypto-tax-calculator \
  --json name,description,homepageUrl,repositoryTopics,licenseInfo
```

Expected: description and homepage set, topics listed, and `licenseInfo` now reporting Apache 2.0 since `LICENSE` is on `master`.

---

### Task 7: README rewrite

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: everything from Tasks 1–6 — badge URLs, site URL, and the document filenames it links to.
- Produces: the repository's front door.

- [ ] **Step 1: Replace everything above the `## Requirements` heading**

Keep the existing Requirements, Usage, Input File Format, Output Reports, Key Tax Rules, Example Scenarios, Warnings, Troubleshooting and Technical Notes sections exactly as they are. Replace only the title, tagline, and Features block at the top, and delete the old `## Disclaimer` section at the very bottom since the callout and `DISCLAIMER.md` now cover it.

```markdown
# India Crypto Tax Calculator

**Turn a CoinDCX trade export into a FIFO profit-and-loss report for Indian Virtual Digital Asset taxation under Section 115BBH.**

[![CI](https://github.com/sanketdaru/india-crypto-tax-calculator/actions/workflows/ci.yml/badge.svg)](https://github.com/sanketdaru/india-crypto-tax-calculator/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)

📖 **[Website and FAQ](https://sanketdaru.github.io/india-crypto-tax-calculator/)**

> ## ⚠️ NOT TAX ADVICE
>
> This is free software provided **with no warranty**, written by someone who is
> **not a tax professional**. Its output is a starting point for a conversation
> with a qualified professional, not a finished computation. **You alone are
> responsible for what you file.**
>
> **[Read the full disclaimer and the list of what this tool does not
> handle](DISCLAIMER.md)** before using any of these numbers.

Indian tax on Virtual Digital Assets is charged at a flat 30% on gains under
Section 115BBH of the Income Tax Act, 1961, with no deduction other than cost of
acquisition and no set-off of losses. This script reads the Excel trade report
you download from CoinDCX and computes that for you.

**Your data never leaves your machine.** No account, no API key, no upload, no
telemetry. It reads a file from your disk and writes a report back to your disk.

## Features

- **FIFO inventory accounting** — oldest holdings disposed first, cost basis
  tracked lot by lot
- **USDT pair transformation** — a USDT-quoted trade is two taxable events, and
  both are recorded
  - `ETHUSDT BUY` → SELL USDT (P&L event) + BUY ETH
  - `ETHUSDT SELL` → SELL ETH (P&L event) + BUY USDT
- **Section 115BBH compliance** — fees excluded from cost basis and proceeds;
  TDS tracked separately for reference
- **Header variant tolerance** — accepts the different column names CoinDCX has
  shipped across export versions, and every pair style (`BTCUSDT`, `BTC-USDT`,
  `BTC/USDT`)
- **Fail-loud parsing** — an unreadable row aborts the run instead of being
  silently dropped, because a dropped purchase understates cost basis and
  overstates your taxable gain
- **Multi-sheet Excel output** — transaction log, per-asset summary, headline
  totals
- **Indian financial year support** — April to March, detected automatically

## Contents

- [Requirements](#requirements) · [Usage](#usage) · [Input File Format](#input-file-format)
- [Output Reports](#output-reports) · [Key Tax Rules](#key-tax-rules-section-115bbh)
- [Troubleshooting](#troubleshooting) · [Technical Notes](#technical-notes)
- [Disclaimer](DISCLAIMER.md) · [Contributing](CONTRIBUTING.md) · [Support](SUPPORT.md) · [Security](SECURITY.md)

## Not affiliated with CoinDCX

This project is not affiliated with, endorsed by or sponsored by CoinDCX or
Neblio Technologies Private Limited. "CoinDCX" identifies the trade report file
format this software reads. All trademarks belong to their respective owners.
```

- [ ] **Step 2: Verify every relative link resolves**

```bash
python3 - <<'PY'
import re, pathlib
text = pathlib.Path('README.md').read_text()
missing = [t for t in re.findall(r']\((?!https?://|#)([^)]+)\)', text)
           if not pathlib.Path(t.split('#')[0]).exists()]
print("broken links:", missing or "none")
PY
```

Expected: `broken links: none`.

- [ ] **Step 3: Confirm the tests still pass**

```bash
uv run pytest -q
```

Expected: 43 passed.

- [ ] **Step 4: Commit and push**

```bash
git add README.md
git commit -m "Rewrite README front matter for discoverability

Leads with what the tool is, who it is for and the disclaimer, then
with the fact that it runs locally. Badges, keywords and a link to the
site. Existing usage and troubleshooting sections are unchanged."
git push origin master
```

- [ ] **Step 5: Confirm CI is green and the site is live**

```bash
gh run list --limit 5
curl -sSI https://sanketdaru.github.io/india-crypto-tax-calculator/ | head -n 1
```

Expected: CI and Deploy site both `completed / success`, and `HTTP/2 200` from the site.

---

## Manual steps to hand back to the user

Report these explicitly at the end. None can be fully automated.

1. **Google Search Console** — go to <https://search.google.com/search-console>, add
   `https://sanketdaru.github.io/india-crypto-tax-calculator/` as a URL-prefix property,
   verify via the HTML tag method (paste the tag into `site/index.html` `<head>` and
   redeploy), then submit `sitemap.xml`. Without this, indexing takes far longer.
2. **Bing Webmaster Tools** — optional; it accepts a Search Console import.
3. **Settings → Pages → Source** — only if the API call in Task 6 Step 4 failed.
4. **Settings → Code security → Private vulnerability reporting** — only if the API call in
   Task 6 Step 7 failed. `SECURITY.md` links to that form, so it must be enabled.
5. **Consider a legal review** by a qualified professional if meaningful usage develops. This
   release is standard open-source boilerplate, not legal advice.
6. **Optional: a dedicated contact alias.** The Code of Conduct currently routes enforcement
   through GitHub private reporting to avoid publishing a personal address. If a real
   community forms, a role address is better.

---

## Self-Review

**Spec coverage**

| Spec section | Task |
|---|---|
| Apache 2.0 `LICENSE`, `NOTICE` | 1 |
| `DISCLAIMER.md` incl. limitations, non-affiliation, jurisdiction | 2 |
| Disclaimer restated in README, site banner, runtime | 2 (runtime), 5 (site), 7 (README) |
| `CONTRIBUTING`, `SECURITY`, `SUPPORT`, `CODE_OF_CONDUCT` | 3 |
| Issue forms with required redaction checkbox, PR template, CI | 4 |
| `site/index.html` with OG/Twitter/JSON-LD, robots, sitemap | 5 |
| "Data never leaves your machine" as its own section | 5, 7 |
| Pages via Actions from `site/` | 6 |
| Repo description, homepage, topics | 6 |
| Rename away from the trademark | 1 |
| README SEO rewrite | 7 |
| Testing: pytest green, JSON-LD valid, links resolve, runtime disclaimer asserted | 2, 5, 7 |

No gaps.

**Placeholder scan** — no TBD/TODO. Every file's full content is inline except `LICENSE` and
`CODE_OF_CONDUCT.md`, which are fetched verbatim from their canonical sources with
verification steps, which is more correct than transcribing them.

**Type consistency** — `DISCLAIMER` and `print_disclaimer()` are defined in Task 2 Step 3 and
used with those exact names in Task 2 Steps 1 and 4. The canonical URL, repo slug and
`Copyright 2026 Sanket Daru` are identical everywhere they appear. Test counts accumulate
consistently: 24 → 31 (7 new in Task 2, of which 5 come from one parametrized test) → 43
(12 new in Task 5).
