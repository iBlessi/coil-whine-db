#!/usr/bin/env python3
"""validate_submissions.py — mechanical schema check for the coil whine census.

Validates every row of data/submissions.csv against schema.json (stdlib only):
  * header must match schema.json's csv_column_order exactly,
  * required fields non-empty,
  * component_type / load_context in their enums,
  * severity an integer 0-4,
  * purchase_year an integer, 2000 <= year <= current year,
  * fps_cap_changes_it one of '', 'true', 'false',
  * notes <= 280 characters,
  * submitted_date a real ISO date (YYYY-MM-DD), not in the future,
  * impossible combo: severity 0 with fps_cap_changes_it=true
    (an inaudible whine cannot audibly change),
  * source_issue empty or a positive issue number, and no issue transcribed twice,
  * no exact-duplicate rows.

Exit codes: 0 = every row valid (a header-only file is valid — the census
starts empty); 1 = at least one invalid row or structural problem.

Usage:
  python scripts/validate_submissions.py               # validate the dataset
  python scripts/validate_submissions.py --self-test   # prove the checker works
  python scripts/validate_submissions.py --csv PATH    # validate another file
"""

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema.json"
CSV_PATH = ROOT / "data" / "submissions.csv"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_schema(path=SCHEMA_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def validate(header, rows, schema, today=None):
    """Validate a parsed CSV. `rows` is a list of (line_number, row_list).

    Returns a list of error strings; empty list means valid.
    """
    today = today or dt.date.today()
    errors = []
    cols = schema["csv_column_order"]
    required = set(schema["required"])
    props = schema["properties"]
    ct_enum = props["component_type"]["enum"]
    lc_enum = props["load_context"]["enum"]
    notes_max = props["notes"]["maxLength"]
    year_min = props["purchase_year"]["minimum"]
    sev_min = props["severity"]["minimum"]
    sev_max = props["severity"]["maximum"]

    if header is None:
        return ["submissions.csv is empty — expected at least the header row"]
    if [h.strip() for h in header] != cols:
        return [
            "header mismatch:\n"
            f"  expected: {','.join(cols)}\n"
            f"  found:    {','.join(h.strip() for h in header)}"
        ]

    seen = {}
    seen_issue = {}
    issue_min = props["source_issue"]["minimum"]
    for lineno, row in rows:
        def err(msg, _n=lineno):
            errors.append(f"line {_n}: {msg}")

        if len(row) != len(cols):
            err(f"expected {len(cols)} columns, found {len(row)}")
            continue
        rec = {c: v.strip() for c, v in zip(cols, row)}

        for field in cols:
            if field in required and rec[field] == "":
                err(f"required field '{field}' is empty")

        if rec["component_type"] and rec["component_type"] not in ct_enum:
            err(f"component_type '{rec['component_type']}' not in {ct_enum}")
        if rec["load_context"] and rec["load_context"] not in lc_enum:
            err(f"load_context '{rec['load_context']}' not in {lc_enum}")

        severity = None
        if rec["severity"]:
            severity = _int_or_none(rec["severity"])
            if severity is None or not (sev_min <= severity <= sev_max):
                err(f"severity '{rec['severity']}' must be an integer {sev_min}-{sev_max}")
                severity = None

        if rec["purchase_year"]:
            year = _int_or_none(rec["purchase_year"])
            if year is None:
                err(f"purchase_year '{rec['purchase_year']}' is not a year")
            elif year < year_min:
                err(f"purchase_year {year} is before {year_min}")
            elif year > today.year:
                err(f"purchase_year {year} is in the future")

        fps_cap = rec["fps_cap_changes_it"].lower()
        if fps_cap not in ("", "true", "false"):
            err(
                f"fps_cap_changes_it '{rec['fps_cap_changes_it']}' must be "
                "'true', 'false', or empty"
            )
        if severity == 0 and fps_cap == "true":
            err(
                "impossible combo: severity 0 (inaudible) with "
                "fps_cap_changes_it=true — an inaudible whine cannot audibly change"
            )

        if len(rec["notes"]) > notes_max:
            err(f"notes is {len(rec['notes'])} characters (max {notes_max})")

        if rec["submitted_date"]:
            if not DATE_RE.match(rec["submitted_date"]):
                err(f"submitted_date '{rec['submitted_date']}' is not YYYY-MM-DD")
            else:
                try:
                    date = dt.date.fromisoformat(rec["submitted_date"])
                except ValueError:
                    err(f"submitted_date '{rec['submitted_date']}' is not a real date")
                else:
                    if date > today:
                        err(f"submitted_date {date} is in the future")

        if rec["source_issue"]:
            issue = _int_or_none(rec["source_issue"])
            if issue is None or issue < issue_min:
                err(f"source_issue '{rec['source_issue']}' must be a positive issue number or empty")
            elif issue in seen_issue:
                err(f"source_issue #{issue} is already transcribed on line {seen_issue[issue]}")
            else:
                seen_issue[issue] = lineno

        key = tuple(rec[c] for c in cols)
        if key in seen:
            err(f"exact duplicate of line {seen[key]}")
        else:
            seen[key] = lineno

    return errors


def read_csv(path):
    """Return (header, [(line_number, row), ...]); header is None for an empty file."""
    header = None
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        for i, row in enumerate(csv.reader(fh), start=1):
            if i == 1:
                header = row
            elif row and any(cell.strip() for cell in row):
                rows.append((i, row))
    return header, rows


def self_test(schema):
    """Run the checker against embedded rows with known defects; return an exit code."""
    today = dt.date(2026, 8, 12)
    cols = schema["csv_column_order"]

    def make(**overrides):
        base = {
            "component_type": "gpu",
            "brand": "ASUS",
            "model": "ROG Strix RTX 4090",
            "exact_sku": "",
            "purchase_year": "2025",
            "severity": "3",
            "load_context": "menu-uncapped-fps",
            "psu_used": "Corsair RM1000x",
            "fps_cap_changes_it": "true",
            "notes": "Zings in uncapped menus, quiet with a 120 fps cap.",
            "submitted_date": "2026-08-12",
            "source_issue": "",
        }
        base.update(overrides)
        return [base[c] for c in cols]

    failures = 0

    def check(name, rows, expect_substrings):
        nonlocal failures
        got = validate(list(cols), rows, schema, today=today)
        joined = "\n".join(got)
        missing = [s for s in expect_substrings if s not in joined]
        unexpected = bool(got) and not expect_substrings
        if missing or unexpected:
            failures += 1
            print(f"FAIL {name}")
            if missing:
                print(f"     expected substring(s) not found: {missing}")
            print(f"     validator said: {got!r}")
        else:
            print(f"ok   {name}")

    check("valid row passes", [(2, make())], [])
    check("valid severity-0 (silent unit) passes",
          [(2, make(severity="0", fps_cap_changes_it="", load_context="idle",
                    notes="Silent even ear-at-case."))], [])
    check("bad component_type", [(2, make(component_type="fan"))], ["not in"])
    check("severity out of band", [(2, make(severity="7"))], ["must be an integer 0-4"])
    check("severity not a number", [(2, make(severity="loud"))], ["must be an integer 0-4"])
    check("future purchase_year", [(2, make(purchase_year="2031"))], ["in the future"])
    check("pre-2000 purchase_year", [(2, make(purchase_year="1997"))], ["before 2000"])
    check("bad load_context", [(2, make(load_context="mining"))], ["not in"])
    check("bad fps_cap flag", [(2, make(fps_cap_changes_it="maybe"))],
          ["must be 'true', 'false', or empty"])
    check("impossible severity-0 + fps-cap combo",
          [(2, make(severity="0", fps_cap_changes_it="true"))], ["impossible combo"])
    check("notes over 280 chars", [(2, make(notes="x" * 281))], ["max 280"])
    check("bad date format", [(2, make(submitted_date="12/08/2026"))], ["not YYYY-MM-DD"])
    check("impossible date", [(2, make(submitted_date="2026-02-30"))], ["not a real date"])
    check("future date", [(2, make(submitted_date="2027-01-01"))], ["in the future"])
    check("missing required brand", [(2, make(brand=""))], ["required field 'brand' is empty"])
    check("exact duplicate rows", [(2, make()), (3, make())], ["exact duplicate of line 2"])
    check("wrong column count", [(2, make()[:-1])], [f"expected {len(cols)} columns"])
    check("valid source_issue passes", [(2, make(source_issue="12"))], [])
    check("source_issue not a number", [(2, make(source_issue="#12"))],
          ["must be a positive issue number or empty"])
    check("source_issue zero", [(2, make(source_issue="0"))],
          ["must be a positive issue number or empty"])
    check("one issue transcribed into two rows",
          [(2, make(source_issue="12")), (3, make(source_issue="12", severity="2"))],
          ["source_issue #12 is already transcribed on line 2"])

    bad_header = list(cols)
    bad_header[0] = "part_type"
    got = validate(bad_header, [], schema, today=today)
    if got and "header mismatch" in got[0]:
        print("ok   header mismatch detected")
    else:
        failures += 1
        print(f"FAIL header mismatch detected — validator said: {got!r}")

    if failures:
        print(f"self-test: {failures} case(s) FAILED")
        return 1
    print("self-test: all cases passed")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", default=str(CSV_PATH), help="CSV file to validate")
    parser.add_argument("--schema", default=str(SCHEMA_PATH), help="schema.json path")
    parser.add_argument("--self-test", action="store_true",
                        help="run the embedded defect cases instead of validating the dataset")
    args = parser.parse_args(argv)

    schema = load_schema(args.schema)
    if args.self_test:
        return self_test(schema)

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found")
        return 1
    header, rows = read_csv(csv_path)
    errors = validate(header, rows, schema)
    if errors:
        print(f"INVALID — {len(errors)} problem(s) in {csv_path}:")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"OK — {len(rows)} data row(s) valid in {csv_path} "
          "(a header-only file is a valid empty census)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
