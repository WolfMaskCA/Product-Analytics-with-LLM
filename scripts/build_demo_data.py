#!/usr/bin/env python3
"""
build_demo_data.py — the synthetic dataset behind the Generic Fitness App demo.

There is no real dataset anywhere in this repo. Every install, trial, conversion and
week below is invented by a seeded PRNG, shaped so the *method* is demonstrable —
not so it reports anyone's results.

The scenario, in one line: a subscription app runs a 3-day free trial, converts about
15% of trials to paid — below the floor for its own trial length — and has no idea
that is where it sits. Two changes are proposed and measured.

Structure follows the one-cube rule: a single atomic table

    cube[arm][week] = {installs, trials, paid, cancels[4], renewed}

Everything the page draws — the funnel, the weekly trend, the cancellation-timing
diagnosis, the result tiles, the benchmark markers — is DERIVED from that table, in
Python here and again in JavaScript on the page, so no filter can make two panels
disagree.

stdlib only. Deterministic: same seed -> byte-identical demo_data.json.

    python3 scripts/build_demo_data.py            # write data/demo_data.json
    python3 scripts/build_demo_data.py --check    # regenerate + verify, write nothing
"""

import json
import os
import random
import sys

SEED = 7
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "demo_data.json")

WEEKS = 12
SPLIT_WEEK = 4          # weeks 0-3 are baseline-only; the experiment starts at week 4
WEEK_LABELS = [
    "Mar 3", "Mar 10", "Mar 17", "Mar 24",
    "Mar 31", "Apr 7", "Apr 14", "Apr 21", "Apr 28",
    "May 5", "May 12", "May 19",
]

# ----------------------------------------------------------------------------------
# The three arms
# ----------------------------------------------------------------------------------
# Both proposed changes target the same headline metric — trial-to-paid — so the
# comparison stays legible. Exactly two proposals: any more and it stops being a
# recommendation and starts being a backlog.

ARMS = [
    {
        "key": "baseline", "slot": 1, "name": "Baseline", "short": "Baseline",
        "label": "3-day trial · paywall on first launch",
        "i2t": 0.069,          # install -> trial start
        "t2p": 0.148,          # trial start -> paid — BELOW the floor of its own band
        "d0": 0.622,           # day-0 cancellations, worse than typical for a 3-day trial
        "renew": 0.781,        # month-2 renewal of new subscribers (the guard metric)
        "live_from": 0,
    },
    {
        "key": "trial14", "slot": 3, "name": "Change A — 14-day trial", "short": "A · 14-day trial",
        "label": "14-day trial · paywall on first launch",
        "i2t": 0.069, "t2p": 0.376, "d0": 0.331, "renew": 0.788,
        "live_from": SPLIT_WEEK,
        "hypothesis": "Three days is not long enough to reach the moment the app is "
                      "actually useful, so the trial is being judged before it has done "
                      "anything. A longer trial should convert better.",
        "change": "Trial length on the subscription product: <code>P3D</code> → <code>P14D</code>.",
        "where": "Store product config + <code>trial_days</code> in the paywall copy string. "
                 "One product setting and one string; no new screens.",
        "expect": "Two-week trials typically land around 42%. Getting there also means fixing "
                  "how early we ask, so expect to clear the two-week floor of 31% and land "
                  "short of the middle — high 30s.",
    },
    {
        "key": "latepay", "slot": 2, "name": "Change B — paywall after onboarding",
        "short": "B · late paywall",
        "label": "3-day trial · paywall after onboarding",
        "i2t": 0.081, "t2p": 0.272, "d0": 0.523, "renew": 0.774,
        "live_from": SPLIT_WEEK,
        "hypothesis": "The paywall appears before the user has any reason to want the app. "
                      "Showing it after the first workout — once there is something to lose "
                      "— should convert better and start more trials.",
        "change": "Move the paywall from launch to the end of onboarding, after the first "
                  "completed session.",
        "where": "<code>onboarding_paywall_step</code>: <code>0</code> → <code>4</code> "
                 "(after <code>first_session_complete</code>). Existing screens, new order.",
        "expect": "This keeps the 3-day trial, so it is judged against the short-trial band. "
                  "Clearing that band's typical 25% would mean the timing alone was worth more "
                  "than the whole gap we are down. Expect high 20s, plus a lift in trial starts.",
    },
]

# ----------------------------------------------------------------------------------
# Industry context — ILLUSTRATIVE, and generated here like everything else.
# Rounded, directional ranges of the kind that are common knowledge in subscription
# apps. Deliberately not attributed to, or copied from, any particular study.
# ----------------------------------------------------------------------------------
BENCH = {
    "metric": "Trial-to-paid conversion",
    "note": "Illustrative industry range for subscription apps, by trial length. "
            "Shown to demonstrate how an outside anchor changes what a number means — "
            "these are directional figures for the demo, not a published benchmark.",
    "bands": [
        {"label": "3 days or less", "q1": 18.0, "median": 25.0, "q3": 38.0},
        {"label": "About a week",   "q1": 27.0, "median": 37.0, "q3": 52.0},
        {"label": "Two weeks or more", "q1": 31.0, "median": 42.0, "q3": 59.0},
    ],
    "scale_max": 65.0,
    "cancel_note": "Short trials lose most of their cancellations on day zero; longer "
                   "trials spread them out. Illustrative figures.",
    "cancel_bands": [
        {"label": "3-day trial", "d0": 55.0},
        {"label": "7-day trial", "d0": 40.0},
        {"label": "14-day trial", "d0": 36.0},
        {"label": "30-day trial", "d0": 31.0},
    ],
}

CANCEL_DAYS = ["Day 0", "Day 1", "Day 2", "Day 3+"]


def split_cancels(total, d0_share, rng):
    """Distribute cancellations across day buckets; d0_share lands on day 0."""
    d0 = int(round(total * d0_share * rng.uniform(0.97, 1.03)))
    rest = max(0, total - d0)
    w = [0.44, 0.28, 0.28]
    parts = [int(round(rest * x)) for x in w]
    parts[-1] += rest - sum(parts)
    return [d0] + parts


# ----------------------------------------------------------------------------------
# Derivations — every one reads ONLY the cube
# ----------------------------------------------------------------------------------

def slice_cube(cube, keys, w0, w1):
    out = {"installs": 0, "trials": 0, "paid": 0, "renewed": 0,
           "cancels": [0, 0, 0, 0]}
    for k in keys:
        for w in range(w0, w1 + 1):
            r = cube[k][w]
            if not r:
                continue
            out["installs"] += r["installs"]
            out["trials"] += r["trials"]
            out["paid"] += r["paid"]
            out["renewed"] += r["renewed"]
            for i in range(4):
                out["cancels"][i] += r["cancels"][i]
    return out


def rates(t):
    return {
        "i2t": round(100.0 * t["trials"] / t["installs"], 2) if t["installs"] else 0.0,
        "t2p": round(100.0 * t["paid"] / t["trials"], 2) if t["trials"] else 0.0,
        "i2p": round(100.0 * t["paid"] / t["installs"], 3) if t["installs"] else 0.0,
        "renew": round(100.0 * t["renewed"] / t["paid"], 1) if t["paid"] else 0.0,
        "d0": round(100.0 * t["cancels"][0] / sum(t["cancels"]), 1) if sum(t["cancels"]) else 0.0,
    }


def main():
    rng = random.Random(SEED)
    check = "--check" in sys.argv

    # ---------------- build the cube -----------------------------------------------
    cube = {}
    for a in ARMS:
        rows = []
        for w in range(WEEKS):
            if w < a["live_from"]:
                rows.append(None)
                continue
            live = sum(1 for x in ARMS if x["live_from"] <= w)
            weekly_installs = 12400 + 260 * w
            installs = int(round(weekly_installs / live * rng.uniform(0.96, 1.04)))

            # Counts come from the arm's rate plus a small controlled jitter, rather than
            # from per-user Bernoulli draws. At a few hundred trials a week, sampling noise
            # alone swings the weekly rate by 2-3 points, which reads as spiky and invites
            # the viewer to explain bumps that are not there. The figures are illustrative,
            # so the jitter is set to show ordinary week-to-week movement without the noise
            # burying the effect being demonstrated.
            trials = int(round(installs * a["i2t"] * rng.uniform(0.97, 1.03)))
            paid = int(round(trials * a["t2p"] * rng.uniform(0.955, 1.045)))
            renewed = int(round(paid * a["renew"] * rng.uniform(0.985, 1.015)))
            rows.append({
                "installs": installs, "trials": trials, "paid": paid,
                "renewed": min(renewed, paid),
                "cancels": split_cancels(trials - paid, a["d0"], rng),
            })
        cube[a["key"]] = rows

    KEYS = [a["key"] for a in ARMS]

    # ---------------- derive ---------------------------------------------------------
    weekly = {}
    for a in ARMS:
        out = []
        for w in range(WEEKS):
            if not cube[a["key"]][w]:
                out.append(None)
                continue
            t = slice_cube(cube, [a["key"]], w, w)
            r = rates(t)
            out.append({"installs": t["installs"], "trials": t["trials"], "paid": t["paid"],
                        "t2p": r["t2p"], "i2t": r["i2t"], "i2p": r["i2p"]})
        weekly[a["key"]] = out

    # Baseline "where we are" reads the PRE-experiment weeks only — the honest before.
    pre = slice_cube(cube, ["baseline"], 0, SPLIT_WEEK - 1)
    pre_r = rates(pre)

    # Results read the experiment window only, so arms are compared like for like.
    arms_out = []
    for a in ARMS:
        t = slice_cube(cube, [a["key"]], SPLIT_WEEK, WEEKS - 1)
        r = rates(t)
        arms_out.append({
            "key": a["key"], "slot": a["slot"], "name": a["name"], "short": a["short"],
            "label": a["label"], "live_from": a["live_from"],
            "installs": t["installs"], "trials": t["trials"], "paid": t["paid"],
            "cancels": t["cancels"],
            "i2t": r["i2t"], "t2p": r["t2p"], "i2p": r["i2p"],
            "renew": r["renew"], "d0": r["d0"],
            "hypothesis": a.get("hypothesis", ""), "change": a.get("change", ""),
            "where": a.get("where", ""), "expect": a.get("expect", ""),
        })
    base = next(x for x in arms_out if x["key"] == "baseline")
    for x in arms_out:
        x["lift_pp"] = round(x["t2p"] - base["t2p"], 2)
        x["lift_rel"] = round(100.0 * (x["t2p"] / base["t2p"] - 1), 1) if base["t2p"] else 0.0

    funnel = [
        {"step": "Installs", "n": pre["installs"]},
        {"step": "Trial started", "n": pre["trials"]},
        {"step": "Converted to paid", "n": pre["paid"]},
        {"step": "Renewed month 2", "n": pre["renewed"]},
    ]

    data = {
        "meta": {
            "company": "Generic Fitness App",
            "product": "Subscription fitness app — free-trial conversion",
            "seed": SEED, "weeks": WEEKS, "split_week": SPLIT_WEEK,
            "window": "Mar 3 – May 25",
            "synthetic": True,
            "note": "Every figure in this file, including the industry ranges, is generated "
                    "by scripts/build_demo_data.py. No real customer or company data is "
                    "present, and the industry context is illustrative rather than sourced.",
        },
        "week_labels": WEEK_LABELS,
        "cancel_days": CANCEL_DAYS,
        "cube": cube,
        "weekly": weekly,
        "arms": arms_out,
        "baseline_pre": {
            "installs": pre["installs"], "trials": pre["trials"], "paid": pre["paid"],
            "renewed": pre["renewed"], "cancels": pre["cancels"],
            "i2t": pre_r["i2t"], "t2p": pre_r["t2p"], "i2p": pre_r["i2p"],
            "renew": pre_r["renew"], "d0": pre_r["d0"],
            "weeks": SPLIT_WEEK,
        },
        "funnel": funnel,
        "bench": BENCH,
    }

    # ---------------- self-check -----------------------------------------------------
    problems = []
    for a in arms_out:
        wl = sum(r["trials"] for i, r in enumerate(weekly[a["key"]]) if r and i >= SPLIT_WEEK)
        if wl != a["trials"]:
            problems.append("weekly rows do not re-aggregate for %s" % a["key"])
    for a in arms_out:
        if sum(a["cancels"]) + a["paid"] != a["trials"]:
            problems.append("cancels + paid != trials for %s" % a["key"])
    r = {a["key"]: a["t2p"] for a in arms_out}
    if not (r["trial14"] > r["latepay"] > r["baseline"]):
        problems.append("both changes should beat baseline, with A ahead of B")
    # Each arm is judged inside the band its own trial length belongs to. That is the
    # decision the arc rests on, so it is asserted rather than left to the copy.
    short_band, long_band = BENCH["bands"][0], BENCH["bands"][2]
    if pre_r["t2p"] >= short_band["q1"]:
        problems.append("baseline %.2f should sit BELOW the short-trial floor of %.1f — "
                        "without a visible hole there is nothing to diagnose"
                        % (pre_r["t2p"], short_band["q1"]))
    lp = next(a for a in arms_out if a["key"] == "latepay")
    if not (short_band["median"] < lp["t2p"] < short_band["q3"]):
        problems.append("change B (%.2f) should clear the short-trial median %.1f and stay inside "
                        "that band — it does not change trial length"
                        % (lp["t2p"], short_band["median"]))
    t14 = next(a for a in arms_out if a["key"] == "trial14")
    if not (long_band["q1"] < t14["t2p"] < long_band["median"]):
        problems.append("change A (%.2f) should land inside the two-week band (floor %.1f) but "
                        "below its median %.1f, so headroom is still visible"
                        % (t14["t2p"], long_band["q1"], long_band["median"]))
    if pre_r["d0"] <= BENCH["cancel_bands"][0]["d0"]:
        problems.append("baseline day-0 cancellations should exceed the typical short-trial figure")
    d0 = {a["key"]: a["d0"] for a in arms_out}
    if not (d0["baseline"] > d0["trial14"]):
        problems.append("the longer trial should pull cancellations off day 0")
    renews = [a["renew"] for a in arms_out]
    if max(renews) - min(renews) > 6.0:
        problems.append("renewal rates should stay flat — the guard against a hollow win")

    for p in problems:
        print("MISMATCH: " + p)
    if not problems:
        print("MATCH: cube reconciles to every derived view; story checks hold")

    print("  baseline (pre)  install→trial %.2f%% · trial→paid %.2f%% · day-0 cancels %.1f%%"
          % (pre_r["i2t"], pre_r["t2p"], pre_r["d0"]))
    for a in arms_out:
        print("  %-18s trial→paid %5.2f%%  (%+.2f pp, %+.1f%%)  renew %.1f%%  day-0 %.1f%%"
              % (a["short"], a["t2p"], a["lift_pp"], a["lift_rel"], a["renew"], a["d0"]))

    if check:
        print("--check: nothing written")
        return 1 if problems else 0

    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print("wrote %s (%.1f kB)" % (os.path.relpath(OUT), os.path.getsize(OUT) / 1024.0))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
