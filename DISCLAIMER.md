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
or implied. See sections 7 and 8 of [LICENSE](LICENSE) for the controlling
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
