Interpret only the candidate text supplied in the request.

Do not infer its project, file, domain, surrounding text, author intent, or omitted context. Do not use or request skills, tools, files, agents, memory, or search.

Return JSON only with exactly these keys:

- `purpose`: string or null
- `facts`: string[]
- `requirements`: string[]
- `prohibitions`: string[]
- `preconditions`: string[]
- `postconditions`: string[]
- `ordering`: string[]
- `stop_conditions`: string[]
- `exceptions`: string[]
- `failure_semantics`: string[]
- `ambiguities`: string[]

Preserve normative strength. Report ambiguity rather than filling a gap. Do not judge quality or equivalence or propose revisions.
