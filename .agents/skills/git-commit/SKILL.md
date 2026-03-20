---
name: git-commit
description: "Must load when writing, reviewing, or improving any git commit message, staging changes, or deciding how to split commits. Do not write commit messages without this skill."
user-invocable: false
---

# Git Commit Principles

Derived from the Linux Kernel's `Documentation/process/submitting-patches.rst` and Linus's stated taste on commit hygiene.

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

The diff already shows what changed. The body must answer:
1. **Why was the current behavior wrong?** (the problem)
2. **Why is this the right fix?** (the reasoning)
3. **What are the trade-offs or risks, if any?**

Wrap body at 72 characters. Separate from subject with one blank line.

Gotcha: A commit message that only restates the diff ("Change X to Y") is useless. Linus's standard: if you can't explain why, you probably don't understand the change well enough to commit it.

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
