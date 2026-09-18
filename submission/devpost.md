# Devpost body — Grid Clock

**Project name** (Devpost field 1):

> **Grid Clock**

**Project tagline** (Devpost field 2 — required; it is what shows on the gallery tile):

> **Ontario's off-peak electricity has one price. It does not have one fuel mix.**

Four were drafted. This one is GPT-6 Pro's, proposed when it was asked to choose among the
other three, and it rejected the leading candidate — *"the cheapest hour on your electricity
bill is the one that burns the most gas"* — as overclaiming on two counts our own data
confirms: twelve hours share the 9.8¢ price, so there is no single "cheapest hour"; and we
measure gas **share**, not how much gas is **burned**. The three it replaced are kept below
for the record.

| # | Drafted, not used | Why not |
|---|---|---|
| A | *The cheapest hour on your electricity bill is the one that burns the most gas.* | Two overclaims, above |
| B | *Ontario prices 9 p.m. and 3 a.m. the same. The grid does not — 25.23 % gas versus 19.06 %.* | Accurate, but two numbers is a lot for a tile |
| C | *One price, 9.8¢, for twelve hours — and a 1.324× spread in how much gas you burn inside it.* | Most precise, weakest as a hook |

---

## Inspiration

We run the washing machine late because the rate is lower then. That was never a decision
anyone made out loud. It is just what the house does.

Somewhere underneath it I had assumed cheap meant clean. Not in those words. If you had asked
me I would have said something about supply and demand, that the cheap hours are the ones with
power to spare, and that spare power is probably the clean kind. It sounds reasonable. I never
checked.

It is not true. Ontario's off-peak window opens at seven in the evening, and gas output is
still climbing at seven in the evening. The window opens at its dirtiest end: of its twelve
hours, the four with the most gas are the first four. The advice everyone repeats, run it after
seven because it is cheaper, points straight at them. Same price, more gas.

What stayed with me was not being wrong. It was how comfortable the wrong version had been.
Nobody ever told me cheap was clean. The tariff charges one price for twelve hours and leaves
the rest to you, and I filled in the flattering answer without noticing I was filling in
anything at all.

The last thing I built was the comparison that takes most of this project away from me: a $12
plug-in timer set to 2 a.m. gets within 0.217 pp of the hour I recommend. I left it in the
video. Finding that out was worth more than the finding.

## What it does

Grid Clock puts Ontario's hourly generation mix and its electricity tariff on the same axis,
and produces one sentence: **run it at 3 a.m. tonight.**

The finding:

| | Gas share of Ontario's electricity | What you pay |
|---|---:|---|
| 9 p.m. | **25.23 %** | 9.8¢ — the cheapest bracket |
| 3 a.m. | **19.06 %** | 9.8¢ — the same price |
| Dearest bracket, worst hour | 24.19 % | 20.3¢ |

**The highest-gas-share hour inside the cheapest bracket exceeds any hour inside the most
expensive one.** And the advice everyone gives — "run it after 7 p.m., it's cheaper" — points
at exactly that hour.

## Why now

Winter has half as much of this problem. Winter's tariff puts on-peak in two blocks, 7–11 a.m.
and 5–7 p.m., and the second one covers most of the evening gas ramp. **Two misaligned hours.**

Summer has a single on-peak block, 11 a.m. to 5 p.m., and off-peak opens at 7 p.m. — precisely
while gas output is still climbing. **Four misaligned hours.**

| | Worst | Best | Spread | Misaligned |
|---|---|---|---|---|
| **Summer (May 1 – Oct 31)** | 9 p.m., 25.23 % | 3 a.m., 19.06 % | **1.324×** | **4 hours** |
| Winter (Nov 1 – Apr 30) | 8 p.m., 23.62 % | 2 a.m., 20.04 % | 1.178× | 2 hours |

So the tariff is not blind to evening peaks — it catches them in winter. The summer bracket
structure lets the peak fall into the cheapest window. **Summer rates run until October 31.**

## This is not a new idea — here is what is new

WattTime, Electricity Maps and Google's Nest *Clean Energy Time-of-Day* all ship "cleanest hour"
signals. None of this is ours. Two things here are not in those products:

1. They tell you when the grid is clean. **None tell you that your own tariff points the other
   way.** The comparison here is against the price you are actually charged, bracket by bracket.
2. The claim needs **no emission factor.** Gas share is measured; every ratio and ordering
   survives whatever intensity you assign to a gas plant.

## Does it work on a given night? 82 % of them.

Everything else here is a mean over 92 nights. "The average gain is 6.06 pp" and "you gain
tonight" are different claims, and only the second one is advice. So I replayed each night
separately — 7 p.m. as the advice says, versus 3 a.m. as I recommend:

| Cycle | Nights overnight wins | Median gain | Worst night |
|---|---|---:|---:|
| 1 hour | **75 / 92 (81.5 %)** | +5.31 pp | −4.08 pp |
| 2 hours | 80 / 92 (87.0 %) | +5.16 pp | −4.07 pp |
| 3 hours | 79 / 92 (85.9 %) | +5.26 pp | −3.88 pp |

**It loses on 17 nights in 92.** Distribution for a one-hour load: worst −4.08, 10th percentile
−0.66, median +5.31, 90th percentile +13.16, best +20.49 pp.

The shape is the finding: **when it loses it loses small; when it wins it often wins large.**
That asymmetry is what makes a fixed overnight rule worth following without a forecast — not that
it is always right, because it is not. Two- and three-hour cycles behave the same, so this is not
an artefact of scoring only the start hour.

## How I built it

- **Data**: IESO `Generator Output by Fuel Type Hourly` — no key, no signup, 5.7 MB of XML.
  2026-01-01 to 09-13, **6,144 hourly records**. Committed to the repo, so a clone runs.
- **Parsing**: `xml.etree.ElementTree` streaming, standard library.
- **Tariffs**: Toronto Hydro's published rates (summer TOU; ULO for Nov 2025 – Oct 2026).
- **Population**: summer-tariff weekdays, May–Oct, Mon–Fri, **excluding the ten OEB Time-of-Use
  statutory holidays** — 92 days in range. Holidays bill off-peak all day, so their bracket
  structure is not the one under test.
- **Figures**: SVG written by hand. No matplotlib. **Zero dependencies.**
- **Testing**: a permutation test that shuffles hour labels within each day, plus block
  permutation and circular rotation to see whether autocorrelation is inflating it.

## What was built when

The rules ask that any project with prior work document what was done before versus during the
contest. Here is that accounting, and it is short:

**Everything in this repository was written on 2026-09-15, inside the contest window**
(2026-08-21 – 2026-09-20). No files predate it. Nothing was carried in from an earlier project.

The one thing that *did* carry over is **technique, not code**. Earlier in this same window I
built an unrelated spatial-statistics project, and the permutation-null and block-permutation
ideas here come from that experience — re-implemented from scratch for the time domain, which is
where I met autocorrelation for the first time. I checked rather than asserting this: of the 37
functions here and 41 there, exactly three share a name (`load`, `main`, `run` — generic), and
**no two implementations are identical** (for example `load` is 27 lines there and 8 here).

The data is IESO's public hourly fuel-mix feed, downloaded during the window and committed to
this repo so a clone runs offline.

## Challenges I faced

| Problem | Risk | Resolution |
|---|---|---|
| First permutation test gave p = 0.0005 | Autocorrelation inflates p | Re-ran with block permutation and circular rotation → **p = 0.0240, a 48× move.** Leaned on the mechanism rather than the p-value |
| Scale sweep contradicted my hypothesis | A prepared argument with no support | "Widen the window and it vanishes" was **falsified**. Only the ratio declines monotonically (1.324→1.224). Rewrote the argument |
| An 8-hour window showed a bump | Reporting a signal that isn't there | Moved the window start → it swings −4.2 to +6.4. **Alignment artefact** |
| Emission factor unverified | Headline resting on an assumption | **Removed the dependency.** Rewrote the claim on gas share |
| Three self-checks could not fail | Counting decoration as verification | Replaced with a round-trip, two known-answer cases, and a sabotage that runs the *same* null loop |
| Demo checks missed 13 of 23 sabotages | A green light that means nothing | Rewrote them: fixed denominator, argmax not membership, parse the output instead of recomputing it |
| **Feature creep** | 76 checks on a rubric with no box for them | Cut them. The suite that stayed is tied to the **demo path**: 14 then, **27 now** — every addition binds a specific claim in the README to a specific line of script output, so it grows only when a claim does |
| Never compared against the alternative | Claiming value a $12 timer already gives | Measured it. **A 2 a.m. plug-in timer captures 96.2 %.** Rewrote what the project claims to be |
| Treated statutory holidays as ordinary weekdays | A tariff label that is factually wrong on those days | Ontario TOU bills holidays off-peak for all 24 h. Excluding the four in range **flips the cleanest hour from 4 a.m. to 3 a.m.** — 2 a.m. and 3 a.m. differ by 0.217 pp, which is the real resolution of my hour-picking |
| Two verification scripts were not reproducible | **The number in my README changed between runs** | Ties in a majority vote were broken by `max(set(...))`; sets have no order and Python randomises string hashing. One window read `+7.0 g` or "cannot compare" depending on the run. Fixed with a strict-majority rule; added a hash-seed sweep and a source-level ban |
| A sabotage "caught nothing" | Concluding a live check is dead and "fixing" it | The mutation wasn't a defect — `min` over a superset returns the same argmin. **A miss means the check is dead *or* the mutation was behaviour-preserving**; you have to tell them apart |

## What I learned

**I crossed domains.** Until this project my work was spatial-ecology statistics — how clustered
a pest's host trees are across a city. Grids, latitude corrections, spatial permutation.

Electricity markets shared none of that. What a system operator publishes, how the fuel mix moves
hour to hour, why tariff brackets are drawn where they are, why average and marginal emissions
differ — all of it was new. Carrying a spatial permutation into the time domain is where I first
met autocorrelation, and where I found out it had inflated my first p-value.

**The biggest lesson**: when you hit an unverified assumption there are two roads — verify it, or
remove it. I spent an hour trying to pin down an emission factor before realising it was faster
and stronger to rewrite the claim so it did not depend on one. **An assumption you can remove is
not an assumption you should verify.**

## What's next

- A 24-hour forecast. Right now this is an eight-month average.
- Winter is measured but not shipped (1.178× spread, two misaligned hours rather than four).
- A per-night forecast. A perfect one is worth 1.35 pp over a fixed timer; a static average
  captures none of it, and my 3 a.m. pick is the cleanest hour on only **20.7 % of nights**.
- Cycle length. The card names a start hour and ignores how long the appliance runs — measured,
  that omission costs **0.064 pp**, under a third of the 0.217 pp separating the hour I print from
  the next one. **The variable I model matters less than the one I don't.**
- Something a ULO customer would want. Right now I add 0.00 pp for them — the same hour a timer already gives.

## What this does not claim

- **No carbon saved.** Nobody changed behaviour because of this and I measured nobody who did.
  A lower gas share at 3 a.m. does not prove a shifted kWh burns less gas — gas may be marginal
  at both hours. Real avoided emissions need **marginal** intensity and shifted kWh. I have
  neither, so 6.06 pp is an **opportunity signal, not demonstrated savings**.
- **No claim to beat ULO.** Ontario's Ultra-Low Overnight plan already prices the evening at
  39.1¢. It is a baseline to beat or complement — not proof that the tariffs contradict each
  other, since they are separate products and nobody is on both.
- **No claim to beat a timer.** A $12 plug-in timer at 2 a.m. gets 19.27 % gas share; my 3 a.m.
  pick gets 19.06 %. Hour-picking is worth 0.217 pp, and a timer set to 3:00 gets my hour
  exactly. I am not a better scheduler. What I have is the measurement that gives someone a
  reason to set the timer at all, against a default tariff that argues otherwise.
- What I do claim is narrow and measured: **price does not stand in for carbon**, and Ontario's
  default summer tariff hides a 1.324× gas-share spread inside a single price.

## Built with

`python` `xml` `svg` `ieso-open-data` `no-dependencies`
