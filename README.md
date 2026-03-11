# Crypto P&L Calculator for Indian VDA Taxation

A Python script to calculate cryptocurrency profit and loss statements compliant with Indian VDA (Virtual Digital Asset) taxation under Section 115BBH of the Income Tax Act, 1961.

## Features

- **FIFO Inventory Accounting**: Uses First In First Out method for cost basis calculation
- **USDT Pair Transformation**: Automatically handles implicit disposal events when trading with USDT
  - `ETHUSDT BUY` → SELL USDT (P&L event) + BUY ETH
  - `ETHUSDT SELL` → SELL ETH (P&L event) + BUY USDT
- **Section 115BBH Compliance**: Fees are NOT included in cost basis or proceeds (as per Indian VDA tax rules)
- **Multi-Sheet Excel Output**: Generates comprehensive reports with transaction log, crypto-wise summary, and overall summary
- **Indian Financial Year Support**: Automatically detects and reports for April-March financial year

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

The script expects an Excel file with two sheets:

### 1. Instant Orders Sheet
Columns:
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

### 2. Spot Orders Sheet
Columns:
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
```
Buy: BTCINR - Purchase 0.001 BTC for ₹5,000
Cost Basis: ₹5,000
Fees: ₹29.50 (tracked but not added to cost basis)

Sell: BTCINR - Sell 0.001 BTC for ₹6,000
Proceeds: ₹6,000
Fees: ₹35.40 (tracked but not deducted from proceeds)
P&L: ₹6,000 - ₹5,000 = ₹1,000 profit
```

### USDT Pair Trade
```
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

## Warnings

The script may show warnings like:
```
Warning: No holdings available for USDT for transaction on 2025-09-03
```

This is normal and means:
- USDT was used to buy crypto but wasn't acquired in the current data period
- USDT may have been purchased before the reporting period
- Or USDT was acquired through means not in the transaction file

These warnings don't affect other calculations but indicate incomplete USDT P&L data.

## Troubleshooting

### No transactions parsed
- Check if Excel file has sheets named "Instant Orders" and "Spot Orders"
- Verify column headers match expected format
- Check if data rows start after header rows

### Incorrect P&L calculations
- Verify all buy transactions before sell transactions are included
- Check if USDT purchases are in the data (for USDT pair trades)
- Ensure dates are in correct format

### Missing cryptos in report
- Check if transactions were successfully parsed (see console output)
- Verify crypto symbols match expected format (e.g., BTC, ETH, not BTC-USD)

## License

This script is provided as-is for tax calculation purposes. Please consult with a tax professional for accurate tax filing.

## Disclaimer

This tool is for informational purposes only and should not be considered as tax advice. Users are responsible for ensuring the accuracy of their tax filings and should consult with qualified tax professionals.