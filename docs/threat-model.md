# Threat model (STRIDE + OWASP LLM Top 10, lab scope)

| Threat | Example here | Control |
|---|---|---|
| Spoofing | Replayed GPS event presented as new | event id + monotonic timestamp check (failure 3) |
| Tampering | Unit changed from h to min upstream | field definition + timestamp recomputation (failure 2) |
| Repudiation | Who approved a booking? | named approver required; idempotency key logged (failure 4) |
| Information disclosure | n/a: synthetic data only | no real records; gitleaks in CI |
| Denial of service | Optimizer loops and books without end | iteration cap, minimum gain (failure 4) |
| Elevation of privilege | Agent commits without a human | plan/commit split (failure 4) |
| LLM06 Excessive agency | Booking every option | human approval + single commit |
| LLM09 Misinformation | Overconfident ETA | fresh-evidence rule + escalation |
| Eval gaming | Escalate-all, always-routine | multi-objective and risk-group gates (failures 5-6) |
