---
name: search-grounded-response
description: "Must load before answering any factual, technical, or time-sensitive query. Do not produce factual responses without this skill."
user-invocable: false
---

# Search-Grounded Response Protocol

A runtime validation layer applied before synthesizing any response that involves factual claims, current data, or evolving technical specifications. Augments other active skills — does not replace reasoning or research craft principles.

## Temporal Awareness — Anchor Queries to the Current Date

Verify the current date from context before formulating search queries. Use it to bound queries temporally (e.g., "as of March 2026") and to judge whether internal knowledge is likely stale.

Gotcha: Pre-training has a cutoff. Treat internal knowledge of time-sensitive facts — API versions, pricing, org structures, library releases, live events — as a prior to be invalidated, not a source to cite.

## Search-First Mandate

Do not construct factual claims from pre-trained knowledge alone. Use the search tool to retrieve live data first; synthesize afterward.

Procedure (order matters):
1. Identify every factual claim the response will make.
2. For each claim, issue a temporally-anchored search query.
3. Retrieve results before beginning synthesis.

Gotcha: Internal confidence in a fact is not a substitute for a search. High confidence in stale information produces authoritative-sounding hallucinations — the most dangerous failure mode.

## Evidence-Based Synthesis

Construct the response exclusively from retrieved search results. If results conflict, surface the discrepancy and characterize the gap rather than silently arbitrating.

Gotcha: Do not blend retrieved evidence with internal assumptions without explicitly flagging which is which. If a search returns no usable result for a specific claim, state that explicitly — do not fill the gap from memory.

## Mandatory Citations

Every factual statement, statistic, or technical specification must carry an inline citation number. Append a numbered source list at the end of the response.

Format:
- Inline: `...the rate was 3.2% [1].`
- Footer: `[1] <Title> — <URL>`

Gotcha: A citation is evidence of grounding, not a formality. If no source URL can be produced for a claim, do not make the claim — flag the absence instead.
