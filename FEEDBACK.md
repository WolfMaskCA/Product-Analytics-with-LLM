# Open feedback

Review notes not yet actioned. Delete each section once it lands.

---

## Trial-conversion story arc

**Raised by** Adrian, 2026-08-24 · **Status** open · **Area** views 1 and 2

Target shape, not a spec. Pick the exact figures to suit the generator.

### What is there now

| | value |
|---|---|
| Baseline trial-to-paid | 23.75% (pre-period headline 24.91%) |
| Industry band, ≤3 days | q1 18.0 · **median 25.0** · q3 38.0 |
| Change A, 14-day trial | 31.96% |
| Change B, late paywall | 30.63% |

### The problem

The baseline lands on the median — 23.75 against 25.0. There is no visible hole,
so the arc reads *"we were average, then we got a bit better."* That is the least
persuasive version of this demo, and it makes the stage-2 proposals look
disproportionate to the problem they solve.

### What to change

1. **Start well below the band** — around 14–15% trial-to-paid, roughly ten points
   under even the q1 of 18. The gap should be obvious on the bench strip at a
   glance: a hole to patch and an easy win, not a marginal gain.
2. **Change A lands at or just below the industry median.**
3. **Change B lands just above it.**

Both then read as genuine recoveries to par-or-better rather than small lifts.
Being under the floor is a diagnosis; being on the median is not.

### Decide this explicitly

The arms sit in **different bands**. Change A is a 14-day trial, so the strip
measures it against *two weeks or more* (q1 31 · median 42), not against the
≤3-day band. Landing A at ~25% would put it below that band's floor even though
it clearly beat the baseline — which undercuts the very story the change is meant
to tell.

Either hold every arm against the baseline's ≤3-day band, or keep per-band
comparison and re-pick the targets so the arc still reads. The strip currently
compares each arm to its own band. Don't leave this implicit.

### Downstream work

- Figures are generated. Edit `scripts/build_demo_data.py`, then re-run
  `build_demo_data.py` and `build_page.py`. Hand-editing `data/demo_data.json`
  will fail the build — the generator re-derives each view twice and refuses to
  publish on a mismatch.
- `24.9%` is hardcoded in three places and will go stale: the `<title>`, the
  stage-1 bullet (*"Is 24.9% good?"*), and the bench panel heading. The hero
  reads from data via `#hero-rate` and is fine.
- Re-check the day-zero cancellation copy afterwards. A much lower baseline may
  change what the diagnosis should say.
