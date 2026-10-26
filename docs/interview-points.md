# Interview points
- Agents fail on meaning, not just on facts: "positive" can be the worst news. Fix with concept lookup and policy status, not sentiment.
- Every number needs a direction, unit and origin; recompute from timestamps and escalate on disagreement.
- An agent re-reading its own output is not evidence. Require fresh evidence ids; count stale iterations; escalate.
- Separate plan from commit. Planning is free to repeat; committing happens once, with human approval and an idempotency key.
- A single metric can be gamed: escalate-everything scores perfectly on "no unsafe autonomous action". Gate on several objectives.
- 99% accuracy on imbalanced data can mean 0% critical recall. Report risk groups separately and block release on critical recall.
- Gate both directions so a broken harness cannot pass quietly.
