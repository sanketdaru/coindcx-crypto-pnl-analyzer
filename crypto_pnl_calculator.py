#!/usr/bin/env python3
"""
Crypto Asset P&L Calculator for Indian VDA Taxation (Section 115BBH)
Implements FIFO inventory accounting for crypto transactions
"""

import pandas as pd
from datetime import datetime
from collections import deque, defaultdict
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


# Quantities below this are treated as zero (crypto quantities carry up to 8 decimals)
QUANTITY_EPSILON = 1e-8

# Quote currencies used to split a trading pair when the export does not tell us
KNOWN_QUOTE_CURRENCIES = ('USDT', 'USDC', 'INR', 'BTC', 'ETH')


class MissingColumnError(KeyError):
    """Raised when a required column is absent from a CoinDCX export sheet"""


class InsufficientHoldingsError(ValueError):
    """Raised when a disposal exceeds the quantity currently held"""


def _normalize_column(name) -> str:
    """Normalize a header for matching: lowercase, no whitespace, no footnote asterisks"""
    return ''.join(str(name).split()).replace('*', '').lower()


def resolve_column(df: pd.DataFrame, candidates: Tuple[str, ...], label: str,
                   required: bool = True) -> Optional[str]:
    """
    Find the actual column name in `df` matching any of `candidates`.

    CoinDCX has shipped several header variants of the same export (e.g.
    'Trade Completion time' vs 'Transaction time', '*TDS(in INR)' vs
    '**TDS(in INR)'), so match on a normalized form and accept aliases.
    """
    lookup = {_normalize_column(c): c for c in df.columns}
    for candidate in candidates:
        actual = lookup.get(_normalize_column(candidate))
        if actual is not None:
            return actual
    if not required:
        return None
    raise MissingColumnError(
        f"Could not find the '{label}' column. Tried {list(candidates)}. "
        f"Sheet has: {list(df.columns)}"
    )


def resolve_symbol(pair: str, base_currency: Optional[str]) -> Tuple[str, str]:
    """
    Split a trading pair into (target symbol, quote currency).

    Handles every separator style CoinDCX has used: 'BTC-USDT', 'BTC/USDT',
    'BTC_USDT' and 'BTCUSDT'. A plain str.replace() is wrong here - it leaves
    'BTC-' for 'BTC-USDT' and would mangle a pair such as 'USDTINR'.
    """
    pair = str(pair).strip().upper()
    base = str(base_currency).strip().upper() if base_currency and pd.notna(base_currency) else ''

    for separator in ('-', '/', '_'):
        if separator in pair:
            target, _, quote = pair.rpartition(separator)
            if target and (not base or quote == base):
                return target, quote

    if base and pair.endswith(base) and len(pair) > len(base):
        return pair[:-len(base)], base

    for quote in KNOWN_QUOTE_CURRENCIES:
        if pair.endswith(quote) and len(pair) > len(quote):
            return pair[:-len(quote)], quote

    raise ValueError(f"Cannot determine target crypto for pair '{pair}' (base currency '{base}')")


class Transaction:
    """Represents a single crypto transaction"""
    
    def __init__(self, date: datetime, crypto: str, side: str, quantity: float,
                 price_per_unit: float, gross_amount: float, fees: float = 0.0,
                 tds: float = 0.0, description: str = ""):
        self.date = date
        self.crypto = crypto
        self.side = side.upper()  # BUY or SELL
        self.quantity = quantity
        self.price_per_unit = price_per_unit
        self.gross_amount = gross_amount
        self.fees = fees
        self.tds = tds
        self.description = description
        
    def __repr__(self):
        return f"Transaction({self.date.date()}, {self.crypto}, {self.side}, {self.quantity:.8f})"


class FIFOInventory:
    """Manages crypto holdings using FIFO (First In First Out) method"""
    
    def __init__(self):
        # Each crypto has a deque of (quantity, cost_per_unit, date)
        self.holdings: Dict[str, deque] = defaultdict(deque)
        
    def add_holding(self, crypto: str, quantity: float, cost_per_unit: float, date: datetime):
        """Add a new holding to inventory"""
        self.holdings[crypto].append({
            'quantity': quantity,
            'cost_per_unit': cost_per_unit,
            'date': date
        })
        
    def dispose_holding(self, crypto: str, quantity_to_dispose: float) -> Tuple[float, List[Dict]]:
        """
        Dispose holdings using FIFO method
        Returns: (total_cost_basis, list_of_disposals)

        The plan is built before anything is mutated, so a shortfall raises
        without consuming inventory - otherwise a single oversell would silently
        wipe out lots that later, valid sells still need for their cost basis.
        """
        lots = self.holdings.get(crypto)

        # Phase 1: plan the disposal without touching inventory
        plan: List[Tuple[Dict, float]] = []
        remaining_to_dispose = quantity_to_dispose
        for lot in (lots or ()):
            if remaining_to_dispose <= QUANTITY_EPSILON:
                break
            take = min(lot['quantity'], remaining_to_dispose)
            plan.append((lot, take))
            remaining_to_dispose -= take

        if remaining_to_dispose > QUANTITY_EPSILON:
            available = self.get_remaining_holdings(crypto)
            raise InsufficientHoldingsError(
                f"Insufficient holdings for {crypto}: need {quantity_to_dispose:.8f}, "
                f"hold {available:.8f}, short by {remaining_to_dispose:.8f}"
            )

        # Phase 2: commit
        total_cost_basis = 0.0
        disposals = []
        for lot, take in plan:
            cost = take * lot['cost_per_unit']
            total_cost_basis += cost
            disposals.append({
                'quantity': take,
                'cost_per_unit': lot['cost_per_unit'],
                'cost': cost,
                'acquisition_date': lot['date']
            })
            lot['quantity'] -= take

        while lots and lots[0]['quantity'] <= QUANTITY_EPSILON:
            lots.popleft()

        return total_cost_basis, disposals

    def get_remaining_holdings(self, crypto: str) -> float:
        """Get total quantity of remaining holdings for a crypto"""
        if crypto not in self.holdings:
            return 0.0
        return sum(h['quantity'] for h in self.holdings[crypto])
    
    def get_all_holdings(self) -> Dict[str, float]:
        """Get remaining holdings for all cryptos"""
        return {crypto: self.get_remaining_holdings(crypto) 
                for crypto in self.holdings.keys()}


class CryptoPnLCalculator:
    """Main calculator for crypto P&L with FIFO accounting"""
    
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        self.transactions: List[Transaction] = []
        self.inventory = FIFOInventory()
        self.pnl_records = []
        
    def load_data(self):
        """Load data from Excel file"""
        print(f"Loading data from {self.excel_file}...")
        
        # Read Instant Orders sheet - column headers are at row 8 (0-indexed)
        instant_orders = pd.read_excel(self.excel_file, sheet_name='Instant Orders', header=8)
        # Read Spot Orders sheet - column headers are at row 8 (0-indexed)  
        spot_orders = pd.read_excel(self.excel_file, sheet_name='Spot Orders', header=8)
        
        # Clean up - remove any completely empty rows
        instant_orders = instant_orders.dropna(how='all')
        spot_orders = spot_orders.dropna(how='all')
        
        print(f"Loaded {len(instant_orders)} instant orders and {len(spot_orders)} spot orders")
        
        return instant_orders, spot_orders
    
    @staticmethod
    def _optional_float(row, column: Optional[str]) -> float:
        """Read an optional numeric cell, treating blanks as 0.0"""
        if column is None:
            return 0.0
        value = row[column]
        return float(value) if pd.notna(value) else 0.0

    def parse_instant_orders(self, df: pd.DataFrame):
        """Parse Instant Orders (all INR-based)"""
        print("Parsing Instant Orders...")

        cols = {
            'date': resolve_column(df, ('Trade Completion time', 'Transaction time'), 'trade time'),
            'crypto': resolve_column(df, ('Crypto',), 'crypto'),
            'side': resolve_column(df, ('Side (Buy/Sell)', 'Side'), 'side'),
            'quantity': resolve_column(df, ('Quantity',), 'quantity'),
            'price': resolve_column(df, ('Avg Buying/Selling Price(in INR)',), 'price'),
            'gross': resolve_column(df, ('Gross Amount Paid/Received by the user(in INR)',), 'gross amount'),
            'fees': resolve_column(df, ('Fees(in INR)',), 'fees', required=False),
            'tds': resolve_column(df, ('*TDS(in INR)', 'TDS(in INR)'), 'TDS', required=False),
        }

        for position, (_, row) in enumerate(df.iterrows(), start=1):
            try:
                crypto = str(row[cols['crypto']]).strip().upper()
                side = self._normalize_side(row[cols['side']])

                txn = Transaction(
                    date=pd.to_datetime(row[cols['date']]),
                    crypto=crypto,
                    side=side,
                    quantity=float(row[cols['quantity']]),
                    price_per_unit=float(row[cols['price']]),
                    gross_amount=float(row[cols['gross']]),
                    fees=self._optional_float(row, cols['fees']),
                    tds=self._optional_float(row, cols['tds']),
                    description=f"Instant Order - {crypto} {side}"
                )
                self.transactions.append(txn)
            except Exception as e:
                # A dropped row silently understates cost basis and inflates P&L,
                # so surface it instead of continuing with an incomplete report.
                raise ValueError(f"Instant Orders row {position}: {e}") from e

    @staticmethod
    def _normalize_side(value) -> str:
        side = str(value).strip().upper()
        if side not in ('BUY', 'SELL'):
            raise ValueError(f"Unrecognised side '{value}' (expected Buy or Sell)")
        return side

    def parse_spot_orders(self, df: pd.DataFrame):
        """Parse Spot Orders (INR and crypto-quoted pairs)"""
        print("Parsing Spot Orders...")

        cols = {
            'date': resolve_column(df, ('Trade Completion time', 'Transaction time'), 'trade time'),
            'pair': resolve_column(df, ('Crypto Pair',), 'crypto pair'),
            'base': resolve_column(df, ('Base currency',), 'base currency', required=False),
            'side': resolve_column(df, ('Side (Buy/Sell)', 'Side'), 'side'),
            'quantity': resolve_column(df, ('Quantity',), 'quantity'),
            'price': resolve_column(df, ('Avg Buying/Selling Price(in base currency)',), 'price'),
            'gross_base': resolve_column(
                df, ('Gross Amount Paid/Received by the user(in base currency)',), 'gross amount'),
            'fees_base': resolve_column(df, ('Fees(in base currency)',), 'fees', required=False),
            'net_base': resolve_column(
                df, ('Net Amount Paid/Received by the user(in base currency)',), 'net amount', required=False),
            'net_inr': resolve_column(
                df, ('*Net Amount Paid/Received by the user (in INR)',), 'net amount in INR', required=False),
            'tds_inr': resolve_column(df, ('**TDS (in INR)', 'TDS (in INR)'), 'TDS in INR', required=False),
        }

        for position, (_, row) in enumerate(df.iterrows(), start=1):
            try:
                self._parse_spot_row(row, cols)
            except Exception as e:
                raise ValueError(f"Spot Orders row {position}: {e}") from e

    def _parse_spot_row(self, row, cols: Dict[str, Optional[str]]):
        date = pd.to_datetime(row[cols['date']])
        crypto_pair = str(row[cols['pair']]).strip()
        base_currency = row[cols['base']] if cols['base'] else None
        side = self._normalize_side(row[cols['side']])
        quantity = float(row[cols['quantity']])
        price_per_unit = float(row[cols['price']])
        gross_base = float(row[cols['gross_base']])
        fees_base = self._optional_float(row, cols['fees_base'])
        tds_inr = self._optional_float(row, cols['tds_inr'])

        target_crypto, quote_currency = resolve_symbol(crypto_pair, base_currency)

        if quote_currency == 'INR':
            # Base currency is already INR - one transaction, nothing implicit.
            self.transactions.append(Transaction(
                date=date,
                crypto=target_crypto,
                side=side,
                quantity=quantity,
                price_per_unit=price_per_unit,
                gross_amount=gross_base,
                fees=fees_base,
                tds=tds_inr,
                description=f"Spot Order - {crypto_pair} {side}"
            ))
            return

        # Crypto-quoted pair: the quote asset is itself bought/sold, so the
        # trade is two taxable events.
        #
        # Net amount = gross +/- fees, and is the quantity of quote currency
        # that actually moves in/out of the wallet. The export only gives an
        # INR figure for the NET amount, so derive the INR rate from it and
        # value the GROSS leg with that rate - Section 115BBH excludes fees
        # from cost of acquisition and from consideration.
        net_base = self._optional_float(row, cols['net_base'])
        if net_base <= 0:
            net_base = gross_base + fees_base if side == 'BUY' else gross_base - fees_base

        net_inr = self._optional_float(row, cols['net_inr'])
        if net_inr <= 0:
            raise ValueError(
                f"Missing INR valuation for {crypto_pair} trade quoted in {quote_currency}; "
                f"cannot value it for Section 115BBH reporting"
            )

        inr_rate = net_inr / net_base
        gross_inr = gross_base * inr_rate
        fees_inr = fees_base * inr_rate

        quote_leg = Transaction(
            date=date,
            crypto=quote_currency,
            side='SELL' if side == 'BUY' else 'BUY',
            quantity=net_base,
            price_per_unit=inr_rate,
            gross_amount=net_inr,
            fees=0.0,  # trade fee is recorded once, on the target leg
            # TDS is levied on the transfer of a VDA, so it belongs to whichever
            # leg is the disposal.
            tds=tds_inr if side == 'BUY' else 0.0,
            description=(f"Implicit {quote_currency} disposal from {crypto_pair} BUY" if side == 'BUY'
                         else f"Implicit {quote_currency} acquisition from {crypto_pair} SELL")
        )

        target_leg = Transaction(
            date=date,
            crypto=target_crypto,
            side=side,
            quantity=quantity,
            price_per_unit=gross_inr / quantity if quantity > 0 else 0.0,
            gross_amount=gross_inr,
            fees=fees_inr,
            tds=0.0 if side == 'BUY' else tds_inr,
            description=(f"Spot Order - {crypto_pair} BUY (bought with {quote_currency})" if side == 'BUY'
                         else f"Spot Order - {crypto_pair} SELL (for {quote_currency})")
        )

        # Disposal first so FIFO sees the acquisition it funds.
        if side == 'BUY':
            self.transactions.extend([quote_leg, target_leg])
        else:
            self.transactions.extend([target_leg, quote_leg])

    def process_transactions(self):
        """Process all transactions in chronological order and calculate P&L"""
        print(f"\nProcessing {len(self.transactions)} transactions...")
        
        # Sort by date; on identical timestamps settle acquisitions first so a
        # same-second buy/sell pair does not look like an oversell.
        self.transactions.sort(key=lambda x: (x.date, 0 if x.side == 'BUY' else 1))

        for txn in self.transactions:
            if txn.side == 'BUY':
                # Add to inventory (cost basis = gross amount per Section 115BBH)
                cost_per_unit = txn.gross_amount / txn.quantity if txn.quantity > 0 else 0
                self.inventory.add_holding(txn.crypto, txn.quantity, cost_per_unit, txn.date)
                
                # Record transaction (no P&L for buys)
                self.pnl_records.append({
                    'Date': txn.date,
                    'Crypto': txn.crypto,
                    'Transaction Type': 'BUY',
                    'Side': txn.side,
                    'Quantity': txn.quantity,
                    'Price per Unit (INR)': txn.price_per_unit,
                    'Gross Amount (INR)': txn.gross_amount,
                    'Fees (INR)': txn.fees,
                    'TDS (INR)': txn.tds,
                    'Cost Basis (INR)': txn.gross_amount,
                    'Proceeds (INR)': 0.0,
                    'P&L (INR)': 0.0,
                    'Description': txn.description
                })
                
            elif txn.side == 'SELL':
                # Dispose from inventory using FIFO
                try:
                    cost_basis, disposals = self.inventory.dispose_holding(txn.crypto, txn.quantity)
                    proceeds = txn.gross_amount  # Per Section 115BBH, no fee deduction
                    pnl = proceeds - cost_basis
                    
                    # Record transaction with P&L
                    self.pnl_records.append({
                        'Date': txn.date,
                        'Crypto': txn.crypto,
                        'Transaction Type': 'SELL',
                        'Side': txn.side,
                        'Quantity': txn.quantity,
                        'Price per Unit (INR)': txn.price_per_unit,
                        'Gross Amount (INR)': txn.gross_amount,
                        'Fees (INR)': txn.fees,
                        'TDS (INR)': txn.tds,
                        'Cost Basis (INR)': cost_basis,
                        'Proceeds (INR)': proceeds,
                        'P&L (INR)': pnl,
                        'Description': txn.description
                    })
                    
                except InsufficientHoldingsError as e:
                    print(f"Warning: {e} for transaction on {txn.date.date()}")
                    # Record transaction with error
                    self.pnl_records.append({
                        'Date': txn.date,
                        'Crypto': txn.crypto,
                        'Transaction Type': 'SELL (ERROR)',
                        'Side': txn.side,
                        'Quantity': txn.quantity,
                        'Price per Unit (INR)': txn.price_per_unit,
                        'Gross Amount (INR)': txn.gross_amount,
                        'Fees (INR)': txn.fees,
                        'TDS (INR)': txn.tds,
                        'Cost Basis (INR)': 0.0,
                        'Proceeds (INR)': txn.gross_amount,
                        'P&L (INR)': 0.0,
                        'Description': f"ERROR: {str(e)}"
                    })
    
    def generate_crypto_wise_summary(self) -> pd.DataFrame:
        """Generate crypto-wise P&L summary"""
        crypto_stats = defaultdict(lambda: {
            'Total Quantity Bought': 0.0,
            'Total Quantity Sold': 0.0,
            'Total Purchase Cost (INR)': 0.0,
            'Cost Basis of Sold (INR)': 0.0,
            'Total Proceeds (INR)': 0.0,
            'Total P&L (INR)': 0.0,
            'Total Fees (INR)': 0.0,
            'Total TDS (INR)': 0.0,
            'Remaining Holdings': 0.0
        })

        # Aggregate data from pnl_records
        for record in self.pnl_records:
            crypto = record['Crypto']

            if record['Side'] == 'BUY':
                crypto_stats[crypto]['Total Quantity Bought'] += record['Quantity']
                # What was paid for everything acquired, sold or still held
                crypto_stats[crypto]['Total Purchase Cost (INR)'] += record['Cost Basis (INR)']
            elif record['Side'] == 'SELL':
                crypto_stats[crypto]['Total Quantity Sold'] += record['Quantity']
                # FIFO cost of only the quantity disposed - this is what nets
                # against proceeds to give P&L
                crypto_stats[crypto]['Cost Basis of Sold (INR)'] += record['Cost Basis (INR)']
                crypto_stats[crypto]['Total Proceeds (INR)'] += record['Proceeds (INR)']
                crypto_stats[crypto]['Total P&L (INR)'] += record['P&L (INR)']

            crypto_stats[crypto]['Total Fees (INR)'] += record['Fees (INR)']
            crypto_stats[crypto]['Total TDS (INR)'] += record['TDS (INR)']
        
        # Add remaining holdings
        remaining_holdings = self.inventory.get_all_holdings()
        for crypto, qty in remaining_holdings.items():
            crypto_stats[crypto]['Remaining Holdings'] = qty
        
        # Convert to DataFrame
        summary_df = pd.DataFrame.from_dict(crypto_stats, orient='index')
        summary_df.index.name = 'Crypto'
        summary_df = summary_df.reset_index()
        
        # Sort by Total P&L descending (only if data exists)
        if len(summary_df) > 0 and 'Total P&L (INR)' in summary_df.columns:
            summary_df = summary_df.sort_values('Total P&L (INR)', ascending=False)
        
        return summary_df
    
    def generate_overall_summary(self) -> pd.DataFrame:
        """Generate overall P&L summary"""
        total_pnl = sum(r['P&L (INR)'] for r in self.pnl_records if r['Side'] == 'SELL')
        total_tds = sum(r['TDS (INR)'] for r in self.pnl_records)
        total_fees = sum(r['Fees (INR)'] for r in self.pnl_records)
        num_transactions = len(self.pnl_records)
        num_buys = sum(1 for r in self.pnl_records if r['Side'] == 'BUY')
        num_sells = sum(1 for r in self.pnl_records if r['Side'] == 'SELL')
        
        # Determine financial year from transactions
        fy_label = "N/A"
        date_range = "N/A"
        
        if self.transactions:
            dates = [t.date for t in self.transactions]
            min_date = min(dates)
            max_date = max(dates)
            
            # Indian FY: April 1 to March 31
            if min_date.month >= 4:
                fy_start_year = min_date.year
            else:
                fy_start_year = min_date.year - 1
            
            if max_date.month >= 4:
                fy_end_year = max_date.year + 1
            else:
                fy_end_year = max_date.year
            
            fy_label = f"FY {fy_start_year}-{str(fy_end_year)[2:]}"
            date_range = f"{min_date.date()} to {max_date.date()}"
        
        summary_data = {
            'Metric': [
                'Financial Year',
                'Total Realized P&L (INR)',
                'Total TDS Deducted (INR)',
                'Total Fees Paid (INR)',
                'Total Transactions',
                'Total Buy Transactions',
                'Total Sell Transactions',
                'Transaction Date Range',
                'Unique Cryptocurrencies'
            ],
            'Value': [
                fy_label,
                f"₹ {total_pnl:,.2f}",
                f"₹ {total_tds:,.2f}",
                f"₹ {total_fees:,.2f}",
                num_transactions,
                num_buys,
                num_sells,
                date_range,
                len(set(r['Crypto'] for r in self.pnl_records))
            ]
        }
        
        return pd.DataFrame(summary_data)
    
    def generate_excel_report(self, output_file: str) -> str:
        """Generate comprehensive Excel report with multiple sheets"""
        print(f"\nGenerating Excel report: {output_file}")
        
        # Convert pnl_records to DataFrame
        transactions_df = pd.DataFrame(self.pnl_records)
        
        # Generate summaries
        crypto_summary_df = self.generate_crypto_wise_summary()
        overall_summary_df = self.generate_overall_summary()
        
        # Write to Excel with multiple sheets
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: Transaction Log
            transactions_df.to_excel(writer, sheet_name='Transaction Log', index=False)
            
            # Sheet 2: Crypto-wise Summary
            crypto_summary_df.to_excel(writer, sheet_name='Crypto-wise Summary', index=False)
            
            # Sheet 3: Overall Summary
            overall_summary_df.to_excel(writer, sheet_name='Overall Summary', index=False)
        
        print(f"✓ Excel report generated successfully!")
        print(f"  - Transaction Log: {len(transactions_df)} records")
        print(f"  - Crypto-wise Summary: {len(crypto_summary_df)} cryptocurrencies")
        print(f"  - Overall Summary: Key metrics and totals")
        
        return output_file
    
    def run(self, output_file: Optional[str] = None) -> str:
        """Main execution flow"""
        print("=" * 80)
        print("CRYPTO ASSET P&L CALCULATOR - FIFO METHOD (Section 115BBH)")
        print("=" * 80)
        
        # Load data
        instant_orders, spot_orders = self.load_data()
        
        # Parse transactions
        self.parse_instant_orders(instant_orders)
        self.parse_spot_orders(spot_orders)
        
        print(f"Total transactions parsed: {len(self.transactions)}")
        
        # Process transactions and calculate P&L
        self.process_transactions()
        
        # Generate output filename if not provided
        if output_file is None:
            # Determine FY from transactions
            if self.transactions:
                dates = [t.date for t in self.transactions]
                min_date = min(dates)
                if min_date.month >= 4:
                    fy_year = min_date.year
                else:
                    fy_year = min_date.year - 1
                output_file = f"crypto_pnl_report_FY{fy_year}-{str(fy_year+1)[2:]}.xlsx"
            else:
                output_file = "crypto_pnl_report.xlsx"
        
        # Generate report
        self.generate_excel_report(output_file)
        
        # Display summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        crypto_summary = self.generate_crypto_wise_summary()
        overall_summary = self.generate_overall_summary()
        
        print("\nCrypto-wise P&L:")
        print(crypto_summary.to_string(index=False))
        
        print("\n\nOverall Summary:")
        print(overall_summary.to_string(index=False))
        
        print("\n" + "=" * 80)
        print(f"Report saved to: {output_file}")
        print("=" * 80)
        
        return output_file


def main():
    """Main entry point"""
    import sys
    
    # Check if file path is provided
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        excel_file = 'crypto_transactions.xlsx'
    
    # Check if output file is provided
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = None
    
    try:
        # Create calculator and run
        calculator = CryptoPnLCalculator(excel_file)
        calculator.run(output_file)
        
    except FileNotFoundError:
        print(f"Error: File '{excel_file}' not found!")
        print("Usage: python crypto_pnl_calculator.py <excel_file> [output_file]")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
