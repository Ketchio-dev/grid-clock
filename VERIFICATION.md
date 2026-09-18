# Verification — the detailed record

The README keeps a three-line summary. This is the long version, kept out of the main writeup on
purpose: a judge should be able to find it, and should not have to read past it to reach the
finding.

## What the checks are

```bash
python3 src/check_demo.py            # 36 checks on the path the demo walks, fixed denominator
python3 src/sabotage.py              # 49 planted defects — all must be caught (~6 min)
python3 src/determinism.py data/fuel2026.xml   # same input, same answer, across 5 hash seeds
```

**Fixed denominator.** An earlier suite kept its checks inside conditionals, so a failure removed
the check rather than failing it: `10/10` became `3/9` and read as "9/9 passed". The denominator
is now a constant list and a failure can only ever move a pass to a fail.

**Every documented number is bound to a line of script output.** Not recomputed by the checker —
parsed from what the script actually printed, then compared to what the document says. A checker
that recomputes agrees with itself when both are wrong. The binding covers the README, the two
figure SVGs, and the submission documents.

**Coverage of the coverage.** Every check must be targeted by at least one planted defect. We
found 8 of 22 checks had never been targeted; closing that gap immediately exposed a real bug
(the card image was being validated against a stale file).

## Measurements that changed the argument

- **The permutation test.** A naive hour-label shuffle gave
  **permutation test gave p = 0.0005**; a **circular-rotation null** that preserves the daily
  curve's shape gave **p = 0.0240**. The rotation null is 48× weaker, which is the honest number:
  neighbouring hours are correlated (lag-1 0.933), so the shuffle's p is inflated by construction.
  We lean on the mechanism instead: tariff brackets track demand, and demand is not carbon.
- **Scale sweep.** Aggregating to coarser windows, the actionable *ratio* declines monotonically
  (1.324 → 1.224) while the count of misaligned hours does not shrink. A larger count is a
  different quantity, not a larger opportunity.
- **Alignment artefact.** An 8-hour window appeared to show a bump; moving the window start
  swings it from −4.2 to +6.4, so it is not a signal.

## Things the checks caught that we would otherwise have shipped

| | |
|---|---|
| Statutory holidays counted as ordinary weekdays | Ontario TOU bills them off-peak all day; this moved the answer from 4 a.m. to 3 a.m. |
| Two verification scripts not reproducible | Majority-vote ties broken by `max(set(...))`; Python randomises string hashing, so one window read `+7.0 g` or "cannot compare" depending on the run, and **the range quoted in the README changed between runs** |
| The card said "Mean of 96 summer weeknights" | After the holiday fix it was 92. Figures were not in the binding list |
| The check suite overwrote the deliverable | Its hour sweep wrote to `figures/card.svg`, leaving the weakest version (23:00, 38 g) in the repo instead of 20:00 (91 g) |
| Check labels attached to the wrong results | Inserting a check mid-list shifted every index after it. 25/25 stayed green throughout — a pass does not care which name it lands on |
| `check_demo` crashed when `chart.py` failed | Variables defined only inside an `if` branch; the denominator evaporated |

## Reproducibility

`align8.py` and `scale.py` labelled each aggregation window by majority vote and broke exact ties
with `max(set(...))`. A set has no iteration order, and Python randomises string hashing per
process, so the same input gave different answers across runs. Fixed by requiring a strict
majority and iterating `sorted(set(...))`. `determinism.py` re-runs every script under five
`PYTHONHASHSEED` values; `check_demo.py` rejects the pattern in source via AST — a regex scan was
tried first and false-positived on the checker's own string literals.

## Provenance detail

Everything was written on 2026-09-15, inside the contest window. The supporting comparison
against the earlier project: 37 functions here, 41 there, three shared names (`load`, `main`,
`run` — all generic), no two implementations identical (`load` is 27 lines there and 8 here).

**This establishes non-identity, not provenance.** The provenance claim rests on the file dates
and the statement above; the function comparison only rules out one specific way of being wrong.

## What the binding does not do

Regex binding proves that a displayed number matches script output. **It does not prove the
sentence describes the right statistic.** It prevents staleness, not misreading. Two of the
objections that changed this project most — that 6.06 pp needed its endpoints named, and that
"12 % smaller" needed a perturbation model — were invisible to every check here.
