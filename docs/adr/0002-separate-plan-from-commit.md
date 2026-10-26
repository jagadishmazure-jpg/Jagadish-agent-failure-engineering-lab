# ADR 0002: Separate plan from commit
**Decision.** Search returns a plan with no side effects; a separate commit step needs a named approver and an idempotency key.
**Why.** Fusing them is what makes an optimizer book every improvement. Separation makes retries and replays safe.
**Cost.** One extra human step on time-critical paths; mitigated by bounded, fast planning.
