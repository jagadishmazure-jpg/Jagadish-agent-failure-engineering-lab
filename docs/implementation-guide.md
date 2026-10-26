# Implementation guide (for adopters)

Apply the six fixes to your own agent in this order. Each step names the module here to copy the pattern from.

## 1. Inventory risky meanings (failures 1-2)
1. List every domain term where generic sentiment is wrong ("positive" test results, "negative" margins).
2. Map synonyms to a concept id; attach a policy status (`contraindication`, `compatible`, ...). Pattern: `SYNONYMS`, `ONTOLOGY`.
3. For every numeric field the agent reads, write a definition: direction (elapsed vs remaining), unit, origin timestamp. Pattern: `FieldDef`.
4. Recompute derived values from timestamps; if the reported value disagrees, escalate.
5. Unknown term or unit -> escalate to an expert, never guess.

## 2. Make loops terminate (failures 3-4)
1. Every belief update must cite a fresh evidence id and timestamp; the agent's own prior output is never evidence.
2. Keep a stale counter; escalate after N stale iterations (N=2 here).
3. Separate planning (pure, repeatable) from committing (side effects).
4. Bound planning: max iterations plus minimum-improvement stop.
5. Commit once, only with a named human approver, with an idempotency key the downstream API enforces.

## 3. Make evals honest (failures 5-6)
1. Split the test set into routine / critical / adversarial groups and report each.
2. Gate on several objectives at once: critical escalated = 1.0, missed escalations = 0, autonomous completion >= target, unnecessary escalation <= target.
3. Report critical recall separately; never publish headline accuracy alone.
4. Gate both ways: fixes must pass and known-bad baselines must still fail.
5. Every production incident becomes a regression case.

## Checklists
**Semantic:** terms normalized? concepts mapped? policy status known? field direction/unit/origin defined? mismatch escalates?
**Loop:** fresh evidence required? stale counter? iteration cap? minimum gain? plan separate from commit? human approval? idempotency?
**Eval:** risk groups? critical recall reported separately? multi-objective gate? adversarial cases? regression tests in CI?
