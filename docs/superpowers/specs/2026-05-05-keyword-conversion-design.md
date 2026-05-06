# Keyword Conversion Design

## Goal

Add amount conversion to the existing Alfred keyword. Users can type `toczk 50 EUR` and copy the CZK value for invoices.

## Current Behavior

The workflow already supports these cases:

- `toczk` lists all available CNB currencies.
- `toczk EUR` shows the official CNB EUR rate.

The new behavior must keep both cases working.

## Input Rules

The keyword parser will accept two forms:

- `toczk EUR`: rate lookup for one currency.
- `toczk 50 EUR`: conversion from foreign currency to CZK.

The amount can use `.` or `,` as the decimal separator. Currency matching stays case-insensitive.

Date support remains out of scope for this step. If the user types extra tokens after amount and currency, Alfred should show a clear invalid-input item instead of guessing.

## Output Rules

For `toczk 50 EUR`, Alfred should show one result:

```text
50 EUR = 1219.00 CZK
Rate: 1 EUR = 24.380 CZK
```

Selecting the result copies only the converted CZK number, for example `1219.00`.

For currencies with CNB amount units above one, the conversion must divide by the CNB unit. Example: if CNB reports `100 HUF = 6.724 CZK`, then `500 HUF` converts as `500 * 6.724 / 100`.

## Implementation Shape

Add a small parser in `czk-exchange.py` for Alfred query strings. The wrapper will pass Alfred's raw query to Python. Python will decide whether the query means list, single rate, or amount conversion.

Keep the conversion math in Python, not `alfred/czk.sh`, so Universal Action can reuse it later.

## Error Handling

Invalid input should return Alfred JSON with one non-valid item. Examples:

- `toczk 50` -> `Enter amount and currency, e.g. 50 EUR`
- `toczk 50 EUR foo` -> `Too many arguments`
- `toczk 50 ABC` -> `Currency ABC not found`

Network and CNB fetch errors keep the existing `Error fetching rates` item.

## Tests

Use command-line checks as the first verification layer:

```bash
bash alfred/czk.sh
bash alfred/czk.sh EUR
bash alfred/czk.sh "50 EUR"
bash alfred/czk.sh "500 HUF"
plutil -lint alfred/info.plist
```

The Alfred UI check is manual: reload the workflow, type `toczk 50 EUR`, select the result, and confirm the clipboard contains the converted CZK number.
