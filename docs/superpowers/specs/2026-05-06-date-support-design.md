# Date Support Design

## Goal

Add date lookup to the Alfred keyword so invoice workflows can use the CNB rate for a specific day.

## Current Behavior

The workflow now uses `czk` as the Alfred keyword. These cases must keep working:

- `czk` lists today's CNB rates.
- `czk EUR` shows today's EUR rate.
- `czk 50 EUR` converts 50 EUR to CZK using today's CNB rate.

## Input Rules

The parser will accept an optional trailing date token:

- `czk EUR 5.5.26`
- `czk 50 EUR 5.5.26`

Without a trailing date, the workflow uses today's date.

The parser treats the last token as a date only when it looks date-like. Supported date inputs reuse the CLI parser:

- `5.5.26`
- `05.05.26`
- `05.05.2026`
- `2026-05-05`

If the final token looks date-like but cannot parse, Alfred should return one non-selectable error item. The parser should not guess a different date.

## Output Rules

For a dated rate lookup, Alfred should show the normalized date in the subtitle:

```text
1 EUR = 24.380 CZK
Rate on 05.05.2026: 1 EUR = 24.380 CZK
```

For a dated conversion, Alfred should show the converted CZK amount and include the date in the subtitle:

```text
50 EUR = 1219.00 CZK
Rate on 05.05.2026: 1 EUR = 24.380 CZK
```

Selecting a dated conversion copies only the CZK number, for example `1219.00`. Selecting a dated rate lookup copies the rate number, as current rate lookup does.

## Date Detection

Use a small helper that checks whether a token could be a date before calling the existing date parser. A token is date-like when it contains either `.` or `-` and at least one digit.

The existing `get_date_str()` fallback behavior currently prints an error and returns today. Alfred date parsing must avoid that fallback for date-like invalid input. Invalid dates should produce JSON like:

```json
{"items": [{"title": "Invalid date", "subtitle": "Use e.g. 5.5.26 or 2026-05-05", "valid": false}]}
```

## Implementation Shape

Extend the Alfred query parser to return a normalized date in addition to mode, amount, and currency. The Alfred branch will pass that date to `fetch_exchange_rates()`.

The Bash wrapper and `info.plist` should not need behavior changes for date support. Alfred already passes the raw query to Python.

## Error Handling

Keep current invalid input behavior for non-date problems:

- `czk 50` -> `Enter amount and currency, e.g. 50 EUR`
- `czk 50 EUR foo` -> `Too many arguments`
- `czk 50 ABC` -> `Currency ABC not found`

Add date-specific errors:

- `czk EUR 32.13.26` -> `Invalid date`
- `czk 50 EUR 2026-99-99` -> `Invalid date`

Network and CNB errors must keep JSON-only stdout in Alfred mode.

## Tests

Use command-line checks first:

```bash
python3 -m py_compile czk-exchange.py
plutil -lint alfred/info.plist
bash alfred/czk.sh EUR
bash alfred/czk.sh "EUR 5.5.26"
bash alfred/czk.sh "50 EUR 5.5.26"
bash alfred/czk.sh "EUR 2026-05-05"
bash alfred/czk.sh "EUR 32.13.26"
```

Manual Alfred check:

- Reload the workflow.
- Run `czk EUR 5.5.26`.
- Run `czk 50 EUR 5.5.26`.
- Select the conversion result and confirm the clipboard contains only the CZK number.
