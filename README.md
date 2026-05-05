# Czech Invoice Helper

Fetch daily exchange rates from the Czech National Bank (ČNB). You're a freelancer in Czechia and get paid in EUR (or USD, GBP…)? You file in CZK, so you need the official ČNB exchange rate for that date. This script fetches the daily rate from ČNB — handy to include on your invoice for reference.

## Requirements

- Python 3.x
- No external dependencies (uses stdlib only)

## Usage

```bash
# Get today's USD rate (quiet/number only)
python czk-exchange.py -c USD -q                    # → "20.853"

# Get specific date and currency
python czk-exchange.py -d 05.05.2026 -c EUR -q       # → "24.380"

# Get rate and copy to clipboard (with message)
python czk-exchange.py -c USD                        # → "1 USD = 20.853 CZK"

# List all available currencies
python czk-exchange.py --list
```

## Alfred Integration

Use `-q` flag for automation workflows:

- **Name**: CNB Exchange Rate
- **Keyword**: `czk` or custom
- **Script**: `python /path/to/czk-exchange.py -c {query} -q`

## Options

| Flag | Description |
|------|-------------|
| `-d DATE` | Date in dd.mm.yyyy format |
| `-c CODE` | Currency code (USD, EUR, etc.) |
| `-q` | Quiet mode - output number only, no clipboard |
| `--list` | List all available currencies |

## Supported Currencies

AUD, BRL, CAD, CHF, CNY, DKK, EUR, GBP, HKD, HUF, IDR, ILS, INR, ISK, JPY, KRW, MXN, MYR, NOK, NZD, PHP, PLN, RON, SEK, SGD, THB, TRY, USD, XDR, ZAR