# Training: labs and capstone

Each lab: run the CLI, read the baseline, break the fix on purpose, watch the test or gate fail, restore it.

| Lab | Task | Done when |
|---|---|---|
| 1 Term meaning | Add `"donor-specific antibody positive"` as a contraindication concept | `fixed_term_risk` holds it and a new test passes |
| 2 Field direction | Add a `remaining`-direction field (e.g. courier battery minutes) with its own definition | both directions handled, mismatched units escalate |
| 3 Confidence spiral | Change `max_stale` to 3; explain the trade-off between speed and false alarms | tests updated with reasoning in the PR |
| 4 Endless booking | Remove the idempotency key and run `test_single_commit_with_retry_and_replay` | you can explain why it fails, then restore it |
| 5 Gaming the metric | Write an agent that escalates only severity >= 9 | scorecard reports the missed escalations and the gate blocks it |
| 6 Hidden misses | Add 5 adversarial cases with disguised signals | a severity-only agent gets `DO NOT DEPLOY` |

## Capstone
Add a seventh failure from your own domain (for example, a tool returning stale cached data). Deliver: a baseline that fails, a fix, at least 4 tests, a row in the CLI comparison, and a gate condition. CI must stay green and the README table must regenerate.
