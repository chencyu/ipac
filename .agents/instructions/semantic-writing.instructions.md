---
applyTo: '**'
---

# Semantic Writing

Governs all content a reader decodes for meaning, human or AI: chat replies, comments, docstrings, documentation, prompts, skills, commit and error messages. Content consumed only by its form, such as executable logic, configuration values, and schemas, follows its own domain rules.

Readers differ in two parameters, not in rule sets: what they already hold, and where the content renders.

## Deliver a running model

Content installs a model that answers correctly on its own at the size of the need. A large true fraction of the subject does not run; the complete model of a smaller world does.

- **Scope** = the questions the reader must then answer correctly, derived from the request's shape, not its topic: "why X rather than Y" includes "is Y viable here". Neither widen it nor settle short of it.
- **Selection:** for each fact held, ask whether an in-scope answer changes were the fact different. Changes through how it works → state the mechanism. Changes only through its result → name it and state what it guarantees. No change → absent, not summarised or flagged as omitted.
- Name in one line where the model stops holding. Simplify only into a restricted case of the truth, never into a mechanism that must later be torn down.
- A hedge is a branch the reader cannot resolve: in scope → state it flat, attached to what it qualifies; out of scope → absent. No preamble, unasked adjacent question, or account of what was read. Stop when the model runs.

## Attach in order

- Open on what the reader can point to: the subject in use, what is done with it and what follows.
- Bring in each later element through its relation to one already present; state what a thing is before contrasting it.
- Use vocabulary the reader already holds; keep each causal chain in one place.

## Encode the relations

Make relations visible in the representation: nesting for containment, aligned rows for comparison on shared dimensions, labelled directed links for order or dependency, the literal form for exact form, a followable reference for an existing object. Position, direction, and grouping make claims too: a bare arrow must not turn sequence into causation. Do not restate what structure carries; what one reference reaches is not carried again. Use only forms the destination renders.

Read `skill: semantic-writing`: `references/source-links.md` when referring to a location in a file. Content that outlives the conversation, such as files and commit messages, also passes the contract and audit in skill `semantic-writing`: load it before writing or revising such content.
