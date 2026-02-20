"""Lightweight cost tracker - logs token usage per query to a local CSV."""
import csv, os
from datetime import datetime

LOG_FILE = "./logs/usage_log.csv"
os.makedirs("./logs", exist_ok=True)

PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o":      {"input": 2.50, "output": 10.00},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
}

def log_usage(model, input_tokens, output_tokens, query_preview=""):
    cost = (
        (input_tokens / 1_000_000) * PRICING.get(model, {}).get("input", 0) +
        (output_tokens / 1_000_000) * PRICING.get(model, {}).get("output", 0)
    )
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost, 6),
        "query_preview": query_preview[:80]
    }
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    return cost

def get_total_cost():
    if not os.path.exists(LOG_FILE):
        return 0.0
    total = 0.0
    with open(LOG_FILE, "r") as f:
        for row in csv.DictReader(f):
            total += float(row.get("cost_usd", 0))
    return round(total, 4)
