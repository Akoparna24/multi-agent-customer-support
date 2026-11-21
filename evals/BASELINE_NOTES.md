# Baseline: Claude Haiku 4.5, prompt v1 (21 Nov 2026)

This is the official "before" score for the ticket classifier
(`classify_ticket` in `src/supervisor.py`). Every later change is
compared against these numbers.

## Setup

- **Model:** `claude-haiku-4-5`, current prompt (v1), default temperature
- **Test set:** `evals/data/test_set.csv`, 250 tickets (183 easy, 67 hard).
  ~175 written with AI help and reviewed by hand, ~75 real customer
  messages from a public dataset. Labelled using `evals/LABELING_GUIDELINES.md`.
- **Runs:** 3 (accuracy from run 1; latency and consistency from all runs)
- **Script:** `python evals/run_baseline.py --runs 3`
- **Raw results:** `evals/results/baseline_20261121_112959_*`

## Results

| Metric | Value |
|---|---|
| Accuracy | 95.6% (239 / 250) |
| Accuracy on easy tickets | 98.4% |
| Accuracy on hard tickets | 88.1% |
| Macro-F1 | 0.956 |
| Invalid replies | 0% |
| Latency p50 / p95 | 717 ms / 818 ms |
| Cost per 1,000 tickets | $0.15 |
| Same answer across runs | 98% |

### Confusion matrix (rows = true label, columns = predicted)

|  | billing | technical | general |
|---|---|---|---|
| **billing** | 80 | 3 | 2 |
| **technical** | 1 | 83 | 0 |
| **general** | 1 | 4 | 76 |

## Error analysis (11 errors)

### 1. Problem-sounding words push questions to "technical" (5 errors)

Words like "unable", "not able", "log out", "data leak" and "flag" make
Claude choose technical, even when the customer is asking how to do
something or asking about policy.

| id | Ticket | Label | Predicted |
|---|---|---|---|
| 13 | I am not able to remove my saved credit card from my payment methods. Pls remove it | billing | technical |
| 30 | Unable to locate accessibility settings | general | technical |
| 67 | How can I flag a user who's using abusive language? | general | technical |
| 117 | How do I log out from all my devices? | general | technical |
| 134 | Is it safe to use your app? I heard there was a data leak | general | technical |

### 2. Tie-breaker rules are not in the prompt (6 errors)

The rules in `LABELING_GUIDELINES.md` exist only in the answer key. The
prompt never mentions them, so Claude cannot apply them. The most common
case is "paid but feature not unlocked → billing".

| id | Ticket | Rule | Label | Predicted |
|---|---|---|---|---|
| 153 | bought premium yesterday, still showing free plan | Paid but not unlocked | billing | technical |
| 246 | upgraded to pro but my storage limit is still 5GB | Paid but not unlocked | billing | technical |
| 71 | charged twice and now the app won't even open | Two problems: blocking one wins | technical | billing |
| 86 | want to delete my acount permanantly and also want refund | Two problems: first mentioned wins | general | billing |
| 81 | What is your refund policy? | Refunds beat "policy" | billing | general |
| 185 | Do you have any offers going on right now? | Price questions → billing | billing | general |

### Observations

- 8 of the 11 errors are hard tickets. The hard cases are where Claude
  struggles and where a fine-tuned model has the best chance to compete.
- The most common error is general → technical (4 of 11).
- Cost is already very low, so a fine-tuned model's advantage will come
  from **latency, no external API dependency, and learning
  company-specific rules**, not from cost.

## Next

- **Phase 4:** run the same test set on the fine-tuned model and compare
  it against:
  1. this baseline (prompt v1), and
  2. a **prompt v2** that includes the tie-breaker rules, to answer
     "why not just put the rules in the prompt?"
- Possible small fix later: strip punctuation in `classify_ticket` so a
  reply like `Billing.` is not silently routed to general.