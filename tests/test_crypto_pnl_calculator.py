"""Tests for the crypto P&L calculator."""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crypto_pnl_calculator import (  # noqa: E402
    CryptoPnLCalculator,
    FIFOInventory,
    InsufficientHoldingsError,
    MissingColumnError,
    resolve_symbol,
)


# --------------------------------------------------------------------------
# Column resolution across CoinDCX export variants
# --------------------------------------------------------------------------

INSTANT_LEGACY = {
    'Trade ID': 'x1',
    'Crypto': 'USDT',
    'Trade Completion time': '2025-09-03 07:45:41',
    'Side (Buy/Sell)': 'Buy',
    'Avg Buying/Selling Price(in INR)': REDACTED,
    'Quantity': REDACTED,
    'Gross Amount Paid/Received by the user(in INR)': 10000.0,
    'Fees(in INR)': 59.0,
    'Net Amount Paid/Received by the user(in INR)': 10059.0,
    '*TDS(in INR)': None,
}

INSTANT_CURRENT = {
    'Transaction ID': 'x1',
    'Crypto': 'USDT',
    'Transaction time': '2025-09-03 07:45:41',
    'Side (Buy/Sell)': 'Buy',
    'Avg Buying/Selling Price(in INR)': REDACTED,
    'Quantity': REDACTED,
    'Gross Amount Paid/Received by the user(in INR)': 10000.0,
    'Fees(in INR)': 59.0,
    'Net Amount Paid/Received by the user(in INR)': 10059.0,
    '**TDS(in INR)': None,
}


def _calc():
    return CryptoPnLCalculator('unused.xlsx')


@pytest.mark.parametrize('row', [INSTANT_LEGACY, INSTANT_CURRENT], ids=['legacy', 'current'])
def test_instant_orders_parse_both_header_variants(row):
    calc = _calc()
    calc.parse_instant_orders(pd.DataFrame([row]))

    assert len(calc.transactions) == 1
    txn = calc.transactions[0]
    assert txn.crypto == 'USDT'
    assert txn.side == 'BUY'
    assert txn.quantity == pytest.approx(REDACTED)
    assert txn.gross_amount == pytest.approx(10000.0)
    assert txn.fees == pytest.approx(59.0)


def test_missing_required_column_raises_instead_of_silently_dropping_rows():
    row = dict(INSTANT_CURRENT)
    del row['Transaction time']
    with pytest.raises(MissingColumnError):
        _calc().parse_instant_orders(pd.DataFrame([row]))


def test_unparseable_row_raises_rather_than_being_skipped():
    row = dict(INSTANT_CURRENT)
    row['Quantity'] = 'not-a-number'
    with pytest.raises(ValueError):
        _calc().parse_instant_orders(pd.DataFrame([row]))


# --------------------------------------------------------------------------
# Trading pair -> symbol
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    'pair,base,expected',
    [
        ('BTC-USDT', 'USDT', 'BTC'),
        ('ETH-USDT', 'USDT', 'ETH'),
        ('ZBCNUSDT', 'USDT', 'ZBCN'),
        ('SOLINR', 'INR', 'SOL'),
        ('BTC/USDT', 'USDT', 'BTC'),
        ('BTC_USDT', 'USDT', 'BTC'),
        ('USDTINR', 'INR', 'USDT'),
        ('btc-usdt', 'usdt', 'BTC'),
        ('BTCUSDT', None, 'BTC'),
    ],
)
def test_resolve_symbol(pair, base, expected):
    assert resolve_symbol(pair, base) == (expected, (base or 'USDT').upper())


def test_resolve_symbol_rejects_unknown_quote():
    with pytest.raises(ValueError):
        resolve_symbol('BTCXYZ', None)


# --------------------------------------------------------------------------
# FIFO inventory
# --------------------------------------------------------------------------

def test_fifo_disposes_oldest_lots_first():
    inv = FIFOInventory()
    inv.add_holding('BTC', 1.0, 100.0, datetime(2025, 1, 1))
    inv.add_holding('BTC', 1.0, 200.0, datetime(2025, 2, 1))

    cost, disposals = inv.dispose_holding('BTC', 1.5)

    assert cost == pytest.approx(100.0 + 0.5 * 200.0)
    assert [d['quantity'] for d in disposals] == pytest.approx([1.0, 0.5])
    assert inv.get_remaining_holdings('BTC') == pytest.approx(0.5)


def test_insufficient_holdings_leaves_inventory_untouched():
    inv = FIFOInventory()
    inv.add_holding('USDT', 100.0, 90.0, datetime(2025, 1, 1))

    with pytest.raises(InsufficientHoldingsError):
        inv.dispose_holding('USDT', 150.0)

    # The failed disposal must not have consumed the existing lot.
    assert inv.get_remaining_holdings('USDT') == pytest.approx(100.0)


def test_no_holdings_leaves_inventory_untouched():
    inv = FIFOInventory()
    with pytest.raises(InsufficientHoldingsError):
        inv.dispose_holding('USDT', 1.0)
    assert inv.get_remaining_holdings('USDT') == pytest.approx(0.0)


# --------------------------------------------------------------------------
# Spot orders / USDT pair transformation
# --------------------------------------------------------------------------

def _spot_row(**overrides):
    row = {
        'Order ID': 'o1',
        'Trade ID': 't1',
        'Crypto Pair': 'ETH-USDT',
        'Base currency': 'USDT',
        'Trade Completion time': '2025-09-06 14:59:05',
        'Side (Buy/Sell)': 'buy',
        'Avg Buying/Selling Price(in base currency)': 4295.0,
        'Quantity': 0.01,
        'Gross Amount Paid/Received by the user(in base currency)': 42.95,
        'Fees(in base currency)': 0.0859,
        'Net Amount Paid/Received by the user(in base currency)': REDACTED,
        '*Net Amount Paid/Received by the user (in INR)': REDACTED,
        '**TDS(in base currency)': 0.4295,
        '**TDS (in INR)': REDACTED,
    }
    row.update(overrides)
    return row


def test_inr_pair_is_a_single_transaction():
    calc = _calc()
    calc.parse_spot_orders(pd.DataFrame([_spot_row(
        **{
            'Crypto Pair': 'SOLINR',
            'Base currency': 'INR',
            'Avg Buying/Selling Price(in base currency)': 18650.0,
            'Quantity': 0.0414,
            'Gross Amount Paid/Received by the user(in base currency)': 772.11,
            'Fees(in base currency)': REDACTED,
            'Net Amount Paid/Received by the user(in base currency)': REDACTED,
            '*Net Amount Paid/Received by the user (in INR)': REDACTED,
            '**TDS(in base currency)': None,
            '**TDS (in INR)': None,
        }
    )]))

    assert len(calc.transactions) == 1
    txn = calc.transactions[0]
    assert (txn.crypto, txn.side) == ('SOL', 'BUY')
    assert txn.gross_amount == pytest.approx(772.11)
    assert txn.fees == pytest.approx(REDACTED)


def test_usdt_buy_splits_into_usdt_disposal_and_crypto_acquisition():
    calc = _calc()
    calc.parse_spot_orders(pd.DataFrame([_spot_row()]))

    assert len(calc.transactions) == 2
    usdt_leg = next(t for t in calc.transactions if t.crypto == 'USDT')
    eth_leg = next(t for t in calc.transactions if t.crypto == 'ETH')

    rate = REDACTED / REDACTED

    # USDT actually leaving the wallet is the NET amount (gross + fee).
    assert usdt_leg.side == 'SELL'
    assert usdt_leg.quantity == pytest.approx(REDACTED)
    assert usdt_leg.gross_amount == pytest.approx(REDACTED)

    # Cost basis of the acquired crypto is the GROSS INR value, fees excluded
    # (Section 115BBH: fees are not part of cost of acquisition).
    assert eth_leg.side == 'BUY'
    assert eth_leg.quantity == pytest.approx(0.01)
    assert eth_leg.gross_amount == pytest.approx(42.95 * rate)
    assert eth_leg.fees == pytest.approx(0.0859 * rate)


def test_tds_is_attributed_to_the_disposal_leg():
    calc = _calc()
    calc.parse_spot_orders(pd.DataFrame([_spot_row()]))

    usdt_leg = next(t for t in calc.transactions if t.crypto == 'USDT')
    eth_leg = next(t for t in calc.transactions if t.crypto == 'ETH')

    # Buying ETH with USDT is a *disposal of USDT* - TDS belongs there.
    assert usdt_leg.tds == pytest.approx(REDACTED)
    assert eth_leg.tds == pytest.approx(0.0)


def test_usdt_sell_splits_into_crypto_disposal_and_usdt_acquisition():
    calc = _calc()
    calc.parse_spot_orders(pd.DataFrame([_spot_row(
        **{
            'Crypto Pair': 'ZBCNUSDT',
            'Side (Buy/Sell)': 'sell',
            'Avg Buying/Selling Price(in base currency)': 0.004165,
            'Quantity': 2500.0,
            'Gross Amount Paid/Received by the user(in base currency)': REDACTED,
            'Fees(in base currency)': 0.020825,
            'Net Amount Paid/Received by the user(in base currency)': REDACTED,
            '*Net Amount Paid/Received by the user (in INR)': REDACTED,
            '**TDS(in base currency)': REDACTED,
            '**TDS (in INR)': REDACTED,
        }
    )]))

    assert len(calc.transactions) == 2
    zbcn_leg = next(t for t in calc.transactions if t.crypto == 'ZBCN')
    usdt_leg = next(t for t in calc.transactions if t.crypto == 'USDT')

    rate = REDACTED / REDACTED

    assert zbcn_leg.side == 'SELL'
    assert zbcn_leg.gross_amount == pytest.approx(REDACTED * rate)
    assert zbcn_leg.tds == pytest.approx(REDACTED)

    assert usdt_leg.side == 'BUY'
    assert usdt_leg.quantity == pytest.approx(REDACTED)
    assert usdt_leg.gross_amount == pytest.approx(REDACTED)
    assert usdt_leg.tds == pytest.approx(0.0)


# --------------------------------------------------------------------------
# End-to-end P&L
# --------------------------------------------------------------------------

def test_pnl_uses_gross_amounts_on_both_sides():
    calc = _calc()
    calc.parse_instant_orders(pd.DataFrame([
        dict(INSTANT_CURRENT, **{
            'Crypto': 'BTC',
            'Transaction time': '2025-04-01 10:00:00',
            'Side (Buy/Sell)': 'Buy',
            'Quantity': 0.001,
            'Avg Buying/Selling Price(in INR)': 5_000_000.0,
            'Gross Amount Paid/Received by the user(in INR)': 5000.0,
            'Fees(in INR)': 29.5,
            'Net Amount Paid/Received by the user(in INR)': 5029.5,
        }),
        dict(INSTANT_CURRENT, **{
            'Crypto': 'BTC',
            'Transaction time': '2025-05-01 10:00:00',
            'Side (Buy/Sell)': 'Sell',
            'Quantity': 0.001,
            'Avg Buying/Selling Price(in INR)': 6_000_000.0,
            'Gross Amount Paid/Received by the user(in INR)': 6000.0,
            'Fees(in INR)': 35.4,
            'Net Amount Paid/Received by the user(in INR)': 5964.6,
            '**TDS(in INR)': 6.0,
        }),
    ]))
    calc.process_transactions()

    sells = [r for r in calc.pnl_records if r['Side'] == 'SELL']
    assert len(sells) == 1
    assert sells[0]['Cost Basis (INR)'] == pytest.approx(5000.0)
    assert sells[0]['Proceeds (INR)'] == pytest.approx(6000.0)
    assert sells[0]['P&L (INR)'] == pytest.approx(1000.0)
    assert calc.inventory.get_remaining_holdings('BTC') == pytest.approx(0.0)


def test_crypto_summary_separates_purchase_cost_from_cost_of_sold():
    calc = _calc()
    calc.parse_instant_orders(pd.DataFrame([
        dict(INSTANT_CURRENT, **{
            'Crypto': 'BTC', 'Transaction time': '2025-04-01 10:00:00',
            'Side (Buy/Sell)': 'Buy', 'Quantity': 0.002,
            'Gross Amount Paid/Received by the user(in INR)': 10000.0,
            'Fees(in INR)': 0.0,
        }),
        dict(INSTANT_CURRENT, **{
            'Crypto': 'BTC', 'Transaction time': '2025-05-01 10:00:00',
            'Side (Buy/Sell)': 'Sell', 'Quantity': 0.001,
            'Gross Amount Paid/Received by the user(in INR)': 6000.0,
            'Fees(in INR)': 0.0,
        }),
    ]))
    calc.process_transactions()

    summary = calc.generate_crypto_wise_summary().set_index('Crypto')
    btc = summary.loc['BTC']

    assert btc['Total Purchase Cost (INR)'] == pytest.approx(10000.0)
    assert btc['Cost Basis of Sold (INR)'] == pytest.approx(5000.0)
    assert btc['Total Proceeds (INR)'] == pytest.approx(6000.0)
    assert btc['Total P&L (INR)'] == pytest.approx(1000.0)
    assert btc['Remaining Holdings'] == pytest.approx(0.001)
    # Sheet must be internally consistent.
    assert btc['Total P&L (INR)'] == pytest.approx(
        btc['Total Proceeds (INR)'] - btc['Cost Basis of Sold (INR)']
    )


def test_oversell_records_error_row_and_preserves_inventory():
    calc = _calc()
    calc.parse_instant_orders(pd.DataFrame([
        dict(INSTANT_CURRENT, **{
            'Crypto': 'BTC', 'Transaction time': '2025-04-01 10:00:00',
            'Side (Buy/Sell)': 'Buy', 'Quantity': 0.001,
            'Gross Amount Paid/Received by the user(in INR)': 5000.0,
        }),
        dict(INSTANT_CURRENT, **{
            'Crypto': 'BTC', 'Transaction time': '2025-05-01 10:00:00',
            'Side (Buy/Sell)': 'Sell', 'Quantity': 0.005,
            'Gross Amount Paid/Received by the user(in INR)': 30000.0,
        }),
    ]))
    calc.process_transactions()

    assert calc.pnl_records[-1]['Transaction Type'] == 'SELL (ERROR)'
    # The lot must survive so later, valid sells still have a cost basis.
    assert calc.inventory.get_remaining_holdings('BTC') == pytest.approx(0.001)
