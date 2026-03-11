#!/usr/bin/env python3
"""
Crypto Asset P&L Calculator for Indian VDA Taxation (Section 115BBH)
Implements FIFO inventory accounting for crypto transactions

Author: Crypto Trade P&L System
Date: 2026-03-11
"""

import pandas as pd
from datetime import datetime
from collections import deque, defaultdict
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


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
        """
        if crypto not in self.holdings or not self.holdings[crypto]:
            raise ValueError(f"No holdings available for {crypto}")
        
        total_cost_basis = 0.0
        disposals = []
        remaining_to_dispose = quantity_to_dispose
        
        while remaining_to_dispose > 0.00000001:  # Small threshold for floating point
            if not self.holdings[crypto]:
                raise ValueError(f"Insufficient holdings for {crypto}. Trying to sell {remaining_to_dispose} more.")
            
            oldest_holding = self.holdings[crypto][0]
            available_qty = oldest_holding['quantity']
            
            if available_qty <= remaining_to_dispose:
                # Use entire oldest holding
                cost = available_qty * oldest_holding['cost_per_unit']
                total_cost_basis += cost
                disposals.append({
                    'quantity': available_qty,
                    'cost_per_unit': oldest_holding['cost_per_unit'],
                    'cost': cost,
                    'acquisition_date': oldest_holding['date']
                })
                remaining_to_dispose -= available_qty
                self.holdings[crypto].popleft()
            else:
                # Use partial holding
                cost = remaining_to_dispose * oldest_holding['cost_per_unit']
                total_cost_basis += cost
                disposals.append({
                    'quantity': remaining_to_dispose,
                    'cost_per_unit': oldest_holding['cost_per_unit'],
                    'cost': cost,
                    'acquisition_date': oldest_holding['date']
                })
                oldest_holding['quantity'] -= remaining_to_dispose
                remaining_to_dispose = 0
        
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
    
    def parse_instant_orders(self, df: pd.DataFrame):
        """Parse Instant Orders (all INR-based)"""
        print("Parsing Instant Orders...")
        
        for _, row in df.iterrows():
            try:
                date = pd.to_datetime(row['Trade Completion time'])
                crypto = str(row['Crypto']).strip()
                side = str(row['Side (Buy/Sell)']).strip().upper()
                quantity = float(row['Quantity'])
                price_per_unit = float(row['Avg Buying/Selling Price(in INR)'])
                gross_amount = float(row['Gross Amount Paid/Received by the user(in INR)'])
                fees = float(row['Fees(in INR)']) if pd.notna(row['Fees(in INR)']) else 0.0
                tds = float(row['*TDS(in INR)']) if pd.notna(row['*TDS(in INR)']) else 0.0
                
                txn = Transaction(
                    date=date,
                    crypto=crypto,
                    side=side,
                    quantity=quantity,
                    price_per_unit=price_per_unit,
                    gross_amount=gross_amount,
                    fees=fees,
                    tds=tds,
                    description=f"Instant Order - {crypto} {side}"
                )
                self.transactions.append(txn)
            except Exception as e:
                print(f"Error parsing instant order row: {e}")
                continue
    
    def parse_spot_orders(self, df: pd.DataFrame):
        """Parse Spot Orders (INR and USDT pairs)"""
        print("Parsing Spot Orders...")
        
        for _, row in df.iterrows():
            try:
                date = pd.to_datetime(row['Trade Completion time'])
                crypto_pair = str(row['Crypto Pair']).strip()
                base_currency = str(row['Base currency']).strip()
                side = str(row['Side (Buy/Sell)']).strip().upper()
                quantity = float(row['Quantity'])
                price_per_unit = float(row['Avg Buying/Selling Price(in base currency)'])
                gross_amount_base = float(row['Gross Amount Paid/Received by the user(in base currency)'])
                fees_base = float(row['Fees(in base currency)']) if pd.notna(row['Fees(in base currency)']) else 0.0
                
                # Get INR equivalent
                gross_amount_inr = float(row['*Net Amount Paid/Received by the user (in INR)']) if pd.notna(row['*Net Amount Paid/Received by the user (in INR)']) else None
                tds_inr = float(row['**TDS (in INR)']) if pd.notna(row['**TDS (in INR)']) else 0.0
                
                # Extract target crypto from pair
                if crypto_pair.endswith('INR'):
                    # INR pair - direct transaction
                    target_crypto = crypto_pair.replace('INR', '')
                    
                    txn = Transaction(
                        date=date,
                        crypto=target_crypto,
                        side=side,
                        quantity=quantity,
                        price_per_unit=price_per_unit,
                        gross_amount=gross_amount_base,  # Already in INR
                        fees=fees_base,
                        tds=tds_inr,
                        description=f"Spot Order - {crypto_pair} {side}"
                    )
                    self.transactions.append(txn)
                    
                elif crypto_pair.endswith('USDT'):
                    # USDT pair - needs transformation
                    target_crypto = crypto_pair.replace('USDT', '')
                    
                    # Calculate INR equivalent per unit
                    if gross_amount_inr is not None and gross_amount_inr > 0:
                        inr_equivalent = gross_amount_inr
                    else:
                        # Fallback: use approximate conversion if INR value not available
                        inr_equivalent = gross_amount_base * 90  # Approximate USDT rate
                    
                    if side == 'BUY':
                        # xxxUSDT BUY => SELL USDT + BUY target crypto
                        
                        # 1. SELL USDT (disposal event)
                        usdt_txn = Transaction(
                            date=date,
                            crypto='USDT',
                            side='SELL',
                            quantity=gross_amount_base,  # USDT amount
                            price_per_unit=inr_equivalent / gross_amount_base if gross_amount_base > 0 else 0,
                            gross_amount=inr_equivalent,
                            fees=0.0,  # Fees handled separately
                            tds=0.0,
                            description=f"Implicit USDT disposal from {crypto_pair} BUY"
                        )
                        self.transactions.append(usdt_txn)
                        
                        # 2. BUY target crypto
                        target_txn = Transaction(
                            date=date,
                            crypto=target_crypto,
                            side='BUY',
                            quantity=quantity,
                            price_per_unit=inr_equivalent / quantity if quantity > 0 else 0,
                            gross_amount=inr_equivalent,
                            fees=fees_base * (inr_equivalent / gross_amount_base) if gross_amount_base > 0 else 0,
                            tds=tds_inr,
                            description=f"Spot Order - {crypto_pair} BUY (bought with USDT)"
                        )
                        self.transactions.append(target_txn)
                        
                    else:  # SELL
                        # xxxUSDT SELL => SELL target crypto + BUY USDT
                        
                        # 1. SELL target crypto (disposal event)
                        target_txn = Transaction(
                            date=date,
                            crypto=target_crypto,
                            side='SELL',
                            quantity=quantity,
                            price_per_unit=inr_equivalent / quantity if quantity > 0 else 0,
                            gross_amount=inr_equivalent,
                            fees=0.0,
                            tds=tds_inr,
                            description=f"Spot Order - {crypto_pair} SELL (for USDT)"
                        )
                        self.transactions.append(target_txn)
                        
                        # 2. BUY USDT
                        usdt_txn = Transaction(
                            date=date,
                            crypto='USDT',
                            side='BUY',
                            quantity=gross_amount_base,  # USDT amount
                            price_per_unit=inr_equivalent / gross_amount_base if gross_amount_base > 0 else 0,
                            gross_amount=inr_equivalent,
                            fees=fees_base * (inr_equivalent / gross_amount_base) if gross_amount_base > 0 else 0,
                            tds=0.0,
                            description=f"Implicit USDT acquisition from {crypto_pair} SELL"
                        )
                        self.transactions.append(usdt_txn)
                
            except Exception as e:
                print(f"Error parsing spot order row: {e}")
                continue
    
    def process_transactions(self):
        """Process all transactions in chronological order and calculate P&L"""
        print(f"\nProcessing {len(self.transactions)} transactions...")
        
        # Sort by date
        self.transactions.sort(key=lambda x: x.date)
        
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
                    
                except ValueError as e:
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
            'Total Cost Basis (INR)': 0.0,
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
                crypto_stats[crypto]['Total Cost Basis (INR)'] += record['Cost Basis (INR)']
            elif record['Side'] == 'SELL':
                crypto_stats[crypto]['Total Quantity Sold'] += record['Quantity']
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
