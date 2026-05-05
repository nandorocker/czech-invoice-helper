# Czech Invoice Helper - Alfred Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create Alfred workflow for `toczk` keyword to fetch ČNB exchange rates, with phased Universal Action support

**Architecture:** Python script outputs JSON for Alfred Script Filter. Alfred workflow calls script with arguments. Phase 1: basic keyword. Phase 2: Universal Action. Phase 3: expand features.

**Tech Stack:** Python 3 stdlib (urllib), Alfred Workflow (info.plist, Script Filter)

---

## File Structure

```
/Users/nando/code/czech-invoice-helper/
├── czk-exchange.py                  # Main script (existing, modified)
├── alfred/
│   ├── info.plist                 # Alfred workflow config
│   └── icon.png                  # Workflow icon (copy from old)
├── docs/
│   └── superpowers/
│       └── plans/
│           └── 2026-05-05-alfred-workflow.md  # This plan
└── .gitignore                   # Already exists
```

---

## Context

This plan assumes the branch `alfred` has been created in the repo. The workflow is the Czech Invoice Helper's Alfred integration that allows freelancers in Czechia to quickly get the official ČNB exchange rate for their invoices.

### Current State (from czk-exchange.py)
- Basic CLI: `python czk-exchange.py [-d DATE] [-c CURRENCY] [-q] [--list]`
- Uses stdlib only (urllib)
- Fetches from CNB `/daily.txt` endpoint
- Outputs plain text or number only

### Desired End State
- Alfred keyword `toczk` shows currency list in Alfred
- Click to copy rate number to clipboard
- Universal Action support (Phase 2)
- Convert selected text to CZK (Phase 3)

---

## Task 1: Create Alfred Branch and Prepare

- [ ] **Step 1: Create branch `alfred` in czech-invoice-helper repo**

```bash
cd /Users/nando/code/czech-invoice-helper
git checkout -b alfred
```

- [ ] **Step 2: Set upstream and push**

```bash
git push -u origin alfred
```

---

## Task 2: Modify czk-exchange.py for Alfred JSON Output

**Files:**
- Modify: `/Users/nando/code/czech-invoice-helper/czk-exchange.py`

- [ ] **Step 1: Add Alfred JSON output mode**

Add to argparse after other arguments:
```python
parser.add_argument("--alfred", action="store_true",
                  help="Output JSON for Alfred Script Filter")
parser.add_argument("--list", dest="list_currencies", action="store_true",
                  help="List all currencies")
```

Add to main() function, after argument parsing logic:
```python
if args.alfred:
    import json
    date_str = get_date_str(args.date)
    rates = fetch_exchange_rates(date_str)
    if not rates:
        print(json.dumps({"items": [{"title": "Error fetching rates", "valid": "no"}]}))
        return

    if args.list_currencies:
        items = []
        for code, rate in sorted(rates):
            items.append({
                "title": f"1 {code} = {rate} CZK",
                "subtitle": f"Rate: {rate} CZK",
                "arg": rate,
                "copy": rate,
                "valid": "yes",
                "uid": code
            })
    else:
        currency = args.currency or ""
        if not currency:
            print(json.dumps({"items": [{"title": "Specify currency", "valid": "no"}]}))
            return
        rate = find_currency(rates, currency)
        if not rate:
            available = ", ".join(c for c, _ in rates)
            print(json.dumps({"items": [{"title": f"Currency {currency} not found", "subtitle": f"Available: {available}", "valid": "no"}]}))
            return
        amount = get_amount(rates, currency)
        items.append({
            "title": f"1 {currency.upper()} = {rate} CZK",
            "subtitle": f"Rate: {rate} CZK",
            "arg": rate,
            "copy": rate,
            "valid": "yes",
            "uid": currency.upper()
        })

    print(json.dumps({"items": items}))
    return
```

- [ ] **Step 2: Run test to verify JSON output**

```bash
python czk-exchange.py -c USD --alfred
python czk-exchange.py --list --alfred
```

Expected: Valid JSON with "items" array

- [ ] **Step 3: Commit**

```bash
git add czk-exchange.py
git commit -m "feat: add --alfred JSON output for Alfred Script Filter"
```

---

## Task 3: Create Alfred Workflow Files

**Files:**
- Create: `/Users/nando/code/czech-invoice-helper/alfred/info.plist`
- Create: `/Users/nando/code/czech-invoice-helper/alfred/toczk.py` (wrapper script)

- [ ] **Step 1: Create `alfred/` directory**

```bash
mkdir -p /Users/nando/code/czech-invoice-helper/alfred
```

- [ ] **Step 2: Copy icon from old workflow**

```bash
cp /Users/nando/Dropbox/Preferences/Alfred/Alfred.alfredpreferences/workflows/user.workflow.055CB1F2-FC44-42A4-96E7-2FD814C04BBA/icon.png /Users/nando/code/czech-invoice-helper/alfred/
```

- [ ] **Step 3: Create `info.plist`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>bundleid</key>
	<string>com.nan.do.czk</string>
	<key>category</key>
	<string>Productivity</string>
	<key>connections</key>
	<dict>
		<key>CZK-KEYWORD</key>
		<array>
			<dict>
				<key>destinationuid</key>
				<string>SCRIPT-FILTER</string>
				<key>modifiers</key>
				<integer>0</integer>
				<key>modifiersubtext</key>
				<string></string>
				<key>vitoclose</key>
				<false/>
			</dict>
		</array>
		<key>SCRIPT-FILTER</key>
		<array>
			<dict>
				<key>destinationuid</key>
				<string>COPY-RESULT</string>
				<key>modifiers</key>
				<integer>0</integer>
				<key>modifiersubtext</key>
				<string></string>
				<key>vitoclose</key>
				<false/>
			</dict>
		</array>
		<key>COPY-RESULT</key>
		<array>
			<dict>
				<key>destinationuid</key>
				<string></string>
				<key>modifiers</key>
				<integer>0</integer>
				<key>modifiersubtext</key>
				<string></string>
				<key>vitoclose</key>
				<false/>
			</dict>
		</array>
	</dict>
	<key>createdby</key>
	<string>Nando Rossi</string>
	<key>description</key>
	<string>Get Czech National Bank exchange rates for invoices</string>
	<key>disabled</key>
	<false/>
	<key>name</key>
	<string>CZK Exchange</string>
	<key>objects</key>
	<array>
		<dict>
			<key>config</key>
			<dict>
				<key>argumenttype</key>
				<integer>1</integer>
				<key>keyword</key>
				<string>toczk</string>
				<key>subtext</key>
				<string></string>
				<key>text</key>
				<string>Get CZK exchange rate</string>
				<key>withspace</key>
				<true/>
			</dict>
			<key>type</key>
			<string>alfred.workflow.input.keyword</string>
			<key>uid</key>
			<string>CZK-KEYWORD</string>
			<key>version</key>
			<integer>1</integer>
		</dict>
		<dict>
			<key>config</key>
			<dict>
				<key>alfredversion</key>
				<string>5.0</string>
				<key>escaping</key>
				<integer>102</integer>
				<key>keyword</key>
				<string>toczk</string>
				<key>query</key>
				<string></string>
				<key>scriptargtype</key>
				<integer>1</integer>
				<key>scripttypename</key>
				<string>bash</string>
				<key>searchfields</key>
				<array/>
				<keyword>term</keyword>
				<string></string>
			</dict>
			<key>type</key>
			<string>alfred.workflow.input.scriptfilter</string>
			<key>uid</key>
			<string>SCRIPT-FILTER</string>
			<key>version</key>
			<integer>5</integer>
		</dict>
		<dict>
			<key>config</key>
			<dict>
				<key>autopaste</key>
				<false/>
				<key>clipboardtext</key>
				<string>{query}</string>
				<key>ignoredynamicplaceholders</key>
				<false/>
				<key>transient</key>
				<false/>
			</dict>
			<key>type</key>
			<string>alfred.workflow.output.clipboard</string>
			<key>uid</key>
			<string>COPY-RESULT</string>
			<key>version</key>
			<integer>3</integer>
		</dict>
	</array>
	<key>readme</key>
	<string></string>
	<key>uidata</key>
	<dict>
		<key>CZK-KEYWORD</key>
		<dict>
			<key>xpos</key>
			<real>30</real>
			<key>ypos</key>
			<real>150</real>
		</dict>
		<key>SCRIPT-FILTER</key>
		<dict>
			<key>xpos</key>
			<real>220</real>
			<key>ypos</key>
			<real>150</real>
		</dict>
		<key>COPY-RESULT</key>
		<dict>
			<key>xpos</key>
			<real>420</real>
			<key>ypos</key>
			<real>150</real>
		</dict>
	</dict>
	<key>userconfigurationconfig</key>
	<array/>
	<key>webaddress</key>
	<string>https://nan.do</string>
</dict>
</plist>
```

- [ ] **Step 4: Create wrapper script `czk.sh`**

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/../czk-exchange.py" --alfred "$@"
```

Make executable:
```bash
chmod +x /Users/nando/code/czech-invoice-helper/alfred/czk.sh
```

- [ ] **Step 5: Update Script Filter to call the wrapper**

In info.plist, update the script filter config to use:
```
/bin/bash "$SCRIPT_DIR/czk.sh" "{query}"
```

- [ ] **Step 6: Commit**

```bash
git add alfred/
git commit -m "feat: add Alfred workflow files"
```

---

## Task 4: Create Symlink, Test Workflow

- [ ] **Step 1: Delete old workflow folder**

```bash
rm -rf /Users/nando/Dropbox/Preferences/Alfred/Alfred.alfredpreferences/workflows/user.workflow.055CB1F2-FC44-42A4-96E7-2FD814C04BBA
```

- [ ] **Step 2: Create symlink**

```bash
ln -s /Users/nando/code/czech-invoice-helper/alfred /Users/nando/Dropbox/Preferences/Alfred/Alfred.alfredpreferences/workflows/user.workflow.055CB1F2-FC44-42A4-96E7-2FD814C04BBA
```

- [ ] **Step 3: Test in Alfred**

Type `toczk` to see if Alfred loads the workflow.

---

## Task 5: Test Basic Functionality

- [ ] **Step 1: Test `toczk` keyword**

In Alfred: type `toczk`
Expected: Shows list of all currencies with CZK rates

- [ ] **Step 2: Test `toczk USD`**

In Alfred: type `toczk USD`
Expected: Shows "1 USD = {rate} CZK"

- [ ] **Step 3: Test click to copy**

Click on a result
Expected: Rate number copied to clipboard

- [ ] **Step 4: Test with date**

In Alfred: type `toczk EUR 5.5.26`
Expected: Shows EUR rate for that date

---

## Task 6: Phase 1 - Cleanup and Commit

- [ ] **Step 1: Check status**

```bash
cd /Users/nando/code/czech-invoice-helper
git status
```

- [ ] **Step 2: Merge to main or keep in branch?**

Decision: Merge to main or keep in `alfred` branch?

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "feat: Alfred workflow Phase 1 - basic keyword"
git push
```

---

## Future Tasks (Not in This Plan)

### Phase 2: Universal Action
- Add Universal Action trigger
- Accept selected text like "50 EUR"
- Show conversion results

### Phase 3: Expand
- Convert CZK → other currencies
- More advanced queries
- Support both directions

---

## Plan Complete

**Plan saved to:** `docs/superpowers/plans/2026-05-05-alfred-workflow.md`

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**