# Notes for coding agents

Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before changing how any figure is
computed. It explains the design decisions that look arbitrary and are not — the
crypto-quoted trade valuation and the plan-then-commit FIFO disposal in particular.

## Non-negotiables

1. **No real trade data anywhere.** Not in tests, docs, the site's sample table, or a
   commit message. Fixtures are fabricated *and* internally consistent
   (`net = gross ± fees`, `rate = net_inr / net_base`).
2. **Never commit a spreadsheet.** `*.xlsx`/`*.xls`/`*.xlsm`/`*.csv` are gitignored and CI
   fails if one is tracked.
3. **Tests never read a file from the repository root.** Build workbooks in `tmp_path`.
4. **No personal email address in any tracked file.**
5. **Parsing fails loudly.** Never skip an unreadable row. A dropped purchase overstates
   someone's taxable gain.
6. **The site is self-contained** — no CDN, fonts, analytics or remote images.
7. **Never claim the output is tax-correct.** Describe what the tool does.

## Commands

```bash
uv sync                                    # set up
uv run pytest                              # 43 tests
python crypto_pnl_calculator.py            # run on crypto_transactions.xlsx
python crypto_pnl_calculator.py in.xlsx out.xlsx
```

## Conventions

- Single module, `crypto_pnl_calculator.py`. Split along pipeline stages only if it grows
  past ~1000 lines.
- Failing test first, then the fix.
- If you change a tax computation, cite the rule in the commit message.
