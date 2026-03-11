# Crypto P&L Calculator (for CoinDCX trades)

A Python script to calculate cryptocurrency profit and loss statements compliant with Indian VDA (Virtual Digital Asset) taxation under Section 115BBH of the Income Tax Act, 1961. This script is provided as-is for informational purposes only and should not be considered as tax advice.

## Features

- ✅ **FIFO Inventory Accounting**: Uses First In First Out method for cost basis calculation
- ✅ **USDT Pair Transformation**: Automatically handles implicit disposal events when trading with USDT
  - `ETHUSDT BUY` → SELL USDT (P&L event) + BUY ETH
  - `ETHUSDT SELL` → SELL ETH (P&L event) + BUY USDT
- ✅ **Section 115BBH Compliance**: Fees are NOT included in cost basis or proceeds (as per Indian VDA tax rules)
- ✅ **Multi-Sheet Excel Output**: Generates comprehensive reports with transaction log, crypto-wise summary, and overall summary
- ✅ **Indian Financial Year Support**: Automatically detects and reports for April-March financial year
- ✅ **Comprehensive Error Handling**: Validates data and reports parsing issues
- ✅ **Accurate USDT Tracking**: Properly tracks USDT cost basis for P&L calculations

## Requirements

```bash
pip install pandas openpyxl
```

## Usage

### Basic Usage

```bash
python crypto_pnl_calculator.py
```

This will process `crypto_transactions.xlsx` in the current directory and generate `crypto_pnl_report_FY2025-26.xlsx`.

### Custom Input/Output Files

```bash
python crypto_pnl_calculator.py input_file.xlsx output_report.xlsx
```

## Input File Format

The script expects an Excel file exported from CoinDCX with two sheets:

### 1. Instant Orders Sheet

**Format**: CoinDCX Trade Report - Instant Orders export

**Required columns** (header row at Excel row 9):

- Trade ID
- Crypto
- Trade Completion time
- Side (Buy/Sell)
- Avg Buying/Selling Price(in INR)
- Quantity
- Gross Amount Paid/Received by the user(in INR)
- Fees(in INR)
- Net Amount Paid/Received by the user(in INR)
- *TDS(in INR)

**Note**: The sheet must include the CoinDCX standard header rows (approximately 8 rows) before the column headers.

### 2. Spot Orders Sheet
**Format**: CoinDCX Trade Report - Spot Orders export

**Required columns** (header row at Excel row 9):

- Order ID
- Trade ID
- Crypto Pair (e.g., BTCINR, ETHUSDT, SOLINR)
- Base currency
- Trade Completion time
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
- Total Cost Basis and Proceeds
- Total P&L
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
Warning: No holdings available for USDT for transaction on 2025-09-03
```

**Causes:**

- USDT was used to buy crypto but wasn't acquired in the current data export
- USDT may have been purchased before the reporting period
- USDT was acquired through external transfers not in the transaction file

**Solution:**

- Ensure all USDT purchase transactions are included in the Excel file
- Include transactions from all relevant time periods
- If USDT was externally transferred, manually add those transactions

These warnings indicate incomplete USDT P&L data. The script will still process other transactions correctly, but USDT disposal P&L will be marked as errors.

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

## Disclaimer

This script is provided as-is for informational purposes only and should not be considered as tax advice. Users are responsible for ensuring the accuracy of their tax filings and should consult with qualified tax professionals.
