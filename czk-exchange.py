#!/usr/bin/env python3
"""Czech National Bank exchange rate fetcher.

Fetches currency exchange rates from the Czech National Bank (CNB).
Usage: python czk-exchange.py [-d DATE] [-c CURRENCY] [-q/--quiet] [--list]
"""

import sys
import urllib.request
import urllib.parse
import urllib.error
import json
from datetime import datetime
from typing import Optional
import subprocess
import shlex
import shutil
import argparse


CNB_BASE_URL = "https://www.cnb.cz/en/financial-markets/foreign-exchange-market/central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/daily.txt"


def get_clipboard_command() -> Optional[list[str]]:
    """Return platform-appropriate clipboard command, or None if unavailable."""
    if shutil.which("pbcopy"):
        return ["pbcopy"]
    if shutil.which("xclip"):
        return ["xclip", "-selection", "clipboard"]
    if shutil.which("xsel"):
        return ["xsel", "--clipboard"]
    return None


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard using platform-native command."""
    cmd = get_clipboard_command()
    if not cmd:
        return False
    try:
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        process.communicate(input=text.encode("utf-8"))
        return process.returncode == 0
    except Exception:
        return False


def get_date_str(date_input: Optional[str]) -> str:
    """Parse date input or return today's date in dd.mm.yyyy format."""
    if not date_input:
        return datetime.today().strftime("%d.%m.%Y")
    try:
        return datetime.strptime(date_input, "%d.%m.%Y").strftime("%d.%m.%Y")
    except ValueError:
        pass
    try:
        return datetime.strptime(date_input, "%d.%m.%y").strftime("%d.%m.%Y")
    except ValueError:
        pass
    try:
        return datetime.strptime(date_input, "%m.%d.%y").strftime("%d.%m.%Y")
    except ValueError:
        pass
    try:
        return datetime.strptime(date_input, "%m.%d.%Y").strftime("%d.%m.%Y")
    except ValueError:
        pass
    try:
        return datetime.strptime(date_input, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        print(f"Invalid date format '{date_input}'. Using today's date.")
    return datetime.today().strftime("%d.%m.%Y")


def fetch_exchange_rates(date_str: str) -> Optional[list[tuple[str, str]]]:
    """Fetch exchange rates from CNB for given date. Returns list of (code, rate)."""
    params = urllib.parse.urlencode({"date": date_str})
    url = f"{CNB_BASE_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code} {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

    rates = []
    for line in content.strip().split("\n"):
        if line.startswith("Country|") or not line.strip():
            continue
        parts = line.strip().split("|")
        if len(parts) >= 5:
            code = parts[3].strip()
            rate = parts[4].strip()
            if code and rate:
                rates.append((code, rate))

    return rates if rates else None


def find_currency(rates: list[tuple[str, str]], currency: str) -> Optional[str]:
    """Find rate for given currency code."""
    currency = currency.upper()
    for code, rate in rates:
        if code == currency:
            return rate
    return None


def get_amount(rates: list[tuple[str, str]], currency: str) -> int:
    """Get the amount unit for a currency (e.g., 1 for USD, 100 for HUF)."""
    currency = currency.upper()
    params = {"HUF": 100, "JPY": 100, "ISK": 100, "INR": 100, "IDR": 1000,
             "PHP": 100, "KRW": 100, "THB": 100, "TRY": 100}
    return params.get(currency, 1)


def print_list(rates: list[tuple[str, str]]):
    """Print all currencies in simple format."""
    for code, rate in sorted(rates):
        print(f"{code} {rate}")


def parse_amount(text: str) -> Optional[float]:
    """Parse an amount with dot or comma decimal separator."""
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def format_amount(amount: float) -> str:
    """Format user-entered amounts without unnecessary trailing zeroes."""
    return f"{amount:.2f}".rstrip("0").rstrip(".")


def alfred_error(title: str, subtitle: str = "") -> None:
    """Print a non-selectable Alfred error item."""
    item = {"title": title, "valid": "no"}
    if subtitle:
        item["subtitle"] = subtitle
    print(json.dumps({"items": [item]}))


def parse_alfred_query(query: Optional[str]) -> tuple[str, Optional[float], Optional[str]]:
    """Return (mode, amount, currency) for an Alfred query."""
    tokens = (query or "").strip().split()
    if not tokens:
        return "list", None, None
    if len(tokens) == 1:
        amount = parse_amount(tokens[0])
        if amount is not None:
            return "missing_currency", amount, None
        return "rate", None, tokens[0]
    if len(tokens) == 2:
        amount = parse_amount(tokens[0])
        if amount is None:
            return "invalid", None, None
        return "convert", amount, tokens[1]
    return "too_many", None, None


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Czech National Bank exchange rates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s -c USD              Get today's USD rate, copy to clipboard
  %(prog)s -c EUR -q          Get today's EUR rate, quiet output
  %(prog)s -d 05.05.2026 -c EUR    Get EUR rate for specific date
  %(prog)s --list             List all available currencies"""
    )
    parser.add_argument("-d", "--date", help="Date in dd.mm.yyyy format")
    parser.add_argument("-c", "--currency", help="Currency code (e.g., USD, EUR)")
    parser.add_argument("-q", "--quiet", action="store_true",
                      help="Output number only, no clipboard")
    parser.add_argument("--list", action="store_true",
                      help="List all available currencies with rates")
    parser.add_argument("--alfred", action="store_true",
                      help="Output JSON for Alfred Script Filter")

    args = parser.parse_args()

    if args.alfred:
        date_str = get_date_str(args.date)
        rates = fetch_exchange_rates(date_str)
        if not rates:
            print(json.dumps({"items": [{"title": "Error fetching rates", "valid": "no"}]}))
            return

        items = []
        # If -c flag used with a currency, show just that one; otherwise show all
        if args.currency:
            rate = find_currency(rates, args.currency)
            if not rate:
                available = ", ".join(c for c, _ in rates)
                print(json.dumps({"items": [{"title": f"Currency {args.currency} not found", "subtitle": f"Available: {available}", "valid": "no"}]}))
                return
            items.append({
                "title": f"1 {args.currency.upper()} = {rate} CZK",
                "subtitle": f"Rate: {rate} CZK",
                "arg": rate,
                "copy": rate,
                "valid": "yes",
                "uid": args.currency.upper()
            })
        else:
            # No currency specified - show all
            for code, rate in sorted(rates):
                items.append({
                    "title": f"1 {code} = {rate} CZK",
                    "subtitle": f"Rate: {rate} CZK",
                    "arg": rate,
                    "copy": rate,
                    "valid": "yes",
                    "uid": code
                })

        print(json.dumps({"items": items}))
        return

    if args.list:
        date_str = get_date_str(args.date)
        rates = fetch_exchange_rates(date_str)
        if rates:
            print_list(rates)
        else:
            print("Failed to fetch exchange rates.", file=sys.stderr)
            sys.exit(1)
        return

    if args.date or args.currency:
        date_str = get_date_str(args.date)
        currency = args.currency or ""

        if currency:
            rates = fetch_exchange_rates(date_str)
            if not rates:
                print("Failed to fetch exchange rates.", file=sys.stderr)
                sys.exit(1)

            rate = find_currency(rates, currency)
            if not rate:
                available = ", ".join(c for c, _ in rates)
                print(f"Currency '{currency}' not found. Available: {available}",
                      file=sys.stderr)
                sys.exit(1)

            if args.quiet:
                print(rate)
            else:
                amount = get_amount(rates, currency)
                print(f"1 {currency.upper()} = {rate} CZK")
                if copy_to_clipboard(rate):
                    print("Rate copied to clipboard.")

            return

        if args.date and not args.currency:
            print("Currency code required with date.", file=sys.stderr)
            sys.exit(1)

    date_str = get_date_str(None)
    print(f"Fetching CNB exchange rates for {date_str}...")

    rates = fetch_exchange_rates(date_str)
    if not rates:
        print("Failed to fetch exchange rates.", file=sys.stderr)
        sys.exit(1)

    print("Available currencies:", ", ".join(c for c, _ in sorted(rates)))

    currency = input("Enter currency code (e.g., USD): ").strip().upper()
    if not currency:
        print("No currency entered.")
        return

    rate = find_currency(rates, currency)
    if not rate:
        print(f"Currency '{currency}' not found.")
        return

    amount = get_amount(rates, currency)
    print(f"\n1 {currency.upper()} = {rate} CZK")

    if copy_to_clipboard(rate):
        print("Rate copied to clipboard.")
    else:
        print("Clipboard not available.")


if __name__ == "__main__":
    main()
