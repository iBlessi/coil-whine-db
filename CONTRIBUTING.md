# Contributing a coil whine report

**One report = one physical unit you own(ed), judged by your own ears.** Not a model you read
about, not a friend's card, not a summary of a forum thread. Severity-0 reports ("mine is
silent") are the most wanted rows in the census — without them every distribution reads worse
than reality.

## Two submission paths

1. **Issue form (no git needed)** — open a
   [coil whine report](https://github.com/iBlessi/coil-whine-db/issues/new?template=submission.yml).
   The form mirrors the schema field-for-field. A maintainer transcribes accepted reports into
   `data/submissions.csv`, using the issue's creation date as `submitted_date`.
2. **Pull request** — add **one row per unit** to `data/submissions.csv`, following
   [`schema.json`](schema.json) and the CSV column order exactly:

   ```
   component_type,brand,model,exact_sku,purchase_year,severity,load_context,psu_used,fps_cap_changes_it,notes,submitted_date
   ```

   Optional fields (`exact_sku`, `psu_used`, `fps_cap_changes_it`, `notes`) stay as empty
   strings when you have nothing to put in them. Run the validator before opening the PR:

   ```bash
   python scripts/validate_submissions.py
   ```

## The severity anchors (fixed)

| Severity | Anchor |
|---:|---|
| 0 | Inaudible in a quiet room |
| 1 | Audible with an ear at the case |
| 2 | Audible at the desk under load |
| 3 | Audible across the room under load |
| 4 | Audible even at idle |

Score the unit at its **loudest normal state**. If the whine only appears in uncapped menus,
score that state and set `load_context` to `menu-uncapped-fps`.

## How rows get accepted

Every submission — issue or PR — goes through the same two layers before it lands in the CSV:

**1. Mechanical schema check.** `scripts/validate_submissions.py` must pass: column order,
enums (`component_type`, `load_context`), `severity` an integer 0–4, `purchase_year` a real
non-future year, `notes` within 280 characters, `submitted_date` a real non-future ISO date,
no exact-duplicate rows, and no severity-0 + `fps_cap_changes_it=true` contradiction (an
inaudible whine cannot audibly change). CI runs this on every PR that touches the dataset;
a failing check blocks the merge.

**2. Maintainer review — outlier and troll checks.** git (and the issue queue) is the
moderation layer; a human looks at every row before it merges. Patterns that get a submission
rejected or held:

- **Duplicate-account patterns** — bursts of brand-new accounts filing the same model at the
  same severity in a short window, or identical `notes` text appearing across "different"
  submitters. Brigading a model's distribution is the obvious attack on a census like this,
  so burst-shaped clusters are held until they can be checked, and the hold is noted in the
  thread.
- **Impossible combinations** — a `purchase_year` earlier than the model line existed; a
  brand/component mismatch (a brand that has never shipped that component type); a severity-0
  row whose notes describe audible noise; the severity-0 + FPS-cap contradiction above.
- **Not-a-unit reports** — rows that summarize reviews, other people's threads, or "everyone
  says this model whines". The census only wants units the submitter actually heard.
- **Spam in notes** — links, promotion, or off-topic text gets the row rejected, not edited.

A maintainer may ask one clarifying question on a borderline report; unanswered borderline
reports are closed without merging, and can be resubmitted.

**3. Corrections.** A correction to an existing row (you exchanged the unit, the whine faded,
you mis-scored it) is treated exactly like a submission: open an issue or PR pointing at the
row, and the change goes through the same checks. Resubmitting the same unit updates its row
rather than adding a second one.

## What gets published

The census page at <https://techfuelhq.com/data/coil-whine-database/> publishes **per-model
n + severity distribution once a model has >=5 reports** — the activation floor. Below the
floor a model is listed as *collecting*, with no verdict. Published percentages are described
as ceilings, because annoyed owners over-report and silent units under-report.

## License

By submitting you agree that your row is published under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (see [LICENSE](LICENSE)).
