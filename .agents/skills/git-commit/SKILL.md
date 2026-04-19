---
name: git-commit
description: "Must load when writing, reviewing, or improving any git commit message, staging changes, or deciding how to split commits. Do not write commit messages without this skill."
user-invocable: false
---

# Git Commit Principles

Derived from the Linux Kernel's `Documentation/process/submitting-patches.rst` and Linus's stated taste on commit hygiene.

The stance beneath every rule below: *a commit is shaped by what makes the history useful to a future reader, not by what was convenient to author.* Each specific rule is that stance applied to one aspect of commit shape.

## One Logical Change Per Commit

A commit is a unit of reasoning, not a unit of effort. If two changes can be understood, reviewed, or reverted independently — they belong in separate commits.

Gotcha: "While I was there" changes are the enemy. Adding an unrelated cleanup to a bug fix makes the bug fix harder to bisect and the cleanup harder to revert. Resist.

## Bisect-Safety is Non-Negotiable

Every commit must leave the tree in a buildable, runnable, and testable state. A broken intermediate commit makes `git bisect` useless.

Gotcha: Don't commit "WIP" or "will fix in next commit" states. If you can't make the tree whole in one commit, restructure the split.

## Subject Line: Imperative, ≤72 chars, `subsystem: description` format

- Use imperative mood: "Fix", "Add", "Remove" — not "Fixed", "Adding", "Removes"
- Prefix with the affected subsystem/module: `net: fix null deref in socket teardown`
- No trailing period
- Target 50 chars; hard limit 72

Gotcha: `git log --oneline` is how humans scan history. A subject that wraps or is vague ("fix bug", "update", "misc") provides zero information at that view level.

## Body: Explain Why, Not What

The diff already shows what changed. The body exists to supply what the diff cannot: the intent behind the change.

Before writing the body, ask: *what is the intrinsic purpose of this change?* The intrinsic purpose is the property the codebase must hold that it currently does not, or the invariant this change restores, or the capability the system gains. But a useful message also records the concrete symptom, failure mode, or user-visible breakage that exposed the missing property. The reader needs both: the destination property and the observable evidence that made the change necessary.

The body must answer:
1. **What property is this change establishing, restoring, or removing?** (the intent)
2. **What concrete symptom, failure mode, or breakage revealed the gap?** (the evidence)
3. **Why was the prior state inconsistent with that property?** (the gap)
4. **Why is this diff the right way to close the gap?** (the reasoning)
5. **What are the trade-offs or risks, if any?**

Wrap body at 72 characters. Separate from subject with one blank line.

Gotcha: A message that narrates the author's journey ("I noticed X, so I tried Y, then changed Z") is still "what", just in prose form. The reader does not care about the path — they care about the failure, the destination property, and why this diff reaches it. If the body can be written without reference to how the author arrived at the change, it has found the right level.

Gotcha: A message that only restates the diff ("Change X to Y") is useless. Linus's standard: if you can't explain why, you probably don't understand the change well enough to commit it.

## Reference Context, Not Internal State

Reference bug IDs, issue numbers, or related commits by their external identifier. Never reference internal shorthand, branch names, or work-in-progress labels that disappear after merge.

```
Fixes: a3f2b91c ("net: introduce socket teardown path")
Closes: #1234
```

## Sign-Off and Authorship

For kernel-style projects: include `Signed-off-by: Name <email>` to certify the Developer Certificate of Origin (DCO). One sign-off per author in the chain.

Gotcha: `Signed-off-by` is a legal attestation, not a formality. Don't add it for others without their explicit agreement.

## Commit Size — The Linus Test

> "Does this commit make the project strictly better in one clear, self-contained way?"

If the answer requires a paragraph of qualifications, the commit is probably too large, too ambiguous, or mixing concerns. Split or rethink.

Good commits are small enough to review in 5 minutes and clear enough that the reviewer doesn't need to ask why.
