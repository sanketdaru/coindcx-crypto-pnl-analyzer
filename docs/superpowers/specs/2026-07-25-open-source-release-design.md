# Open Source Release: Legal, Support and Discoverability

**Date:** 2026-07-25
**Status:** Approved
**Repo:** `sanketdaru/coindcx-crypto-pnl-analyzer` → renamed to `sanketdaru/india-crypto-tax-calculator`

## Problem

The repository is already public but has no license, which under default copyright means
nobody may legally use, copy or modify it. The project computes figures people put on an
Indian income tax return, so shipping it without an explicit liability posture is a real
exposure. It is also undiscoverable: no description, no topics, no website, and a README
written for someone who already found the repo.

Three goals, in priority order:

1. **Limit the author's legal liability.** The author is not a tax professional. Users may
   file incorrect returns based on this tool's output and suffer penalties.
2. **Make the project legally usable** by others under a clear, OSI-approved license.
3. **Make it findable** by Indians searching for a way to compute crypto taxes.

## Non-Goals

- Legal review by a qualified lawyer. This spec produces standard open-source boilerplate.
  It is not legal advice and does not substitute for professional review.
- Multi-page documentation site. One landing page.
- Publishing to PyPI.
- Supporting exchanges other than CoinDCX.
- Any change to P&L calculation logic.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| License | Apache 2.0 | §7 Disclaimer of Warranty and §8 Limitation of Liability are full legal prose, unlike MIT's single paragraph. Express patent grant. Same permissive freedoms. |
| Repo name | `india-crypto-tax-calculator` | Removes the CoinDCX trademark from branding. Matches the highest-volume search phrase. |
| Trademark in prose | Retained, factual only | The tool parses CoinDCX exports; saying so is nominative fair use and is required for users to know what it does. Paired with an explicit non-affiliation notice. |
| Web presence | Single landing page on GitHub Pages | A README alone rarely ranks. One page is enough surface area for a single-script tool. |
| Maintainer posture | Low-touch | Issues open, no SLA, best-effort. Stated support expectations are themselves part of the liability posture. |
| Security contact | GitHub private advisories | Avoids publishing a personal email address. |
| Pages deployment | GitHub Actions from `site/` | Keeps the published site separate from `docs/`, which holds internal specs. |

## Design

### 1. Legal package

**`LICENSE`** — Apache License 2.0, verbatim. Copyright line: `Copyright 2026 Sanket Daru`.

**`NOTICE`** — Apache attribution convention. Project name, copyright, one-line pointer to
`DISCLAIMER.md`.

**`DISCLAIMER.md`** — the substantive document. Sections:

- **Not professional advice.** Not tax, legal, accounting or financial advice. The author is
  not a chartered accountant, tax practitioner or lawyer. No advisor-client relationship is
  created by using this software.
- **Verify before filing.** Output is a starting point. Every figure must be independently
  verified with a qualified tax professional before it is used in a return.
- **You are responsible.** The user alone is responsible for the accuracy and completeness
  of anything they file, and for any tax, interest, penalty or prosecution arising from it.
- **No warranty.** Restates Apache §7/§8 in plain language and links to `LICENSE`.
- **Law and formats change.** Section 115BBH, its rates, TDS rules and CoinDCX's export
  format may change at any time. The software may silently become wrong.
- **Known limitations**, stated honestly:
  - Handles only what is in the export: Instant Orders and Spot Orders.
  - Does not handle airdrops, staking, mining, forks, gifts, P2P trades, futures, margin,
    lending, or crypto received as payment.
  - Does not handle deposits/withdrawals or transfers between exchanges or wallets. Cost
    basis is derived solely from purchases present in the file.
  - Assumes the export covers the user's complete trading history for every asset sold. A
    missing earlier purchase produces an overstated gain.
  - FIFO only. No other cost-basis method.
  - Per Section 115BBH, no loss set-off or carry-forward is computed, and no deduction other
    than cost of acquisition is applied.
- **No affiliation.** Not affiliated with, endorsed by, sponsored by or connected to CoinDCX
  or Neblio Technologies Private Limited. "CoinDCX" is used only to describe the file format
  the software reads. All trademarks belong to their respective owners.
- **Jurisdiction.** Written with Indian income tax law in mind and useful nowhere else.

**Restatement in three places people actually look:**

1. Callout block at the top of `README.md`.
2. Banner above the fold on the landing page.
3. Printed by `crypto_pnl_calculator.py` on every run, before output.

The runtime notice is deliberate: it is the only one a user cannot skip.

### 2. Community and support

| File | Contents |
|---|---|
| `CONTRIBUTING.md` | Setup (`uv sync`), run tests (`uv run pytest`), PR expectations. Contributions licensed under Apache 2.0. **Never attach a real CoinDCX export or personal data to an issue or PR.** Maintainer may decline anything without explanation. |
| `SECURITY.md` | Report privately via GitHub Security Advisories. No email published. Best-effort response, explicitly no SLA. Scope note: the tool runs locally and transmits nothing. |
| `SUPPORT.md` | Best-effort only, no SLA, no guarantee any issue is fixed. Not a channel for tax questions — see a professional. Redaction warning repeated. |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1. Enforcement channel is GitHub private reporting rather than an email address. |

**`.github/` contents:**

- `ISSUE_TEMPLATE/bug_report.yml` — structured form. Includes a **required** checkbox
  confirming all personal data (name, email, PAN, transaction amounts, transaction IDs) has
  been removed from the report. This is the single highest-value control here: the most
  likely privacy incident is a user pasting their own tax export into a public issue.
- `ISSUE_TEMPLATE/feature_request.yml`
- `ISSUE_TEMPLATE/config.yml` — routes tax questions and usage questions away from the issue
  tracker.
- `PULL_REQUEST_TEMPLATE.md` — checklist: tests pass, no personal data, Apache 2.0 consent.
- `workflows/ci.yml` — `uv sync` + `uv run pytest` on push and PR, Python 3.13. A visible
  passing badge is a genuine trust signal for a tool that touches tax filings.
- `workflows/pages.yml` — build and deploy `site/` to GitHub Pages.

### 3. Landing page and SEO

**`site/index.html`** — self-contained. No CDN, no external fonts, no analytics. Inline CSS
and inline SVG favicon. Renders correctly in light and dark via `prefers-color-scheme`.

Head: `<title>`, meta description, canonical URL, Open Graph tags, Twitter card, theme-color.

Structured data, two JSON-LD blocks:

- `SoftwareApplication` — name, description, `applicationCategory: FinanceApplication`,
  `operatingSystem`, `offers.price: 0`, `license`, `codeRepository`.
- `FAQPage` — the highest-leverage element. FAQ schema is what wins featured snippets for
  queries such as *"how to calculate crypto tax India"*.

Page sections, in order:

1. **Hero** — title, one-line description, two CTAs (Get started, View on GitHub).
2. **Disclaimer banner** — above the fold, visually distinct, links to `DISCLAIMER.md`.
3. **What it does** — FIFO, Section 115BBH, USDT pair handling, multi-sheet Excel output.
4. **Your data never leaves your machine** — runs locally, no account, no upload, no
   telemetry. This is the strongest differentiator against every SaaS crypto-tax product and
   deserves its own section rather than a bullet.
5. **Install and usage** — copy-pasteable blocks.
6. **Sample output** — the Crypto-wise Summary table with illustrative figures, clearly
   labelled as sample data.
7. **FAQ** — mirrors the JSON-LD. Questions: Is this tax advice? What is Section 115BBH?
   What is FIFO and why does it matter? How are USDT pairs handled? Is my data uploaded
   anywhere? Which exchanges are supported? What does it not handle? Is it free?
8. **License and links.**

**`site/robots.txt`** — allow all, point to sitemap.
**`site/sitemap.xml`** — the single page.

**`README.md`** — rewrite the top third only: keyword-bearing H1, one-line description,
badges (CI, license, Python version), disclaimer callout, link to the site. Existing
Requirements / Usage / Input Format / Troubleshooting / Technical Notes sections are already
good and stay as they are.

### 4. Repository metadata

Set via `gh`:

- **Description:** keyword-bearing one-liner naming Section 115BBH and FIFO.
- **Homepage:** the Pages URL.
- **Topics:** `crypto-tax`, `crypto-tax-india`, `india`, `income-tax`, `section-115bbh`,
  `vda`, `fifo`, `pnl-calculator`, `capital-gains`, `itr`, `cryptocurrency`, `python`,
  `coindcx`, `tax-calculator`.

`coindcx` is retained as a topic. A topic is a factual index term, not branding.

### 5. Rename

`sanketdaru/coindcx-crypto-pnl-analyzer` → `sanketdaru/india-crypto-tax-calculator`.

GitHub permanently redirects the old URL and existing git remotes, so nothing breaks. Also
update `pyproject.toml` `name` and the local git remote.

## Manual steps required from the user

These cannot be automated or may need a browser:

1. **Settings → Pages → Source: GitHub Actions.** Attempt via API first; may need a click.
2. **Enable private vulnerability reporting.** Attempt via API first.
3. **Google Search Console** — verify the site and submit `sitemap.xml`. Requires the user's
   Google account. Without this, indexing is slow.
4. **Optional: legal review** by a qualified professional if meaningful usage is expected.

Also noted, not actionable: the author's name and email are already in the public git history
as committer metadata. This is normal for open source but is independent of anything here.

## Testing

- `uv run pytest` — existing 24 tests must stay green; CI enforces this.
- HTML validity and JSON-LD correctness verified by parsing `site/index.html` and
  round-tripping each `application/ld+json` block through a JSON parser.
- Every internal link in the site and in the Markdown files resolved against the filesystem
  or the live repo.
- The runtime disclaimer asserted by a new test, so it cannot be silently dropped.

## Risks

| Risk | Mitigation |
|---|---|
| User pastes a real tax export into a public issue | Required redaction checkbox on the issue form; warning in `CONTRIBUTING.md`, `SUPPORT.md` and the bug template body |
| Disclaimers are ignored because they are boilerplate | Restated at runtime, where they cannot be skipped |
| Boilerplate is insufficient for actual legal protection | Explicitly flagged to the user; professional review recommended |
| CoinDCX changes its export format again | Already mitigated by fail-loud parsing; `DISCLAIMER.md` states formats may change |
