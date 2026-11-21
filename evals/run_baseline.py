import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

# --------------------------------------------------------------------------------------
# 1) PLUG IN YOUR EXISTING CLASSIFIER
# --------------------------------------------------------------------------------------
# The function must take the ticket text and return: (label, input_tokens, output_tokens)
#
# Use the EXACT prompt and model your LangGraph pre-classification node uses today.
# You are measuring the real system, not an improved version of it.
#
# Example with the Anthropic SDK:
#
#   resp = client.messages.create(
#       model=MODEL_NAME, max_tokens=20, temperature=0,
#       system=CLASSIFIER_PROMPT,
#       messages=[{"role": "user", "content": text}],
#   )
#   label = resp.content[0].text
#   return label, resp.usage.input_tokens, resp.usage.output_tokens
#
# Example with LangChain's ChatAnthropic:
#
#   msg = llm.invoke([("system", CLASSIFIER_PROMPT), ("human", text)])
#   return msg.content, msg.usage_metadata["input_tokens"], msg.usage_metadata["output_tokens"]

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so "src" can be imported

from dotenv import load_dotenv
load_dotenv()  # reads your .env (src/config.py needs all 5 keys to be set)

from src.supervisor import classify_ticket_raw as classify_ticket

MODEL_NAME = "claude-haiku-4-5"   # the model your system currently uses
PROMPT_VERSION = "v1"       # bump this if you ever change the classifier prompt

# USD per million tokens, from Anthropic's pricing page for MODEL_NAME
PRICE_IN_PER_MTOK = 1.0    # Claude Haiku 4.5: $1 per million input tokens
PRICE_OUT_PER_MTOK = 5.0   # Claude Haiku 4.5: $5 per million output tokens

LABELS = ["billing", "technical", "general"]  # must match your labeling guidelines


# --------------------------------------------------------------------------------------
# 2) EVALUATION
# --------------------------------------------------------------------------------------
def normalize(raw: str) -> str:
    """Map the model's raw output to a label, or INVALID if it isn't one."""
    cleaned = str(raw).strip().lower().strip(".\"'` ")
    if cleaned in LABELS:
        return cleaned
    # tolerate outputs like '{"category": "billing"}' or 'Category: billing'
    for label in LABELS:
        if label in cleaned:
            return label
    return "INVALID"


def run_once(df: pd.DataFrame, delay: float, run_idx: int) -> pd.DataFrame:
    rows = []
    for i, row in enumerate(df.itertuples(index=False), start=1):
        start = time.perf_counter()
        try:
            raw, in_tok, out_tok = classify_ticket(row.text)
            error = ""
        except Exception as e:  # keep going; failures are part of the baseline
            raw, in_tok, out_tok, error = "", 0, 0, repr(e)
        latency_ms = (time.perf_counter() - start) * 1000

        rows.append({
            "run": run_idx,
            "id": row.id,
            "text": row.text,
            "label": row.label,
            "difficulty": row.difficulty,
            "raw_output": raw,
            "pred": normalize(raw) if not error else "ERROR",
            "latency_ms": round(latency_ms, 1),
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "error": error,
        })
        if i % 25 == 0:
            print(f"  run {run_idx}: {i}/{len(df)} done")
        if delay:
            time.sleep(delay)
    return pd.DataFrame(rows)


def summarize(preds: pd.DataFrame) -> dict:
    first = preds[preds["run"] == 1]
    y_true, y_pred = first["label"], first["pred"]

    in_token, out_token = first["input_tokens"].sum(), first["output_tokens"].sum()
    cost = (in_token * PRICE_IN_PER_MTOK + out_token * PRICE_OUT_PER_MTOK) / 1_000_000
    cost_per_1k = cost / len(first) * 1000

    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": MODEL_NAME,
        "prompt_version": PROMPT_VERSION,
        "n_tickets": int(len(first)),
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "macro_f1": round(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0), 4),
        "accuracy_by_difficulty": {
            d: round(accuracy_score(g["label"], g["pred"]), 4)
            for d, g in first.groupby("difficulty")
        },
        "invalid_or_error_rate": round(float(y_pred.isin(["INVALID", "ERROR"]).mean()), 4),
        # latency uses all runs, so --runs 3 gives a steadier number
        "latency_ms_p50": round(float(preds["latency_ms"].quantile(0.50)), 1),
        "latency_ms_p95": round(float(preds["latency_ms"].quantile(0.95)), 1),
        "avg_input_tokens": round(float(first["input_tokens"].mean()), 1),
        "avg_output_tokens": round(float(first["output_tokens"].mean()), 1),
        "cost_usd_per_1k_tickets": round(cost_per_1k, 4),
        "per_class": classification_report(
            y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0
        ),
        "confusion_matrix": {
            "labels": LABELS,
            "matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist(),
        },
    }

    # Consistency: how often does the same ticket get the same label across runs?
    n_runs = preds["run"].nunique()
    if n_runs > 1:
        agree = preds.groupby("id")["pred"].nunique().eq(1).mean()
        summary["runs"] = int(n_runs)
        summary["label_agreement_across_runs"] = round(float(agree), 4)

    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-set", default="evals/data/test_set.csv")
    parser.add_argument("--runs", type=int, default=1, help="repeat the full set N times")
    parser.add_argument("--delay", type=float, default=0.0, help="seconds between calls (rate limits)")
    parser.add_argument("--out-dir", default="evals/results")
    parser.add_argument("--limit", type=int, default=0, help="only use the first N tickets (for a quick test)")
    args = parser.parse_args()

    df = pd.read_csv(args.test_set)
    missing = {"id", "text", "label", "difficulty"} - set(df.columns)
    if missing:
        raise SystemExit(f"Test set is missing columns: {missing}")
    if args.limit:
        df = df.head(args.limit)
    bad = set(df["label"]) - set(LABELS)
    if bad:
        raise SystemExit(f"Test set has labels not in LABELS: {bad}")

    print(f"Evaluating {len(df)} tickets x {args.runs} run(s) with {MODEL_NAME} ...")
    preds = pd.concat(
        [run_once(df, args.delay, r) for r in range(1, args.runs + 1)], ignore_index=True
    )
    summary = summarize(preds)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    preds.to_csv(out / f"baseline_{stamp}_predictions.csv", index=False)
    (out / f"baseline_{stamp}_summary.json").write_text(json.dumps(summary, indent=2))

    print("\n=== BASELINE ===")
    for key in ["accuracy", "macro_f1", "accuracy_by_difficulty", "invalid_or_error_rate",
                "latency_ms_p50", "latency_ms_p95", "cost_usd_per_1k_tickets",
                "label_agreement_across_runs"]:
        if key in summary:
            print(f"{key:30s} {summary[key]}")
    print("\nConfusion matrix (rows = true, cols = predicted):", LABELS)
    for label, row in zip(LABELS, summary["confusion_matrix"]["matrix"]):
        print(f"  {label:10s} {row}")
    print(f"\nSaved to {out}/baseline_{stamp}_*")


if __name__ == "__main__":
    main()