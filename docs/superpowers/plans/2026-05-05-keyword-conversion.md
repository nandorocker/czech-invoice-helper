# Keyword Conversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `toczk 50 EUR` keyword conversion while preserving `toczk` and `toczk EUR`.

**Architecture:** Keep Alfred as a thin wrapper. `alfred/czk.sh` passes the raw query to `czk-exchange.py`, and Python parses list, rate lookup, and amount conversion modes. Conversion math uses CNB amount units through the existing `get_amount()` helper.

**Tech Stack:** Python 3 stdlib, Bash wrapper, Alfred Script Filter JSON, `plutil`.

---

## File Structure

- Modify: `czk-exchange.py`
  - Add Alfred query parsing helpers.
  - Add amount conversion JSON output.
  - Preserve existing CLI behavior.
- Modify: `alfred/czk.sh`
  - Pass Alfred's raw query through one new `--alfred-query` option.
- Verify: `alfred/info.plist`
  - No changes expected.

---

## Task 1: Add Alfred Query Parser

**Files:**
- Modify: `/Users/nando/code/czech-invoice-helper/czk-exchange.py`

- [ ] **Step 1: Add helper functions above `main()`**

Add this code after `print_list()`:

```python
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
```

- [ ] **Step 2: Run syntax check**

Run:

```bash
python3 -m py_compile czk-exchange.py
```

Expected: command exits with no output.

- [ ] **Step 3: Commit parser helpers**

Run:

```bash
git add czk-exchange.py
git commit -m "feat: parse Alfred conversion queries"
```

---

## Task 2: Wire Alfred Query Into Python

**Files:**
- Modify: `/Users/nando/code/czech-invoice-helper/czk-exchange.py`
- Modify: `/Users/nando/code/czech-invoice-helper/alfred/czk.sh`

- [ ] **Step 1: Add an argparse option for the raw Alfred query**

In `main()`, after the existing `--alfred` argument, add:

```python
    parser.add_argument("--alfred-query", help="Raw query passed by Alfred")
```

- [ ] **Step 2: Replace the Alfred branch with parsed modes**

Replace the current `if args.alfred:` block with:

```python
    if args.alfred:
        date_str = get_date_str(args.date)
        rates = fetch_exchange_rates(date_str)
        if not rates:
            print(json.dumps({"items": [{"title": "Error fetching rates", "valid": "no"}]}))
            return

        mode, amount, currency = parse_alfred_query(args.alfred_query)
        items = []

        if mode == "list":
            for code, rate in sorted(rates):
                items.append({
                    "title": f"1 {code} = {rate} CZK",
                    "subtitle": f"Rate: {rate} CZK",
                    "arg": rate,
                    "copy": rate,
                    "valid": "yes",
                    "uid": code
                })
        elif mode == "rate":
            rate = find_currency(rates, currency or "")
            if not rate:
                available = ", ".join(c for c, _ in rates)
                alfred_error(f"Currency {currency} not found", f"Available: {available}")
                return
            code = (currency or "").upper()
            items.append({
                "title": f"1 {code} = {rate} CZK",
                "subtitle": f"Rate: {rate} CZK",
                "arg": rate,
                "copy": rate,
                "valid": "yes",
                "uid": code
            })
        elif mode == "convert":
            rate = find_currency(rates, currency or "")
            if not rate:
                available = ", ".join(c for c, _ in rates)
                alfred_error(f"Currency {currency} not found", f"Available: {available}")
                return
            code = (currency or "").upper()
            unit = get_amount(rates, code)
            converted = (amount or 0) * float(rate) / unit
            converted_text = f"{converted:.2f}"
            amount_text = format_amount(amount or 0)
            items.append({
                "title": f"{amount_text} {code} = {converted_text} CZK",
                "subtitle": f"Rate: {unit} {code} = {rate} CZK",
                "arg": converted_text,
                "copy": converted_text,
                "valid": "yes",
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
```

- [ ] **Step 3: Update Alfred wrapper to pass raw query**

Replace `alfred/czk.sh` contents with:

```bash
#!/bin/bash
# Alfred workflow wrapper for czk-exchange.py
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/../czk-exchange.py" --alfred --alfred-query "$1"
```

- [ ] **Step 4: Run baseline checks**

Run:

```bash
python3 -m py_compile czk-exchange.py
bash alfred/czk.sh
bash alfred/czk.sh EUR
```

Expected:
- `py_compile` exits with no output.
- Empty query returns Alfred JSON with many currency items.
- `EUR` returns one Alfred JSON item for EUR.

- [ ] **Step 5: Commit query wiring**

Run:

```bash
git add czk-exchange.py alfred/czk.sh
git commit -m "feat: route Alfred query through parser"
```

---

## Task 3: Verify Conversion Cases

**Files:**
- Verify: `/Users/nando/code/czech-invoice-helper/czk-exchange.py`
- Verify: `/Users/nando/code/czech-invoice-helper/alfred/czk.sh`
- Verify: `/Users/nando/code/czech-invoice-helper/alfred/info.plist`

- [ ] **Step 1: Test normal conversion**

Run:

```bash
bash alfred/czk.sh "50 EUR"
```

Expected: JSON contains one item with title matching `50 EUR = ... CZK` and `arg` set to the converted CZK amount.

- [ ] **Step 2: Test decimal comma conversion**

Run:

```bash
bash alfred/czk.sh "50,5 EUR"
```

Expected: JSON contains one item with title matching `50.5 EUR = ... CZK`.

- [ ] **Step 3: Test CNB unit conversion**

Run:

```bash
bash alfred/czk.sh "500 HUF"
```

Expected: JSON subtitle contains `Rate: 100 HUF = ... CZK`, and title uses a CZK amount calculated as `500 * rate / 100`.

- [ ] **Step 4: Test invalid inputs**

Run:

```bash
bash alfred/czk.sh "50"
bash alfred/czk.sh "50 EUR foo"
bash alfred/czk.sh "50 ABC"
```

Expected:
- `50` returns `Enter amount and currency, e.g. 50 EUR` with `valid: no`.
- `50 EUR foo` returns `Too many arguments` with `valid: no`.
- `50 ABC` returns `Currency ABC not found` with `valid: no`.

- [ ] **Step 5: Validate plist**

Run:

```bash
plutil -lint alfred/info.plist
```

Expected: `alfred/info.plist: OK`.

- [ ] **Step 6: Commit final verification notes if code changed**

No commit is needed if Task 3 only verifies behavior.

---

## Task 4: Manual Alfred Check

**Files:**
- Verify: Alfred UI

- [ ] **Step 1: Reload Alfred workflow**

Reload the workflow in Alfred Preferences.

- [ ] **Step 2: Check existing keyword behavior**

In Alfred, run:

```text
toczk
toczk EUR
```

Expected:
- `toczk` lists currencies.
- `toczk EUR` shows the single EUR rate.

- [ ] **Step 3: Check conversion behavior**

In Alfred, run:

```text
toczk 50 EUR
```

Expected: Alfred shows `50 EUR = ... CZK`. Selecting the item copies only the CZK number.

---

## Self-Review

- Spec coverage: The plan covers rate lookup preservation, amount conversion, decimal comma parsing, CNB amount units, invalid input items, terminal checks, and manual Alfred verification.
- Placeholder scan: No placeholders remain.
- Type consistency: Helper names and argparse option names match across tasks.
