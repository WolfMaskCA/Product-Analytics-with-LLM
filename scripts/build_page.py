#!/usr/bin/env python3
"""
build_page.py — inline data/demo_data.json into src/template.html -> index.html

The published page is one self-contained file: no server, no database, no chart
library, no runtime fetch. Open it from file://, email it, or serve it from Pages.

    python3 scripts/build_page.py            # -> index.html
    python3 scripts/build_page.py --check    # verify only, write nothing
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEMPLATE = os.path.join(ROOT, "src", "template.html")
DATA = os.path.join(ROOT, "data", "demo_data.json")
OUT = os.path.join(ROOT, "index.html")

PLACEHOLDER = "/*__DEMO_DATA__*/{}"


def main():
    check = "--check" in sys.argv

    with open(TEMPLATE) as f:
        html = f.read()
    with open(DATA) as f:
        raw = f.read()
        data = json.loads(raw)

    if PLACEHOLDER not in html:
        print("ERROR: placeholder %s not found in template" % PLACEHOLDER)
        return 1
    if html.count(PLACEHOLDER) != 1:
        print("ERROR: placeholder appears %d times, expected 1" % html.count(PLACEHOLDER))
        return 1

    # </script> inside a JSON string would close the script block early.
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    out = html.replace(PLACEHOLDER, payload)

    problems = []
    if not data.get("meta", {}).get("synthetic"):
        problems.append("data is not flagged synthetic — refusing to publish")
    if "</script>" in payload:
        problems.append("payload still contains a literal </script>")
    for needle in ("Generic Fitness App", "synthetic"):
        if needle not in out:
            problems.append("published page is missing the %r disclosure" % needle)
    # Nothing from the private project this method came out of may reach this repo.
    # The blocklist itself would be a leak if it lived here, so it is read from a
    # local, git-ignored file: one lowercase token per line, '#' for comments.
    # Absent (a fresh clone), the check is skipped and says so.
    blocklist = os.path.join(ROOT, ".private-tokens")
    if os.path.exists(blocklist):
        low = out.lower()
        n = 0
        with open(blocklist) as f:
            for line in f:
                tok = line.strip().lower()
                if not tok or tok.startswith("#"):
                    continue
                n += 1
                if tok in low:
                    problems.append("page contains a blocked private token (line %d of "
                                    ".private-tokens)" % n)
        print("    blocklist: %d tokens checked" % n)
    else:
        print("    blocklist: .private-tokens not present — skipped")

    for p in problems:
        print("FAIL: " + p)
    if problems:
        return 1

    print("OK: %d arms, %d weeks, experiment starts week %d" % (
        len(data["arms"]), data["meta"]["weeks"], data["meta"]["split_week"]))
    print("    data payload %.1f kB · page %.1f kB" % (len(payload)/1024.0, len(out)/1024.0))

    if check:
        print("--check: nothing written")
        return 0

    with open(OUT, "w") as f:
        f.write(out)
    print("wrote %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
