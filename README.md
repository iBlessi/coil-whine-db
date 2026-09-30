# Coil Whine Census — an open, per-model distribution dataset

Community reports of coil whine — and, just as important, its **absence** — for GPUs, power
supplies, and AIO pump blocks, scored on an anchored 0–4 severity scale. One row = one physical
unit somebody owns and listened to.

The dataset is rendered as a live census page here:
**<https://techfuelhq.com/data/coil-whine-database/>**

---

## The core rule: distributions, never verdicts

Coil whine varies **unit to unit**. The same GPU model ships silent units and screaming units,
because whine depends on which inductors a board got, how they were potted, the PSU feeding them,
and the load pattern — not on the model name. A review of one unit cannot answer "does this card
whine?", and neither can this dataset.

So this dataset never publishes a per-model verdict. It publishes per-model **distributions**:
how many units were reported (`n`) and what share of them landed at each severity level. The
activation floor: **per-model n + severity distribution once a model has >=5 reports.** Below
that floor a model is listed as *collecting*, with its report count and no severity breakdown.
Since 2026-09-30 the census page also groups the graphics-card reports by GPU name across boards,
under the same floor. A GPU group mixes boards, so it is a weaker statement than a model's own
distribution and never replaces it.

One limit is named up front: reports are self-selected. Annoyed owners may be more likely to
submit, but the size and direction of that bias are not measured, so a published whine percentage
is neither a population estimate nor a guaranteed upper bound.

## Status: v0.2.2 (2026-09-26)

As of 2026-09-26, `data/submissions.csv` holds **47 rows**: 40 GPU reports and 7 power supply
reports across 44 models. Each row was transcribed from an issue-form report and names that issue
in its `source_issue` column. No model has reached the 5-report floor, so every model is still
*collecting*.

The count above is dated because every accepted report changes it; the validator prints the live
count (`python scripts/validate_submissions.py`).

The census opened on 2026-08-12 with 0 rows on purpose. A census of unit-to-unit variance cannot
be seeded from published reviews, because each review describes a single unit that is not ours to
report. Every row is a real owner reporting a real unit.

Severity-0 reports ("mine is silent") are the most valuable rows in the dataset — they are the
half of the distribution that never shows up in forum threads.

## The severity scale (anchored)

| Severity | Anchor |
|---:|---|
| **0** | Inaudible in a quiet room |
| **1** | Audible with an ear at the case |
| **2** | Audible at the desk under load |
| **3** | Audible across the room under load |
| **4** | Audible even at idle |

Score the unit at its loudest normal state. The anchors are fixed; changing them would make old
and new rows incomparable, so any future anchor change bumps the dataset's major version.

## How to submit

Two paths, both reviewed by a maintainer before anything merges:

1. **No git knowledge needed** — fill in the
   [coil whine report issue form](https://github.com/iBlessi/coil-whine-db/issues/new?template=submission.yml).
   It mirrors the schema field-for-field; a maintainer transcribes accepted reports into the CSV
   with `submitted_date` taken from the issue's creation date.
2. **The PR path** — add **one row** to [`data/submissions.csv`](data/submissions.csv) following
   [`schema.json`](schema.json), and open a pull request. The validator runs on every PR.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the acceptance and outlier checks.

## Validation

[`scripts/validate_submissions.py`](scripts/validate_submissions.py) (Python stdlib only) checks
every row against `schema.json` — column order, enums, ranges, dates, note length, impossible
combinations, exact duplicates — and exits non-zero on any invalid row:

```bash
python scripts/validate_submissions.py               # validate data/submissions.csv
python scripts/validate_submissions.py --self-test   # prove the checker catches what it claims to
```

The same check runs in CI on every pull request that touches the dataset.

## Changelog

- **0.2.2 (2026-09-26)**: issues #11 and #24 transcribed after their submitters answered the
  clarifying question (#11 corrected to a Corsair SF450 at severity 0, #24 at severity 3 as the third
  XFX MERC 319), and the new report #52 (Gigabyte RX 7600 GAMING OC 8G, severity 2). #37's answer
  names two Sapphire RX 6800 lines and waits on one more detail; #2, #16 and #17 still wait on an
  answer.
- **0.2.1 (2026-09-15)**: issues #48 and #50 transcribed after their submitters answered the
  clarifying question (#48 at severity 3 under uncapped FPS, #50 at severity 2 while gaming). Six
  reports from #2-#51 still wait on an answer.
- **0.2.0 (2026-09-14)**: optional `source_issue` column, the GitHub issue a row was transcribed
  from; the validator rejects an issue number that appears on two rows. Reports from issues #2-#51
  triaged: 41 transcribed, 8 need one more detail from the submitter, 1 duplicate.
- **0.1.1 (2026-08-13)**: first accepted report (issue #1).
- **0.1.0 (2026-08-12)**: schema, anchored severity scale, issue-form and PR intake, validator; 0 rows.

## License

The dataset is released under **Creative Commons Attribution 4.0** (see [LICENSE](LICENSE)).
Reuse it, including commercially, with attribution:

> TechFuelHQ Community Coil Whine Census (CC BY 4.0) — https://techfuelhq.com/data/coil-whine-database/
