# Blind Reconstruction

**Author holds:** baseline + contract. **Auditor sees:** candidate only. **Author decides:** equivalence.

## Isolation

Dispatch a fresh subagent whose entire prompt is the text of [auditor-prompt.md](auditor-prompt.md) followed by the candidate. Pick the agent type with the fewest tools the harness offers; tool access it cannot remove is restricted only by that prompt.

Send the candidate alone. Do not attach its source path, original text, surrounding context, skill identity, author intent, or evaluation hints. Preserve names and references that are part of the candidate itself; stripping them would audit a different candidate.

No subagent available → retain the baseline and report the limitation. Self-review is not independent reconstruction.

## Comparison

| Reconstruction | Check against the author's recorded contract |
| --- | --- |
| Purpose and facts | Same claims and scope |
| Requirements and prohibitions | Same normative strength |
| Preconditions, postconditions, ordering, stops, exceptions, failures | Same behavior boundaries |
| Ambiguities | No newly unresolved meaning |

Compare claim-by-claim using the shared contract's acceptance gate. The reconstruction is evidence, not authority: it cannot establish factual truth, required rhetorical value, correct rendering, or successful reference resolution by itself.

A pointer establishes a reference, not the contents behind it. Verify the target's accessibility and contract separately; never infer equivalence from an opaque link. Judge the candidate in its intended integration after the isolated check, without feeding that integration back to the auditor.

Use the retry and stop rules in [audit.md](audit.md); this reference does not start another audit pass.