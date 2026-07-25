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

- [Quick start](#quick-start) (with a **full Windows walkthrough** for non-programmers)
- [Requirements](#requirements) · [Usage](#usage) · [Input File Format](#input-file-format)
- [Output Reports](#output-reports) · [Key Tax Rules](#key-tax-rules-section-115bbh)
- [Troubleshooting](#troubleshooting) · [Technical Notes](#technical-notes)
- [Architecture](docs/ARCHITECTURE.md) · [Disclaimer](DISCLAIMER.md) · [Contributing](CONTRIBUTING.md) · [Support](SUPPORT.md) · [Security](SECURITY.md)

## Not affiliated with CoinDCX

This project is not affiliated with, endorsed by or sponsored by CoinDCX or
Neblio Technologies Private Limited. "CoinDCX" identifies the trade report file
format this software reads. All trademarks belong to their respective owners.

## Requirements

Just [`uv`](https://docs.astral.sh/uv/getting-started/installation/). You do **not** need
to install Python separately — `uv` fetches the right version for you.

## Quick start

```bash
git clone https://github.com/sanketdaru/india-crypto-tax-calculator.git
cd india-crypto-tax-calculator
uv sync
uv run python crypto_pnl_calculator.py
```

Reads `crypto_transactions.xlsx` from the current folder and writes
`crypto_pnl_report_FY2025-26.xlsx` beside it.

Never used a command line before? Open the guide for your system below — it assumes no
programming knowledge and skips nothing.

<details>
<summary><b>📘 Step-by-step for Windows — no programming experience needed</b></summary>

### Step 1 · Download the calculator

1. Go to [the project page on GitHub](https://github.com/sanketdaru/india-crypto-tax-calculator).
2. Click the green **Code** button, then **Download ZIP**.
3. Open your **Downloads** folder and find `india-crypto-tax-calculator-master.zip`.
4. Right-click it → **Extract All…** → **Extract**.
5. You now have a folder called `india-crypto-tax-calculator-master`. Move it somewhere
   easy to find, such as your Desktop.

> Prefer `git clone`? See the **Using Git instead of the ZIP** section further down. The
> ZIP is simpler and works identically.

### Step 2 · Install uv

`uv` is the tool that runs the calculator. It is free, open source and made by Astral.

1. Press the **Windows key**, type `PowerShell`, and click **Windows PowerShell**.
2. Copy the line below, paste it into the blue window (right-click pastes), press **Enter**:

   ```powershell
   winget install --id=astral-sh.uv -e
   ```

3. Wait for it to finish. If it asks you to agree to terms, type `Y` and press Enter.
4. **Close PowerShell completely and open it again.** This step is required — the new
   command is not available until you do.

> If `winget` is not recognised (older Windows), use this instead:
>
> ```powershell
> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
> ```

### Step 3 · Open PowerShell inside the folder

1. Open the `india-crypto-tax-calculator-master` folder.
2. Hold **Shift** and right-click on an empty area inside the folder.
3. Choose **Open PowerShell window here** (Windows 11: **Open in Terminal**).

> No such option? Open PowerShell normally, type `cd ` (with a space), then drag the
> folder onto the window and press Enter.

### Step 4 · Set it up, once

```powershell
uv sync
```

Downloads Python and the libraries the calculator needs. Takes a minute the first time,
instant afterwards.

### Step 5 · Add your CoinDCX trade report

1. Log in to CoinDCX and download your **Trade Report** for the financial year as an Excel file.
2. Rename it to exactly `crypto_transactions.xlsx`.
3. Put it in the `india-crypto-tax-calculator-master` folder, beside `crypto_pnl_calculator.py`.

> Windows may hide the `.xlsx` ending. If you end up with `crypto_transactions.xlsx.xlsx`
> the name is wrong — turn on **File name extensions** under the **View** tab in File
> Explorer to see what is really there.

### Step 6 · Run it

```powershell
uv run python crypto_pnl_calculator.py
```

The disclaimer prints first, then a summary of your gains and losses.

### Step 7 · Collect your report

A new file appears in the same folder, named for your financial year — for example
`crypto_pnl_report_FY2025-26.xlsx`. Open it in Excel. Three sheets: every transaction, a
per-asset summary, and headline totals.

⚠️ **Take that file to a qualified tax professional before you file anything.**

</details>

<details>
<summary><b>🍎 Step-by-step for macOS or Linux</b></summary>

Open **Terminal** and install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Close and reopen Terminal, then:

```bash
git clone https://github.com/sanketdaru/india-crypto-tax-calculator.git
cd india-crypto-tax-calculator
uv sync
```

Save your CoinDCX trade report into that folder as `crypto_transactions.xlsx`, then:

```bash
uv run python crypto_pnl_calculator.py
```

Your report is written beside it as `crypto_pnl_report_FY2025-26.xlsx`.

</details>

<details>
<summary><b>Using Git instead of the ZIP</b></summary>

If you already have [Git](https://git-scm.com/downloads), or want to pull updates later
with `git pull`:

```bash
git clone https://github.com/sanketdaru/india-crypto-tax-calculator.git
cd india-crypto-tax-calculator
uv sync
uv run python crypto_pnl_calculator.py
```

On Windows, install Git first with `winget install --id=Git.Git -e`.

</details>

<details>
<summary><b>🔧 Something went wrong</b></summary>

**"uv is not recognized as the name of a cmdlet"**
PowerShell was open before `uv` was installed. Close every PowerShell window, open a fresh
one, try again. If it still fails, reinstall with the `irm` command in Step 2.

**"running scripts is disabled on this system"**
Windows is blocking the installer script. Use the `winget` command in Step 2 instead — it
does not run a script.

**"No such file or directory: crypto_transactions.xlsx"**
The calculator cannot see your trade report. Check it sits in the same folder as
`crypto_pnl_calculator.py` and that the name matches exactly. Turn on file name extensions
in File Explorer to check for a hidden double `.xlsx.xlsx`.

**"Could not find the 'trade time' column"**
The export is not in the expected shape. Make sure you downloaded the **Trade Report** from
CoinDCX and did not edit, re-save or reorder it. The error names every column it did find,
which usually shows what happened.

**"Insufficient holdings for …"**
You sold an asset the export contains no purchase for — usually bought before the report's
date range, or transferred in from elsewhere. Export a period covering your full history
for that asset. This is a documented limitation, not a bug — see [DISCLAIMER.md](DISCLAIMER.md).

**Still stuck**
Open an [issue](https://github.com/sanketdaru/india-crypto-tax-calculator/issues).
**Never attach your real export or report** — they contain your name and full trading
history. Describe the problem with made-up numbers instead.

</details>

## Usage

### Basic usage

```bash
uv run python crypto_pnl_calculator.py
```

Processes `crypto_transactions.xlsx` in the current directory and generates
`crypto_pnl_report_FY2025-26.xlsx`.

### Custom input/output files

```bash
uv run python crypto_pnl_calculator.py input_file.xlsx output_report.xlsx
```

### Running the tests

```bash
uv run pytest
```

## Input File Format

The script expects an Excel file exported from CoinDCX with two sheets:

### 1. Instant Orders Sheet

**Format**: CoinDCX Trade Report - Instant Orders export

**Required columns** (header row at Excel row 9):

- Trade ID *(or `Transaction ID`)*
- Crypto
- Trade Completion time *(or `Transaction time`)*
- Side (Buy/Sell)
- Avg Buying/Selling Price(in INR)
- Quantity
- Gross Amount Paid/Received by the user(in INR)
- Fees(in INR) *(optional)*
- Net Amount Paid/Received by the user(in INR)
- *TDS(in INR) *(or `**TDS(in INR)`; optional)*

**Note**: The sheet must include the CoinDCX standard header rows (approximately 8 rows) before the column headers.

### 2. Spot Orders Sheet
**Format**: CoinDCX Trade Report - Spot Orders export

**Required columns** (header row at Excel row 9):

- Order ID
- Trade ID
- Crypto Pair (e.g., `BTCINR`, `ETHUSDT`, `SOLINR`, `BTC-USDT`, `BTC/USDT`)
- Base currency
- Trade Completion time *(or `Transaction time`)*
- Side (Buy/Sell)
- Avg Buying/Selling Price(in base currency)
- Quantity
- Gross Amount Paid/Received by the user(in base currency)
- Fees(in base currency)
- Net Amount Paid/Received by the user(in base currency)
- *Net Amount Paid/Received by the user (in INR)
- **TDS (in INR)

**Note**: The sheet must include the CoinDCX standard header rows (approximately 8 rows) before the column headers.

### Excel File Structure

The script expects the standard CoinDCX export format with:

- Header information at row 9 (0-indexed row 8)
- Transaction data starting from row 10 onwards

## Output Reports

The script generates an Excel file with 3 sheets:

### 1. Transaction Log

Detailed log of every transaction including:

- Date, Crypto, Transaction Type, Side
- Quantity, Price per Unit, Gross Amount
- Fees, TDS (for reference only)
- Cost Basis, Proceeds, P&L
- Description (including implicit USDT transactions)

### 2. Crypto-wise Summary

Summary for each cryptocurrency:

- Total Quantity Bought/Sold
- **Total Purchase Cost (INR)** — what was paid for everything acquired, whether sold or still held
- **Cost Basis of Sold (INR)** — FIFO cost of only the quantity disposed
- Total Proceeds (INR)
- Total P&L (INR) — always equals `Total Proceeds − Cost Basis of Sold`
- Total Fees and TDS (reference only)
- Remaining Holdings

### 3. Overall Summary

- Financial Year
- Total Realized P&L
- Total TDS Deducted
- Total Fees Paid
- Transaction counts
- Date range
- Unique cryptocurrencies

## Key Tax Rules (Section 115BBH)

1. **Cost Basis**: Gross purchase amount (fees NOT added)
2. **Proceeds**: Gross sale amount (fees NOT deducted)
3. **Profit/Loss**: Proceeds - Cost Basis
4. **TDS**: Tracked separately for reference (can be claimed while filing ITR)
5. **FIFO Method**: Oldest holdings are disposed first
6. **USDT Pairs**: Each USDT trade triggers two events:
   - Disposal of one asset (P&L calculation)
   - Acquisition of another asset (cost basis tracking)

## Example Scenarios

### INR-based Trade

```plaintext
Buy: BTCINR - Purchase 0.001 BTC for ₹5,000
Cost Basis: ₹5,000
Fees: ₹29.50 (tracked but not added to cost basis)

Sell: BTCINR - Sell 0.001 BTC for ₹6,000
Proceeds: ₹6,000
Fees: ₹35.40 (tracked but not deducted from proceeds)
P&L: ₹6,000 - ₹5,000 = ₹1,000 profit
```

### USDT Pair Trade

```plaintext
Buy: ETHUSDT - Buy 0.01 ETH with 30 USDT

This creates TWO transactions:
1. SELL 30 USDT (disposal event)
   - Proceeds: INR equivalent of 30 USDT
   - Cost Basis: FIFO cost of 30 USDT from holdings
   - P&L: Calculated

2. BUY 0.01 ETH
   - Cost Basis: INR equivalent of 30 USDT
   - Added to ETH holdings
```

## Warnings and Error Handling

### USDT Holdings Warnings

The script may show warnings like:

```plaintext
Warning: Insufficient holdings for USDT: need 120.00000000, hold 50.00000000, short by 70.00000000 for transaction on 2025-09-04
```

**Causes:**

- USDT was used to buy crypto but wasn't acquired in the current data export
- USDT may have been purchased before the reporting period
- USDT was acquired through external transfers not in the transaction file

**Solution:**

- Ensure all USDT purchase transactions are included in the Excel file
- Include transactions from all relevant time periods
- If USDT was externally transferred, manually add those transactions

These warnings indicate incomplete USDT P&L data. The script will still process other transactions correctly, but USDT disposal P&L will be marked as errors. A failed disposal leaves the inventory untouched, so later valid sells keep their cost basis.

### Parse Errors

A row that cannot be read aborts the run with the sheet and row number, for example:

```plaintext
Error: Instant Orders row 4: Unrecognised side 'Transfer' (expected Buy or Sell)
Error: Spot Orders row 12: Could not find the 'trade time' column. Tried [...]. Sheet has: [...]
```

This is deliberate. Earlier versions skipped bad rows and printed a warning, which produced a plausible-looking but wrong tax report when an export used renamed headers.

## Troubleshooting

### No transactions parsed / 0 transactions

**Causes:**

1. Excel file sheets are not named "Instant Orders" and "Spot Orders"
2. Excel file structure has been modified
3. Column headers don't match expected format
4. Data rows are empty

**Solutions:**

- Verify sheet names exactly match "Instant Orders" and "Spot Orders" (case-sensitive)
- Use unmodified CoinDCX export files
- Check console output for specific parsing errors
- Ensure the Excel file contains actual transaction data

### Incorrect P&L calculations

**Common Issues:**

1. **Missing buy transactions**: Ensure all purchase transactions are included for each crypto you're selling
2. **Missing USDT purchases**: For USDT pair trades, verify USDT purchase transactions are in the file
3. **Date range issues**: Include all transactions from the start of your trading history

**Verification Steps:**

- Check "Transaction Log" sheet in output for all parsed transactions
- Verify buy quantities match your expectations
- Review USDT holdings in "Crypto-wise Summary"

### USDT P&L showing ₹0.00 or errors

**Problem**: USDT purchase transactions are not being loaded.

**Solution**:

- Verify Instant Orders sheet contains USDT buy transactions
- Check that USDT purchases occurred before USDT disposals (chronologically)
- Ensure all USDT acquisition sources are in the file

### Missing cryptos in report

**Causes:**

- Transactions failed to parse (check console for errors)
- Crypto symbols don't match expected format
- Transactions are in a different sheet not being processed

**Solutions:**

- Review console output for parsing errors
- Verify crypto symbols: BTC, ETH, USDT, SOL, XRP, etc. (not BTC-USD or BTC/USD)
- Check both Instant Orders and Spot Orders sheets

### Excel file format issues

**Error**: "Unable to read Excel file" or "Sheet not found"

**Solutions:**

1. Ensure file is in `.xlsx` format (not `.xls` or `.csv`)
2. Install required packages: `pip install pandas openpyxl`
3. Verify file is not corrupted
4. Check file permissions

## Technical Notes

### Excel File Structure Detection

The script automatically reads:

- **Instant Orders**: Header at row 9 (0-indexed row 8)
- **Spot Orders**: Header at row 9 (0-indexed row 8)

This matches the standard CoinDCX trade report export format, which includes:

- Rows 1-6: Report metadata (date range, user info, etc.)
- Rows 7-8: Instructions and notes
- Row 9: Column headers
- Row 10+: Transaction data

### USDT Pair Processing Logic

When processing USDT pairs, the script creates two transactions:

**For BUY (e.g., ETHUSDT BUY 0.01 ETH for 30 USDT):**

1. SELL 30 USDT → Calculate P&L using FIFO cost basis
2. BUY 0.01 ETH → Record acquisition at INR equivalent value

**For SELL (e.g., ETHUSDT SELL 0.01 ETH for 30 USDT):**

1. SELL 0.01 ETH → Calculate P&L using FIFO cost basis
2. BUY 30 USDT → Record acquisition at INR equivalent value

### INR Valuation of USDT-Quoted Trades

CoinDCX only supplies an INR figure for the **net** amount (`*Net Amount Paid/Received by the user (in INR)`), which already has the fee added (buys) or subtracted (sells). Section 115BBH needs **gross** figures, so the script derives the rate and revalues:

```plaintext
inr_rate  = net_amount_in_INR / net_amount_in_base
gross_INR = gross_amount_in_base * inr_rate
fees_INR  = fees_in_base * inr_rate
```

The quote-currency leg (USDT) is recorded at the **net** quantity, since that is what actually moves in and out of the wallet — the fee is paid in USDT too. The target crypto leg is recorded at the **gross** INR value, keeping fees out of cost basis and proceeds.

### TDS Attribution

TDS is levied on the *transfer* of a VDA, so it is recorded against the disposal leg:

- `ETHUSDT BUY` → TDS sits on the **USDT SELL** leg
- `ETHUSDT SELL` → TDS sits on the **ETH SELL** leg

Totals are unaffected; only the per-crypto breakdown differs.
