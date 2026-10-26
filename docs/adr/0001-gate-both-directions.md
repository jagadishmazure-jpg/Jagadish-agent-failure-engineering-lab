# ADR 0001: Gate both directions
**Decision.** The CI gate requires every fixed version to pass and every baseline to still fail.
**Why.** If a refactor breaks the dataset so nothing is hard any more, a one-way gate stays green. Requiring the baseline to fail proves the test still exercises the failure.
**Cost.** Changing a baseline needs a deliberate test update.
