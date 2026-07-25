# Contributing

Thanks for considering a contribution.

## Before you open an issue or PR

> **Never attach a real CoinDCX export, a generated report, or a screenshot of
> either.** Those files contain your name, email address, PAN, and your complete
> trading history. Once posted in a public issue they cannot be fully deleted.
>
> Reduce your problem to a few fabricated rows before sharing it.

## Understand the design first

[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) explains why the code is shaped the way it
is. Several decisions look arbitrary and are not — the valuation of crypto-quoted trades
and the plan-then-commit FIFO disposal especially. Read it before changing how any figure
is computed.

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
