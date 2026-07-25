"""The disclaimer must survive refactors: it is the only copy a user cannot skip."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import crypto_pnl_calculator  # noqa: E402
from crypto_pnl_calculator import DISCLAIMER, print_disclaimer  # noqa: E402


REQUIRED_PHRASES = [
    'NOT TAX ADVICE',
    'no warranty',
    'qualified tax professional',
    'You alone are responsible',
    'DISCLAIMER.md',
]


@pytest.mark.parametrize('phrase', REQUIRED_PHRASES)
def test_disclaimer_text_contains_required_phrase(phrase):
    assert phrase in DISCLAIMER


def test_print_disclaimer_writes_to_stdout(capsys):
    print_disclaimer()
    assert 'NOT TAX ADVICE' in capsys.readouterr().out


def _write_workbook(path: Path) -> None:
    """Build a minimal CoinDCX-shaped workbook: 8 filler rows, then headers."""
    instant = pd.DataFrame([
        {
            'Transaction ID': 'a1',
            'Crypto': 'BTC',
            'Transaction time': '2025-04-01 10:00:00',
            'Side (Buy/Sell)': 'Buy',
            'Avg Buying/Selling Price(in INR)': 5_000_000.0,
            'Quantity': 0.001,
            'Gross Amount Paid/Received by the user(in INR)': 5000.0,
            'Fees(in INR)': 29.5,
            'Net Amount Paid/Received by the user(in INR)': 5029.5,
            '**TDS(in INR)': None,
        },
    ])
    spot = pd.DataFrame(columns=[
        'Order ID', 'Trade ID', 'Crypto Pair', 'Base currency',
        'Trade Completion time', 'Side (Buy/Sell)',
        'Avg Buying/Selling Price(in base currency)', 'Quantity',
        'Gross Amount Paid/Received by the user(in base currency)',
        'Fees(in base currency)',
        'Net Amount Paid/Received by the user(in base currency)',
        '*Net Amount Paid/Received by the user (in INR)',
        '**TDS(in base currency)', '**TDS (in INR)',
    ])
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        for name, frame in (('Instant Orders', instant), ('Spot Orders', spot)):
            frame.to_excel(writer, sheet_name=name, index=False, startrow=8)


def test_run_prints_disclaimer_before_the_report(tmp_path, capsys):
    source = tmp_path / 'transactions.xlsx'
    _write_workbook(source)

    calculator = crypto_pnl_calculator.CryptoPnLCalculator(str(source))
    calculator.run(str(tmp_path / 'report.xlsx'))

    out = capsys.readouterr().out
    assert 'NOT TAX ADVICE' in out
    assert out.index('NOT TAX ADVICE') < out.index('CRYPTO ASSET P&L CALCULATOR')
