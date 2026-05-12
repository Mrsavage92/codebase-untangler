#!/usr/bin/env python3
"""
audit_helpers.py - Common audit analysis commands.

Usage:
  python -m scripts.audit_helpers loc          # files ranked by LOC
  python -m scripts.audit_helpers churn        # files ranked by git churn
  python -m scripts.audit_helpers hotspots     # combined LOC + churn ranking
  python -m scripts.audit_helpers deps         # dependency overview (Node/Python)
"""

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, shell=isinstance(cmd, str))


def loc():
    """LOC per tracked file, sorted descending."""
    result = run(["git", "ls-files"])
    files = result.stdout.strip().split("\n")
    rows = []
    for f in files:
        p = Path(f)
        if not p.is_file():
            continue
        # skip binary/large lockfiles
        if p.suffix in (".lock", ".min.js", ".min.css", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"):
            continue
        try:
            n = sum(1 for _ in p.open(errors="ignore"))
        except (OSError, UnicodeDecodeError):
            continue
        rows.append((n, f))
    rows.sort(reverse=True)
    print("Top 30 files by LOC:")
    for n, f in rows[:30]:
        print(f"  {n:>6}  {f}")
    return rows


def churn():
    """File change frequency from git log."""
    result = run(["git", "log", "--format=format:", "--name-only"])
    files = [f for f in result.stdout.split("\n") if f]
    counter = Counter(files)
    print("Top 30 files by change frequency:")
    for f, c in counter.most_common(30):
        print(f"  {c:>4}  {f}")
    return counter.most_common()


def hotspots():
    """Combined ranking: high LOC + high churn = hotspot."""
    loc_rows = loc()
    print()
    churn_rows = churn()
    print()

    loc_rank = {f: i for i, (_, f) in enumerate(loc_rows)}
    churn_rank = {f: i for i, (f, _) in enumerate(churn_rows)}

    common = set(loc_rank) & set(churn_rank)
    scored = []
    for f in common:
        # lower combined rank = bigger hotspot
        scored.append((loc_rank[f] + churn_rank[f], f, loc_rank[f], churn_rank[f]))
    scored.sort()
    print("Top 20 hotspots (high LOC AND high churn):")
    for score, f, l_rank, c_rank in scored[:20]:
        print(f"  combined={score:<4} LOC_rank={l_rank:<4} churn_rank={c_rank:<4} {f}")


def deps():
    """Quick dependency overview for Node and Python projects."""
    if Path("package.json").exists():
        pkg = json.loads(Path("package.json").read_text())
        deps = pkg.get("dependencies", {})
        dev = pkg.get("devDependencies", {})
        print(f"package.json: {len(deps)} deps, {len(dev)} devDeps")
        # detect duplicates by category (e.g. multiple HTTP clients)
        flags = []
        all_deps = list(deps.keys()) + list(dev.keys())
        http_clients = [d for d in all_deps if d in ("axios", "node-fetch", "got", "superagent", "ky", "isomorphic-fetch")]
        date_libs = [d for d in all_deps if d in ("moment", "date-fns", "dayjs", "luxon")]
        if len(http_clients) > 1:
            flags.append(f"Multiple HTTP clients: {http_clients}")
        if len(date_libs) > 1:
            flags.append(f"Multiple date libs: {date_libs}")
        if flags:
            print("Potential redundancy:")
            for f in flags:
                print(f"  - {f}")
    if Path("pyproject.toml").exists():
        print("pyproject.toml found - run `pip list` and review")
    if Path("requirements.txt").exists():
        lines = [l for l in Path("requirements.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
        print(f"requirements.txt: {len(lines)} packages")


COMMANDS = {"loc": loc, "churn": churn, "hotspots": hotspots, "deps": deps}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
