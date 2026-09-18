# Grid Clock — your electricity price plan is not telling you about carbon

Ontario's Time-of-Use tariff charges one price, 9.8¢/kWh, for a twelve-hour off-peak window.
Inside that single price, the share of electricity coming from natural gas ranges from
**19.06 % to 25.23 %** — and the highest-gas-share hour in the cheapest bracket exceeds
**any** hour in the most expensive bracket.

The advice everyone gives — "run it after 7 p.m., it's cheaper" — opens the window at its
dirtiest end. The four dirtiest hours of those twelve are the first four after it opens.

## The one number that matters

| | Gas share of Ontario's electricity | What you pay |
|---|---:|---|
| 9 p.m. | **25.23 %** | 9.8¢ — cheapest bracket |
| 3 a.m. | **19.06 %** | 9.8¢ — same price |
| Most expensive bracket, worst hour | 24.19 % | 20.3¢ |

**No emission factor is used for this claim.** Gas share is a measured quantity; the ordering
and the 1.324× ratio hold whatever intensity you assign to a gas plant.

## Does it actually work on a given night? 82 % of them.

That table is a mean over 92 nights. "The average gain is 6.06 pp" and "you gain on a given
night" are different claims, and only the second one is advice. `src/replay.py` scores each night
separately — run at 7 p.m. as the advice says, versus run at 3 a.m. as our pick says:

| Cycle | Nights overnight wins | Median gain | Worst night | Cost vs a perfect forecast |
|---|---|---:|---:|---:|
| 1 hour | **75 / 92 (81.5 %)** | +5.31 pp | −4.08 pp | +1.22 pp |
| 2 hours | 80 / 92 (87.0 %) | +5.16 pp | −4.07 pp | +0.95 pp |
| 3 hours | 79 / 92 (85.9 %) | +5.26 pp | −3.88 pp | +0.79 pp |

**It loses on 17 nights in 92.** We would rather print that than let a judge assume the mean is
the whole story. The distribution for a one-hour load:

| worst | 10th pct | median | 90th pct | best |
|---:|---:|---:|---:|---:|
| −4.08 pp | −0.66 pp | +5.31 pp | +13.16 pp | +20.49 pp |

The shape is the point: **when it loses it loses small, and when it wins it often wins large.**
That is what makes a fixed overnight rule worth following without a forecast — not that it is
always right, because it is not. Cycles of two and three hours behave the same way, so this is not
an artefact of scoring only the start hour.

## A $12 timer captures 96.2 % of this. Here is what is left.

We were asked what we add over the next-best thing someone would actually do. We had never
measured it. `src/baseline.py` does, on 92 summer weeknights:

| What you could do | Hour | Gas share |
|---|---|---:|
| Run it at dinner, no plan | 8 p.m. | 25.11 % |
| The advice you are given: "after 7, it's cheaper" | 7 p.m. | 24.83 % |
| **A $12 plug-in timer set to 2 a.m.** | 2 a.m. | 19.27 % |
| Grid Clock's recommendation | 3 a.m. | **19.06 %** |
| A perfect per-night forecast (nobody ships this) | varies | 17.92 % |

**Our recommendation beats the timer by 0.217 pp.** That is the whole of what hour-picking adds,
and it is smaller than most people's intuition about it.
Cheaper still, most dishwashers and washing machines already have a delay-start button, so the
honest floor is zero dollars. Two things follow, and we would rather say them than have a judge
find them:

1. **Hour-picking adds almost nothing, and the ranking is not even stable.** Excluding
   four statutory holidays flips the best hour from 4 a.m. to 3 a.m.; 2 a.m. and 3 a.m. differ by
   **0.217 pp**. That is the resolution of our hour-picking. Our pick is the cleanest hour on
   only **20.7 % of nights**. A perfect forecast would beat the timer by 1.35 pp; we do not ship a
   forecast, so that 1.35 pp is not ours to claim.
2. **What is actually worth something is the 5.77 pp between evening and overnight**, which is
   **4.3× larger** than anything available inside the overnight window. Both endpoints, because
   an asynchronous judge cannot ask: **24.83 % at 7 p.m. — the hour the advice actually points
   at — minus 19.06 % at 3 a.m.** The headline 6.06 pp instead uses 8 p.m. (25.11 %), the hour
   people actually run things rather than the one they are told to use; same overnight endpoint.
   The bracket's genuinely worst hour is 9 p.m. at 25.23 %.
   A timer captures this too, *once you have decided to set one.* The default tariff is what
   stops people deciding: at 7 p.m. it quotes its cheapest price, 9.8¢, at the hour with the
   highest gas share it sells.

So this is not a scheduler. It is the measurement that gives someone a reason to set the timer,
against a tariff that argues they shouldn't.

## Exactly what was measured

A judge cannot check a claim whose population is vague, so:

- **Source**: IESO `Generator Output by Fuel Type Hourly`, public, no key. 6,144 hourly records,
  **2026-01-01 to 2026-09-13**. Committed to this repo.
- **Population**: Ontario **summer-tariff weekdays** — month in May–October, Monday–Friday,
  **excluding the ten statutory holidays on the OEB Time-of-Use holiday schedule**. That leaves
  **92 days** in range. Holidays are excluded because Ontario TOU bills them off-peak for all 24
  hours, so their bracket structure is not the one under test. The list and its source are in
  `src/ontario.py`.
- **Aggregation**: for each hour-of-day 0–23, the mean across days of
  `GAS output / total output × 100`, computed per hour then averaged — not a ratio of sums.
- **Two clocks, joined in one place.** IESO publishes hours 1–24, where hour *H* covers
  *H−1*:00 to *H*:00 **on Eastern Standard Time, which it uses all year and never shifts for
  daylight saving.** The tariff brackets are written in the customer's **local** time, which is
  EDT from March to November. Treating one as the other files every summer observation an hour
  early, and moves it across bracket boundaries: IESO hour 19 is 18:00–19:00 EST, which is
  19:00–20:00 locally — on-peak by the first reading, off-peak by the second.
  `src/parse_ieso.py` is the only place the two clocks meet. It converts once, at the source, and
  everything downstream reads local hours 0–23. Analysis scripts that reach for the raw hour fail
  a check. `src/check_time.py` holds twelve hand-computed known answers and cross-checks the
  hand-written daylight-saving rule against the standard library's tz database.
  The data confirms the convention on its own: 2026-03-08 is a spring-forward day and carries
  **24** hours, where a local-time feed would carry 23.
- **Tariff**: Toronto Hydro published rates, verified 2026-09-15. Summer TOU off-peak 19:00–07:00.

## Winter has half as much of this — and that is the point

| | Worst hour | Best hour | Spread | Misaligned hours |
|---|---|---|---|---|
| **Summer** (May 1 – Oct 31) | 9 p.m., 25.23 % | 3 a.m., 19.06 % | 1.324× | **7, 8, 9, 10 p.m.** |
| Winter (Nov 1 – Apr 30) | 8 p.m., 23.62 % | 2 a.m., 20.04 % | 1.178× | **8, 9 p.m.** |

"Misaligned" means an hour inside the cheapest bracket whose gas share exceeds the worst hour of
the most expensive bracket. Summer has four such hours; winter has two.

Winter's tariff puts on-peak in *two* blocks, 7–11 a.m. and 5–7 p.m., and the second one covers
most of the evening gas ramp. Summer has a single on-peak block, 11 a.m. to 5 p.m., and off-peak
opens at 7 p.m. precisely as gas output is still climbing.

So the tariff is not blind to evening peaks: it handles them **better** in winter, with a
narrower spread and half the misaligned hours. **It is the summer bracket structure that lets the
evening peak fall furthest into the cheapest window.** And summer rates are in effect right now,
until October 31.

An earlier version of this section said winter did not have the problem at all. That was true of
the numbers we had before the clock correction above, and it is a good illustration of why the
correction mattered: the claim that survived is narrower than the one it replaced.

## This is not a new idea — and the closest prior work is in Ontario

"Cheapest is not cleanest" has been productised and published before. **WattTime** sells
marginal-emissions signals; **Electricity Maps** publishes live grid carbon intensity;
**Google Nest** ships *Clean Energy Time-of-Day*. In the literature, shifting flexible load by
carbon intensity is **carbon-aware scheduling** — Google's
[Carbon-Aware Computing for Datacenters](https://arxiv.org/abs/2106.11750) (Radovanović et al.,
IEEE Trans. Power Systems, 2023) does it with day-ahead forecasts.

**More directly: the finding has already been made for Ontario specifically, on a stronger basis
than ours.**

- Gai, Wang, Pereira, Hatzopoulou and Posen, *Marginal Greenhouse Gas Emissions of Ontario's
  Electricity System and the Implications of Electric Vehicle Charging*
  ([TRB 98th Annual Meeting, 2019](https://trid.trb.org/view/1573057)) find that minimising GHG
  from charging calls for demand **between 1 a.m. and 7 a.m.** — i.e. overnight rather than
  evening, in Ontario, on a **marginal** basis. That is a stronger basis than our average gas
  share.
- **The Atmospheric Fund** publishes
  [Ontario electricity emissions factors](https://taf.ca/publications/electricity_emissions_factors/)
  including hourly marginal factors, and names **shifting appliance use — washing machines,
  dishwashers** — as the application. That is our exact use case.

So "run it overnight, not in the evening, in Ontario" is **established, not our discovery.** We
found this out by asking a reviewer what we might be rediscovering, and we would rather print it
than have a judge find it.

### What is actually ours

Three things, and none of them is the general phenomenon:

1. **An assumption-free metric.** The work above models *marginal* emissions, which requires a
   dispatch model and an emission factor. We report **measured gas share** and nothing else, so
   the ordering and the 1.324× ratio hold whatever intensity you assign to a gas plant. Weaker
   claim, no modelling to argue with.
2. **The unit of analysis is the tariff bracket, not the hour.** The published work asks *when is
   the grid cleanest*. We ask *what does one price hide*: a single 9.8¢ bracket spanning twelve
   hours contains a 1.324× spread, and its worst hour exceeds every hour of the dearest bracket.
3. **A negative result we did not have to publish.** Our own recommendation turns out to be the
   setting a $12 timer already has, and we say so in the first minute of the video.

That is an applied measurement and an evaluation result on 2026 data — not a new principle.

## Run it

The data file is committed, so this works straight after a clone. `src/fetch_data.py` re-fetches
it from IESO if it ever goes missing.

```bash
python3 src/parse_ieso.py data/fuel2026.xml     # parse, show annual fuel mix
python3 src/profile.py data/fuel2026.xml        # hourly profile
python3 src/compare.py data/fuel2026.xml        # TOU vs ULO vs measured gas share
python3 src/chart.py data/fuel2026.xml          # figures/chart.svg
python3 src/card.py data/fuel2026.xml 20        # figures/card.svg — decision card
python3 src/nulls.py data/fuel2026.xml          # is the misalignment chance?
python3 src/check_demo.py                       # the checks the demo path depends on
python3 src/blocknull.py data/fuel2026.xml      # does autocorrelation inflate that?
python3 src/baseline.py data/fuel2026.xml       # what do we add over a $12 timer?
python3 src/replay.py data/fuel2026.xml         # does it win on a given night, not just on average?
#                                                 full verification record: VERIFICATION.md
python3 src/sabotage.py                         # break things on purpose; do the checks notice?
python3 src/determinism.py data/fuel2026.xml    # same input, same answer? (hash-seed sweep)
```

No dependencies. Python standard library only, including the SVG output.

## What was built when

Everything here was written on **2026-09-15**, inside the contest window (2026-08-21 – 09-20).
Nothing was carried in from an earlier project. Technique did carry over — the permutation-null
ideas come from an unrelated spatial-statistics project I built earlier in this same window — but
the code did not: of 37 functions here and 41 there, three share a generic name (`load`, `main`,
`run`) and no two implementations are identical. The data is IESO's public feed, downloaded
during the window and committed so a clone runs offline.

## What we checked, and what broke

Three things changed the result rather than confirming it, and they are the reason to trust the
rest: **a permutation test's p-value was inflated by autocorrelation** (0.0005 → 0.0240 under a
circular-rotation null, a 48× move, so we lean on the mechanism rather than the p-value);
**statutory holidays were being counted as ordinary weekdays**, which moved the answer from
4 a.m. to 3 a.m.; and **the IESO feed runs on EST all year while the tariff brackets are local
time**, so every summer observation was being filed one hour early — the single largest
correction in this project, and the one that moved the recommended hour from 2 a.m. to 3 a.m.

32 checks run on the path the demo walks, at a denominator that cannot shrink. 45 defects are
planted deliberately and all are caught, and every check is targeted by at least one of them.
Every number in this file, in both figures, and in the submission documents is bound by regex to
a line of script output — parsed from what the script printed, never recomputed by the checker.

**The full record is in [VERIFICATION.md](VERIFICATION.md)** — including what the binding does
*not* do, which is to prove that a sentence describes the right statistic.

## What this does not claim

- **Not a carbon saving.** Nobody has changed behaviour because of this and we measured nobody
  who did. A lower gas share at 3 a.m. does not prove a shifted kilowatt-hour burns less gas:
  gas may well be the marginal generator at both hours. Establishing avoided emissions needs
  **marginal** intensity and shifted kWh, and we have neither. The 6.06 pp is an **opportunity
  signal, not demonstrated savings.**
- **Not a robust hour.** See above — the best-hour ranking flips on a methodology choice. The
  claim we stand behind is "overnight, not evening", not "3 a.m., not 2 a.m."
- **The headline crossover has a thin margin.** The highest-gas-share off-peak hour exceeds the highest-gas-share
  on-peak hour by **25.23 − 24.19 = 1.04 pp**. The perturbation matters, so we state it exactly:
  **holding the 19.06 % overnight minimum and the 24.19 % on-peak maximum fixed and shrinking
  only the 6.17 pp off-peak spread, the strict crossover disappears at a ~17 % reduction**
  (1.04 / 6.17). Under a different perturbation it survives — scale every hour by 0.7 about a
  common baseline and the ordering is unchanged, with the margin simply becoming 0.73 pp.
  "The crossover goes if the signal is 17 % smaller" would be underspecified, and this is the
  most fragile sentence in the README either way. It is also a constructed threshold, not the
  probability that the crossover is wrong.
- **Not better than ULO.** Ontario's Ultra-Low Overnight plan already prices the evening at
  39.1¢ and overnight at 3.9¢. It is a baseline to beat or complement, not evidence that the
  tariffs contradict each other — they are separate products and nobody is on both.
- **We model the wrong variable.** The card names a *start hour* and ignores how long the
  appliance runs. Measured: a 3-hour cycle moves the best start from 3 a.m. to 2 a.m., and
  ignoring cycle length costs **0.064 pp** — under a third of the **0.217 pp** that separates the
  hour we print from the next one. So cycle length matters less than the hour we print, but
  neither margin is large.
- **Not a live signal.** Every number here is a mean over historical hours. The card reads from a
  static profile, not from tonight's grid.
- **Not a measurement of the card itself.** We have not tested whether anyone reading it
  understands the price-versus-mix distinction better, or decides differently. That, not more
  aggregation experiments, is what would establish the product's value.
- What we do claim is narrow and measured: **price does not stand in for carbon**, and Ontario's
  default summer tariff hides a 1.324× gas-share spread inside one price.
