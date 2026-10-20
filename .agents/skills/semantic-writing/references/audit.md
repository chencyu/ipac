# Bounded Audit

**Audit:** baseline + candidate → independent reconstruction → contract comparison → accept or retain.

Remove avoidable representation, not meaning or required value. Construct every candidate by the core; truncation and symbol substitution are not improvements by themselves.

## Bounded pass

| Step | Action | Gate |
| --- | --- | --- |
| 1. Scope | Freeze the target and its contract using the shared baseline rules; diff against pre-edit content where available | Protected passages stay verbatim |
| 2. Decompose | Identify semantic units: declarations, paragraphs, list items, table rows, diagram nodes/edges, comments, messages, names, or configuration entries | Record each candidate unit's contract before rewriting |
| 3. Propose | For one unit, remove duplication, indirect representation, or unnecessary notation; prefer an existing authoritative representation | Name the burden removed; preserve every contract dimension |
| 4. Reconstruct | Read [blind-audit.md](references/blind-audit.md) and obtain an isolated reconstruction of the candidate | Do not give the auditor the baseline or desired reading |
| 5. Compare | Compare reconstructed claims against the recorded contract; check required value and delivery separately | Apply the shared acceptance gate, not a length score |
| 6. Apply | Apply one accepted candidate at a time, then rerun the checks that observe its contract | Verify the integrated artifact, not just the edited unit |

## Outcomes

| Evidence | Outcome |
| --- | --- |
| Equivalent meaning and value, reduced burden, applicable checks pass | Accept |
| Reconstruction loses meaning, adds claims, or introduces ambiguity | Revise once; a second failure retains the baseline unit |
| No justified reduction remains | Retain the unit as `already-minimal` |
| Independent reconstruction or necessary checks unavailable | Retain the baseline; report the unverified reduction, not equivalence |

Retained units do not restart the pass. Return to them only when requirements or evidence change.

Checks follow the artifact: syntax/schema, diagnostics, rendering, reference resolution, behavior tests, or golden comparisons as applicable. For tracked files, check `git diff --check` before completion. Do not deliver a changed artifact on the strength of a blind reconstruction alone.