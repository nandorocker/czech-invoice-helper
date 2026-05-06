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
import math
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


def parse_date_strict(date_input: str) -> Optional[str]:
    """Parse supported date formats without falling back to today."""
    formats = ("%d.%m.%Y", "%d.%m.%y", "%m.%d.%y", "%m.%d.%Y", "%Y-%m-%d")
    for date_format in formats:
        try:
            return datetime.strptime(date_input, date_format).strftime("%d.%m.%Y")
        except ValueError:
            continue
    return None


def looks_like_date(text: str) -> bool:
    """Return true when text looks like a date token."""
    return any(separator in text for separator in (".", "-")) and any(char.isdigit() for char in text)


def fetch_exchange_rates(date_str: str) -> Optional[list[tuple[str, int, str]]]:
    """Fetch exchange rates from CNB for given date. Returns list of (code, amount, rate)."""
    params = urllib.parse.urlencode({"date": date_str})
    url = f"{CNB_BASE_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code} {e.reason}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

    rates = []
    for line in content.strip().split("\n"):
        if line.startswith("Country|") or not line.strip():
            continue
        parts = line.strip().split("|")
        if len(parts) >= 5:
            code = parts[3].strip()
            amount_text = parts[2].strip()
            rate = parts[4].strip()
            if code and amount_text and rate:
                try:
                    amount = int(amount_text)
                except ValueError:
                    continue
                rates.append((code, amount, rate))

    return rates if rates else None


def find_currency(rates: list[tuple[str, int, str]], currency: str) -> Optional[tuple[str, int, str]]:
    """Find rate tuple for given currency code."""
    currency = currency.upper()
    for code, amount, rate in rates:
        if code == currency:
            return code, amount, rate
    return None


def format_rate_title(code: str, amount: int, rate: str) -> str:
    """Format a CNB rate using its published amount unit."""
    return f"{amount} {code} = {rate} CZK"


def format_rate_subtitle(code: str, amount: int, rate: str, date_str: str) -> str:
    """Format an Alfred subtitle with date context."""
    return f"Rate on {date_str}: {format_rate_title(code, amount, rate)}"


def print_list(rates: list[tuple[str, int, str]]):
    """Print all currencies in simple format."""
    for code, amount, rate in sorted(rates):
        print(f"{code} {rate}")


def parse_amount(text: str) -> Optional[float]:
    """Parse an amount with dot or comma decimal separator."""
    try:
        amount = float(text.replace(",", "."))
    except ValueError:
        return None
    return amount if math.isfinite(amount) else None


def format_amount(amount: float) -> str:
    """Format user-entered amounts without unnecessary trailing zeroes."""
    text = str(amount)
    return text[:-2] if text.endswith(".0") else text


def alfred_error(title: str, subtitle: str = "") -> None:
    """Print a non-selectable Alfred error item."""
    item = {"title": title, "valid": False}
    if subtitle:
        item["subtitle"] = subtitle
    print(json.dumps({"items": [item]}))


def parse_alfred_query(query: Optional[str]) -> tuple[str, Optional[float], Optional[str], Optional[str]]:
    """Return (mode, amount, currency, date_str) for an Alfred query."""
    tokens = (query or "").strip().split()
    date_str = None

    if tokens and looks_like_date(tokens[-1]):
        date_str = parse_date_strict(tokens[-1])
        if not date_str:
            return "invalid_date", None, None, None
        tokens = tokens[:-1]

    if not tokens:
        return "list", None, None, date_str
    if len(tokens) == 1:
        amount = parse_amount(tokens[0])
        if amount is not None:
            return "missing_currency", amount, None, date_str
        return "rate", None, tokens[0], date_str
    if len(tokens) == 2:
        amount = parse_amount(tokens[0])
        if amount is None:
            return "invalid", None, None, date_str
        return "convert", amount, tokens[1], date_str
    return "too_many", None, None, date_str


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
    parser.add_argument("--alfred-query", help="Raw query passed by Alfred")

    args = parser.parse_args()

    if args.alfred:
        mode, amount, currency, query_date = parse_alfred_query(args.alfred_query)
        if mode == "invalid_date":
            alfred_error("Invalid date", "Use e.g. 5.5.26 or 2026-05-05")
            return

        date_str = query_date or get_date_str(args.date)
        rates = fetch_exchange_rates(date_str)
        if not rates:
            print(json.dumps({"items": [{"title": "Error fetching rates", "valid": False}]}))
            return

        items = []

        if mode == "list":
            for code, amount, rate in sorted(rates):
                items.append({
                    "title": format_rate_title(code, amount, rate),
                    "subtitle": format_rate_subtitle(code, amount, rate, date_str),
                    "arg": rate,
                    "valid": True,
                    "uid": code
                })
        elif mode == "rate":
            match = find_currency(rates, currency or "")
            if not match:
                available = ", ".join(c for c, _, _ in rates)
                alfred_error(f"Currency {currency} not found", f"Available: {available}")
                return
            code, amount, rate = match
            items.append({
                "title": format_rate_title(code, amount, rate),
                "subtitle": format_rate_subtitle(code, amount, rate, date_str),
                "arg": rate,
                "valid": True,
                "uid": code
            })
        elif mode == "convert":
            match = find_currency(rates, currency or "")
            if not match:
                available = ", ".join(c for c, _, _ in rates)
                alfred_error(f"Currency {currency} not found", f"Available: {available}")
                return
            code, rate_amount, rate = match
            converted = (amount or 0) * float(rate) / rate_amount
            converted_text = f"{converted:.2f}"
            amount_text = format_amount(amount or 0)
            items.append({
                "title": f"{amount_text} {code} = {converted_text} CZK",
                "subtitle": format_rate_subtitle(code, rate_amount, rate, date_str),
                "arg": converted_text,
                "valid": True,
                "uid": f"{amount_text}-{code}"
            })
        elif mode == "missing_currency":
            alfred_error("Enter amount and currency, e.g. 50 EUR")
            return
        elif mode == "too_many":
            alfred_error("Too many arguments", "Use e.g. 50 EUR")
            return
        else:
            alfred_error("Invalid input", "Use a currency code or amount and currency")
            return

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

            match = find_currency(rates, currency)
            if not match:
                available = ", ".join(c for c, _, _ in rates)
                print(f"Currency '{currency}' not found. Available: {available}",
                      file=sys.stderr)
                sys.exit(1)
            code, amount, rate = match

            if args.quiet:
                print(rate)
            else:
                print(format_rate_title(code, amount, rate))
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

    print("Available currencies:", ", ".join(c for c, _, _ in sorted(rates)))

    currency = input("Enter currency code (e.g., USD): ").strip().upper()
    if not currency:
        print("No currency entered.")
        return

    match = find_currency(rates, currency)
    if not match:
        print(f"Currency '{currency}' not found.")
        return

    code, amount, rate = match
    print(f"\n{format_rate_title(code, amount, rate)}")

    if copy_to_clipboard(rate):
        print("Rate copied to clipboard.")
    else:
        print("Clipboard not available.")


if __name__ == "__main__":
    main()
