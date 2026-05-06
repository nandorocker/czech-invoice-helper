# Date Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional trailing date support to the Alfred keyword while preserving current list, rate, and conversion behavior.

**Architecture:** Keep Alfred and the Bash wrapper unchanged. Extend Python query parsing so `czk EUR 5.5.26` and `czk 50 EUR 5.5.26` normalize the trailing date and pass it to the existing CNB fetcher. Alfred stdout remains JSON-only for success and error states.

**Tech Stack:** Python 3 stdlib, Bash wrapper, Alfred Script Filter JSON, `plutil`.

---

## File Structure

- Modify: `czk-exchange.py`
  - Add strict date parsing helpers for Alfred mode.
  - Extend `parse_alfred_query()` to return a normalized date.
  - Include date context in Alfred subtitles.
- Verify: `alfred/czk.sh`
  - No behavior change expected.
- Verify: `alfred/info.plist`
  - No behavior change expected.

---

## Task 1: Add Strict Alfred Date Helpers

**Files:**
- Modify: `/Users/nando/code/czech-invoice-helper/czk-exchange.py`

- [ ] **Step 1: Add strict date helpers after `get_date_str()`**

Add this code after `get_date_str()`:

```python
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
```

- [ ] **Step 2: Run syntax check**

Run:

```bash
python3 -m py_compile czk-exchange.py
```

Expected: command exits with no output.

- [ ] **Step 3: Commit strict date helpers**

Run:

```bash
git add czk-exchange.py
git commit -m "feat: add strict Alfred date parsing helpers"
```

---

## Task 2: Extend Alfred Query Parsing With Dates

**Files:**
- Modify: `/Users/nando/code/czech-invoice-helper/czk-exchange.py`

- [ ] **Step 1: Replace `parse_alfred_query()` signature and body**

Replace the current `parse_alfred_query()` function with:

```python
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
```

- [ ] **Step 2: Update the Alfred branch unpacking and fetch date**

In `main()`, inside `if args.alfred:`, replace:

```python
        date_str = get_date_str(args.date)
        rates = fetch_exchange_rates(date_str)
```

with:

```python
        mode, amount, currency, query_date = parse_alfred_query(args.alfred_query)
        if mode == "invalid_date":
            alfred_error("Invalid date", "Use e.g. 5.5.26 or 2026-05-05")
            return

        date_str = query_date or get_date_str(args.date)
        rates = fetch_exchange_rates(date_str)
```

Then remove the later old line:

```python
        mode, amount, currency = parse_alfred_query(args.alfred_query)
```

- [ ] **Step 3: Run syntax check**

Run:

```bash
python3 -m py_compile czk-exchange.py
```

Expected: command exits with no output.

- [ ] **Step 4: Run parser behavior checks through Alfred wrapper**

Run:

```bash
bash alfred/czk.sh "EUR 5.5.26"
bash alfred/czk.sh "50 EUR 5.5.26"
bash alfred/czk.sh "EUR 32.13.26"
```

Expected:
- `EUR 5.5.26` returns one EUR rate item.
- `50 EUR 5.5.26` returns one CZK conversion item.
- `EUR 32.13.26` returns `Invalid date` with `valid: false`.

- [ ] **Step 5: Commit parser date support**

Run:

```bash
git add czk-exchange.py
git commit -m "feat: parse trailing dates in Alfred queries"
```

---

## Task 3: Add Date Context to Alfred Output

**Files:**
- Modify: `/Users/nando/code/czech-invoice-helper/czk-exchange.py`

- [ ] **Step 1: Add a subtitle formatter near `format_rate_title()`**

Add this function after `format_rate_title()`:

```python
def format_rate_subtitle(code: str, amount: int, rate: str, date_str: str) -> str:
    """Format an Alfred subtitle with date context."""
    return f"Rate on {date_str}: {format_rate_title(code, amount, rate)}"
```

- [ ] **Step 2: Use the dated subtitle in Alfred list, rate, and convert outputs**

Inside the `if args.alfred:` branch, replace each subtitle expression:

```python
"subtitle": f"Rate: {format_rate_title(code, amount, rate)}",
```

and:

```python
"subtitle": f"Rate: {format_rate_title(code, rate_amount, rate)}",
```

with:

```python
"subtitle": format_rate_subtitle(code, amount, rate, date_str),
```

for list and rate items, and:

```python
"subtitle": format_rate_subtitle(code, rate_amount, rate, date_str),
```

for conversion items.

- [ ] **Step 3: Run behavior checks**

Run:

```bash
python3 -m py_compile czk-exchange.py
bash alfred/czk.sh EUR
bash alfred/czk.sh "EUR 5.5.26"
bash alfred/czk.sh "50 EUR 5.5.26"
```

Expected:
- `EUR` subtitle includes today's normalized date.
- `EUR 5.5.26` subtitle includes `Rate on 05.05.2026`.
- `50 EUR 5.5.26` subtitle includes `Rate on 05.05.2026` and the item `arg` is the CZK amount.

- [ ] **Step 4: Commit dated subtitles**

Run:

```bash
git add czk-exchange.py
git commit -m "feat: show date context in Alfred results"
```

---

## Task 4: Full Date Support Verification

**Files:**
- Verify: `/Users/nando/code/czech-invoice-helper/czk-exchange.py`
- Verify: `/Users/nando/code/czech-invoice-helper/alfred/czk.sh`
- Verify: `/Users/nando/code/czech-invoice-helper/alfred/info.plist`

- [ ] **Step 1: Verify syntax and plist**

Run:

```bash
python3 -m py_compile czk-exchange.py
plutil -lint alfred/info.plist
```

Expected:
- `py_compile` exits with no output.
- `alfred/info.plist: OK`.

- [ ] **Step 2: Verify existing behavior**

Run:

```bash
bash alfred/czk.sh
bash alfred/czk.sh EUR
bash alfred/czk.sh "50 EUR"
```

Expected:
- Empty query lists currencies.
- `EUR` returns one rate item.
- `50 EUR` returns one conversion item.

- [ ] **Step 3: Verify dated behavior**

Run:

```bash
bash alfred/czk.sh "EUR 5.5.26"
bash alfred/czk.sh "50 EUR 5.5.26"
bash alfred/czk.sh "EUR 2026-05-05"
```

Expected:
- Each command returns valid Alfred JSON.
- Dated subtitles include `Rate on 05.05.2026`.
- Conversion result `arg` contains only the CZK number.

- [ ] **Step 4: Verify invalid dates**

Run:

```bash
bash alfred/czk.sh "EUR 32.13.26"
bash alfred/czk.sh "50 EUR 2026-99-99"
```

Expected:
- Each command returns `Invalid date` with `valid: false`.
- stdout contains JSON only.

- [ ] **Step 5: Manual Alfred check**

Reload the workflow in Alfred and test:

```text
czk EUR 5.5.26
czk 50 EUR 5.5.26
```

Expected:
- Alfred shows results with `Rate on 05.05.2026`.
- Selecting the conversion copies only the CZK number.

---

## Self-Review

- Spec coverage: The plan covers trailing date parsing, supported date formats, invalid date errors, dated subtitles, JSON-only stdout, wrapper preservation, plist validation, and manual Alfred testing.
- Placeholder scan: No placeholders remain.
- Type consistency: `parse_alfred_query()` returns four values after Task 2, and later tasks use the same tuple shape.
