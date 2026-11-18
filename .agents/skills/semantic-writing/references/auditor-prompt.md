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

Preserve normative strength. An ambiguity is a statement the text makes that admits more than one reading; report it rather than resolving it. A case the text does not address, or a judgment it leaves to its reader, is neither an ambiguity nor a gap to fill. Do not judge quality or equivalence or propose revisions.
