---
name: algorithm-selector
description: "Must load before attempting to solve a problem with an algorithm. Do not select or implement algorithmic solutions without this skill."
---

# Algorithm Selector

Forces systematic pattern-matching from problem structure to known algorithms before implementation begins.

## When This Skill Fires

After upstream skills (`thinking-principles`, `problem-solving`) have decomposed the problem and extracted its generating core — but **before** designing or implementing a solution.

**Skip this skill** when the task is implementation-level work with no algorithmic substance (format a string, read a file, configure a tool, glue APIs together).

## Protocol

### Step 1 — Extract structural features

From the problem analysis already done, identify:
- **Input structure** — what data shape does the problem operate on?
- **Output goal** — what does the solution produce?
- **Key properties** — what constraints or characteristics matter?

### Step 2 — Select hashtags

Run the matcher from the skill's `scripts/` directory to see the full tag vocabulary:

```
python "<skill-dir>/scripts/matcher.py" --tags
```

Select **all tags** that describe the problem.

**Tag selection order**: Start with **Input Structure** tags (observable from the data), then **Output Goal** tags (what the solution must produce). Add **Problem Property** tags only for constraints you can verify from the problem statement — not from solution intuition. Add **Paradigm** tags only as a last resort. The catalog should surface the paradigm for you.

### Step 3 — Retrieve candidates

Run the matcher with the selected tags:

```
python "<skill-dir>/scripts/matcher.py" <tag1> <tag2> <tag3> ...
```

Use `--min-overlap 2` (default) for broad recall, increase to 3+ to narrow.

### Step 4 — Evaluate candidates

For each returned candidate:
1. The algorithm **name alone** is sufficient to activate pretrained knowledge — recall its preconditions, complexity, and typical use cases.
2. Verify: do the algorithm's **assumptions** hold in the current problem context?
3. If a candidate's paradigm tag suggests related algorithms not in the result set, check those too (second-hop retrieval).

### Step 5 — Return judgment

Report:
- Ranked candidates with match rationale
- Any candidates rejected and why (assumption violation)
- If no candidate fits: state this explicitly — the problem may require a novel approach

## Gotchas

- **Do not skip Step 2.** Going straight from problem to implementation is the failure mode this skill exists to prevent.
- **Do not force-fit.** If the best candidate has only 2/6 tag overlap and weak assumption match, it is not a match — say so.
- **Problem Property tags have circularity risk.** Tags like `#overlapping-subproblems` or `#optimal-substructure` require you to already partially know the solution structure. Select them only when the property is directly observable from the problem statement (e.g., "minimize total cost" → `#optimization`), not when it requires solution-side reasoning.

## Files

- [`scripts/catalog.py`](scripts/catalog.py) — Tag enum + Algorithm dataclass + full catalog (138 entries)
- [`scripts/matcher.py`](scripts/matcher.py) — CLI & library API for hashtag matching
