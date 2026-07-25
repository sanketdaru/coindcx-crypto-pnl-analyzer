# Architecture and Design Decisions

Why the code is shaped the way it is. Read this before changing how any figure is
computed — several decisions here look arbitrary and are not.

Everything lives in one module, `crypto_pnl_calculator.py`. It is small enough to hold
in your head, and splitting it would spread a single calculation across files for no
gain. If it grows past roughly a thousand lines, split along the pipeline stages below.

## Pipeline

```
CoinDCX .xlsx
   │  load_data()              read 'Instant Orders' and 'Spot Orders', header row 9
   ▼
parse_instant_orders()         INR-quoted, one Transaction per row
parse_spot_orders()            INR- or crypto-quoted; crypto-quoted rows emit TWO
   │                           Transactions (see "Crypto-quoted trades")
   ▼
List[Transaction]              sorted by (date, buys before sells)
   │  process_transactions()
   ▼
FIFOInventory                  per-asset deque of {quantity, cost_per_unit, date}
   │
   ▼
pnl_records                    one dict per transaction, with cost basis and P&L
   │  generate_excel_report()
   ▼
3-sheet .xlsx                  Transaction Log · Crypto-wise Summary · Overall Summary
```

## Tax rules encoded

Section 115BBH of the Income Tax Act, 1961 (India):

- **Gross figures on both sides.** Cost basis is the gross purchase amount; proceeds are
  the gross sale amount. Fees are tracked for reference but never added to cost or
  deducted from proceeds. This is why the parser works so hard to recover *gross* values
  from an export that only reports *net* ones.
- **FIFO only.** Oldest lots dispose first. No other method is offered.
- **No set-off or carry-forward is computed.** Per-asset losses in the report are
  informational; the section disallows setting them against other income.
- **TDS is reference-only** (Section 194S). Reported, never netted into P&L.

## Decisions

### Column resolution is alias-based, not literal

`resolve_column()` matches headers through `_normalize_column()`, which lowercases and
strips whitespace and footnote asterisks.

CoinDCX has shipped at least two namings of the same export: `Trade Completion time` vs
`Transaction time`, and `*TDS(in INR)` vs `**TDS(in INR)`. Literal lookups broke on the
newer file. Add new spellings to the candidate tuples rather than renaming anything.

### Parsing fails loudly

An unreadable row raises with its sheet and row number. It is never skipped.

This is the single most important behavioural rule in the codebase. An earlier version
caught every exception and continued: when the headers changed, all sixteen instant
orders were silently dropped, every USDT purchase vanished, and the tool produced a
clean-looking report with the realised P&L understated by roughly 94%. A dropped
purchase understates cost basis and **overstates someone's taxable gain**. Failing loudly
is always correct here; a wrong tax return is worse than no output.

### Pair symbols are split, not string-replaced

`resolve_symbol(pair, base_currency)` handles `BTCUSDT`, `BTC-USDT`, `BTC/USDT` and
`BTC_USDT`, preferring the export's `Base currency` column and falling back to
`KNOWN_QUOTE_CURRENCIES`.

`pair.replace('USDT', '')` turns `BTC-USDT` into `BTC-`, which silently forks holdings
across two phantom assets, and would mangle a pair like `USDTINR`. A single export can
mix both styles.

### Crypto-quoted trades are two taxable events

Buying ETH with USDT disposes of USDT *and* acquires ETH. Ignoring the first leg
understates taxable income, so `_parse_spot_row()` emits both, disposal first.

The valuation is the subtlest thing in this codebase. The export gives an INR figure only
for the **net** amount, but Section 115BBH wants **gross**, so the rate is derived and
the gross leg revalued:

```
inr_rate  = net_inr / net_base
gross_inr = gross_base * inr_rate
fees_inr  = fees_base * inr_rate
```

- The **quote leg** (USDT) carries `net_base` as its quantity, because the net amount is
  what actually leaves or enters the wallet — the trading fee is paid in USDT too.
- The **target leg** carries `gross_inr` as its value, keeping fees out of cost basis and
  proceeds.

The two legs therefore differ by the fee. That is correct: the fee is a real, non-deductible
cost. If you "fix" that asymmetry you will reintroduce fees into cost basis.

### TDS attaches to the disposal leg

TDS is levied on the *transfer* of a virtual digital asset. On `ETHUSDT BUY` the transfer
is of USDT, so the TDS belongs to the USDT sell leg, not to ETH. Totals are unaffected;
the per-asset breakdown is not.

### FIFO disposal plans before it mutates

`dispose_holding()` builds the full disposal plan, raises `InsufficientHoldingsError` if
the holding is short, and only then commits.

An earlier version popped lots as it went and raised on exhaustion, so a single oversell
consumed the inventory *and* recorded no P&L — destroying the cost basis that later valid
sells needed. Never mutate inventory before the disposal is known to succeed.

### Buys settle first on identical timestamps

`process_transactions()` sorts by `(date, 0 if BUY else 1)`. Exchange exports routinely
carry same-second fills; without the tiebreak a buy/sell pair in the same second looks
like an oversell. Python's sort is stable, so the two legs of one crypto-quoted trade keep
their emitted order.

### The summary sheet separates two different costs

`Total Purchase Cost (INR)` covers everything acquired, sold or still held.
`Cost Basis of Sold (INR)` covers only what was disposed.

Only the second nets against proceeds. An earlier version reported one column for both, so
`Total P&L` did not equal `Proceeds − Cost Basis` on its own sheet.

### The disclaimer prints at runtime

`print_disclaimer()` is the first statement of `run()`. Files can go unread; a console
notice cannot. `tests/test_disclaimer.py` asserts it appears *before* the report banner,
so a refactor cannot quietly relocate it.

## Rules for anyone working in this repo

These exist because each has already been violated once.

1. **No real trade data anywhere in the repository.** Not in tests, not in docs, not in the
   site's sample table, not in a commit message. The owner's exports contain their name and
   full trading history. Fixtures must be fabricated *and* internally consistent — preserve
   `net = gross ± fees` and `rate = net_inr / net_base`, or the tests stop exercising the
   parser's real arithmetic.
2. **Never commit a spreadsheet.** `.gitignore` covers `*.xlsx`, `*.xls`, `*.xlsm`, `*.csv`
   and Excel lock files; CI fails the build if one is ever tracked.
3. **Tests never read a file from the repository root.** Build the workbook in `tmp_path`,
   or hand a `DataFrame` straight to the parser. Both patterns are in
   `tests/test_crypto_pnl_calculator.py`.
4. **No personal email address in any tracked file.** Security and conduct reports route
   through GitHub forms for this reason.
5. **The site is self-contained.** No CDN, no external fonts, no analytics, no remote
   images — the page must render fully offline. Plain `<a>` hyperlinks to documentation
   are fine; only things the browser *fetches* are banned.
   `test_page_loads_no_external_assets` checks `src=` and non-canonical `<link>` tags,
   and `test_no_trackers_or_cdns` blocks known analytics and CDN hosts by name.
6. **"CoinDCX" is factual, never branding.** It names the export format read. The
   non-affiliation notice must stay wherever it appears prominently.
7. **Don't claim the output is correct.** The site and README describe what the tool
   *does*; they never assert its tax treatment is right. That would contradict
   [DISCLAIMER.md](../DISCLAIMER.md) and is exactly the kind of representation a warranty
   disclaimer protects against least.

## Tests

| File | Covers |
|---|---|
| `tests/test_crypto_pnl_calculator.py` | Both header variants, all pair styles, FIFO ordering, inventory preservation on oversell, gross-vs-net valuation, TDS attribution, summary reconciliation |
| `tests/test_disclaimer.py` | Disclaimer text, and that it prints before the report on a real run |
| `tests/test_site.py` | Landing page SEO payload: title and description lengths, canonical URL, Open Graph, JSON-LD validity, self-containment |

Run with `uv run pytest`. When fixing a bug, write the failing test first — a tax
miscalculation without a regression test is one that comes back.
