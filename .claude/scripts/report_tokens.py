"""
Token usage report — reads .claude/logs/token-usage.jsonl and prints summary.

Usage:
    python .claude/scripts/report_tokens.py [--feature <name>] [--days <n>] [--all]

Options:
    --feature   Filter by feature name
    --days      Limit to last N days (default: 7)
    --all       Show all records regardless of date

Pricing constants are approximations. Verify current rates at anthropic.com/pricing.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
LOG_FILE = REPO_ROOT / ".claude" / "logs" / "token-usage.jsonl"

# Approximate pricing per 1M tokens (USD) — update as needed
# Source: anthropic.com/pricing (as of 2026-03)
PRICING = {
    "claude-opus-4-6":    {"input": 15.0,  "output": 75.0},
    "claude-sonnet-4-6":  {"input": 3.0,   "output": 15.0},
    "claude-haiku-4-5":   {"input": 0.8,   "output": 4.0},
    "claude-haiku-4-5-20251001": {"input": 0.8, "output": 4.0},
}
DEFAULT_PRICING = {"input": 3.0, "output": 15.0}  # fallback: sonnet rates


def estimate_cost(model: str, input_tok: int, output_tok: int) -> float:
    rates = PRICING.get(model, DEFAULT_PRICING)
    return (input_tok * rates["input"] + output_tok * rates["output"]) / 1_000_000


def load_records(days: int | None, feature: str | None) -> list[dict]:
    if not LOG_FILE.exists():
        return []

    cutoff = None
    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    records = []
    with LOG_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            if cutoff:
                try:
                    ts = datetime.fromisoformat(rec["timestamp"])
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts < cutoff:
                        continue
                except Exception:
                    pass

            if feature and rec.get("feature") != feature:
                continue

            records.append(rec)

    return records


def print_report(records: list[dict], days: int | None, feature: str | None) -> None:
    if not records:
        print("No records found.")
        return

    total_input = sum(r.get("input_tokens", 0) for r in records)
    total_output = sum(r.get("output_tokens", 0) for r in records)
    total_cache_read = sum(r.get("cache_read_tokens", 0) for r in records)
    total_cost = sum(
        estimate_cost(r.get("model", ""), r.get("input_tokens", 0), r.get("output_tokens", 0))
        for r in records
    )

    period = f"last {days} days" if days else "all time"
    feat_filter = f" | feature: {feature}" if feature else ""
    print(f"\nToken Usage Report — {period}{feat_filter}")
    print("=" * 50)
    print(f"Total sessions      : {len(records):,}")
    print(f"Total input tokens  : {total_input:,}")
    print(f"Total output tokens : {total_output:,}")
    print(f"Cache read tokens   : {total_cache_read:,}")
    print(f"Estimated cost      : ~${total_cost:.4f}  (approx, see pricing constants)")

    # By feature
    by_feature: dict[str, dict] = defaultdict(lambda: {"input": 0, "output": 0, "count": 0})
    for r in records:
        feat = r.get("feature") or "unknown"
        by_feature[feat]["input"] += r.get("input_tokens", 0)
        by_feature[feat]["output"] += r.get("output_tokens", 0)
        by_feature[feat]["count"] += 1

    print("\nBy feature:")
    for feat, stats in sorted(by_feature.items(), key=lambda x: -(x[1]["input"] + x[1]["output"])):
        print(f"  {feat:<30} {stats['input']:>8,} in / {stats['output']:>7,} out  ({stats['count']} sessions)")

    # By model
    by_model: dict[str, int] = defaultdict(int)
    for r in records:
        by_model[r.get("model") or "unknown"] += 1

    print("\nBy model:")
    for model, count in sorted(by_model.items(), key=lambda x: -x[1]):
        print(f"  {model:<35} {count:>4} sessions")

    # By user
    by_user: dict[str, int] = defaultdict(int)
    for r in records:
        user = r.get("git_user_name") or r.get("git_user_email") or "unknown"
        by_user[user] += 1

    print("\nBy user:")
    for user, count in sorted(by_user.items(), key=lambda x: -x[1]):
        print(f"  {user:<35} {count:>4} sessions")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Token usage report")
    parser.add_argument("--feature", default=None, help="Filter by feature name")
    parser.add_argument("--days", type=int, default=7, help="Last N days (default: 7)")
    parser.add_argument("--all", action="store_true", dest="all_time", help="Show all records")
    args = parser.parse_args()

    days = None if args.all_time else args.days
    records = load_records(days=days, feature=args.feature)
    print_report(records, days=days, feature=args.feature)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    sys.exit(0)
