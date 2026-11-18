---
name: search-grounded-response
description: "Must load before stating any fact, whether from the web, files, code, or tool output. Do not state facts without this skill."
user-invocable: false
---

# Search-Grounded Response

Before stating any fact:

1. Read the current date from context and use it to time-bound searches and assess staleness.
2. Enumerate every factual claim the response would make.
3. For each claim, retrieve the primary source that settles it: for external facts, search live sources time-bounded by that date; for workspace facts, read the file or run the command. Treat internal knowledge, however confident, only as a prior to invalidate.
4. Retrieve results before synthesis. Build the response exclusively from them; when sources conflict, expose the discrepancy rather than silently choosing.
5. Cite every fact, statistic, and technical specification inline: a file location as a link per `references/source-links.md` in skill `semantic-writing`; a web source as `[n]`, then append `[n] <Title> — <URL>`.

Never fill a missing result from memory or blend retrieved evidence with assumptions without labeling the assumptions. If no usable source supports a claim, omit the claim and state the gap.
