---
applyTo: '**'
---

# Re-anchor Skills at the Point of Action

**Why** — A skill loads into context once; its guidance then ages as the turn fills with reasoning, tool calls, and file reads. You weight recent context far more heavily than distant context, so a skill loaded earlier no longer reliably shapes output by the time you act — it is present but no longer governing.

**Rule** — Re-load the governing skill as the *last step before* producing any artifact it governs — even if it is already active this turn. The re-load and the operation must be back-to-back, with nothing between them: load, then immediately act. This overrides the usual habit of skipping an already-loaded skill. What makes guidance bind is not that it was loaded, but that it sits adjacent to the operation, at the position of strongest attention. If any reasoning, tool call, or file read separates the re-load from the act, the adjacency is broken — re-load again. Re-load is cheap; emitting work under decayed guidance is not.
