"""Run the eval set against the chatbot and write a results report.

  python eval/run_eval.py                 # engine chosen like the app does (auto)
  python eval/run_eval.py --engine local  # offline engine, no API key needed
  python eval/run_eval.py --engine claude # needs ANTHROPIC_API_KEY + credit
  python eval/run_eval.py --out eval/results_v1_local.md

A case passes when every regex in "must" matches the reply (case-insensitive) and no regex in
"must_not" does. Keep the case list honest: add cases for every real failure you find.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["local", "claude", "auto"], default="auto")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if args.engine == "local":
        os.environ["CHAT_MODE"] = "local"
    elif args.engine == "claude":
        os.environ["CHAT_MODE"] = "claude"
    import chatbot  # after env is set

    cases = json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))
    rows, by_type = [], defaultdict(lambda: [0, 0])
    for c in cases:
        reply, mode = chatbot.answer([{"role": "user", "content": c["q"]}])
        miss = [p for p in c.get("must", []) if not re.search(p, reply, re.I)]
        bad = [p for p in c.get("must_not", []) if re.search(p, reply, re.I)]
        ok = not miss and not bad
        by_type[c["type"]][0] += ok
        by_type[c["type"]][1] += 1
        rows.append((c, reply, mode, ok, miss, bad))

    total = sum(r[3] for r in rows)
    lines = [f"# Eval results ({date.today()})", "",
             f"Engine requested: `{args.engine}`. Replies came from: {', '.join(sorted({r[2] for r in rows}))}.", "",
             f"**Overall: {total}/{len(rows)} passed ({100 * total // len(rows)}%).**", "",
             "| Type | Passed |", "|---|---|"]
    lines += [f"| {k} | {v[0]}/{v[1]} |" for k, v in by_type.items()]
    lines += ["", "## Failures", ""]
    fails = [r for r in rows if not r[3]]
    if not fails:
        lines.append("None.")
    for c, reply, mode, ok, miss, bad in fails:
        lines += [f"- **{c['id']}** {c['q']}", f"  - reply: {reply!r}", f"  - missing: {miss}  forbidden hit: {bad}"]
    lines += ["", "## All cases", "", "| ID | Type | Result | Question |", "|---|---|---|---|"]
    lines += [f"| {c['id']} | {c['type']} | {'PASS' if ok else 'FAIL'} | {c['q']} |" for c, _, _, ok, _, _ in rows]
    report = "\n".join(lines) + "\n"
    print(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
    sys.exit(0 if total == len(rows) else 1)


if __name__ == "__main__":
    main()
