# Representation Patterns

During protocol step 4, match the branch smell—not merely its data type—apply the corresponding representation move, and delete the branch. Apply correctness-shaping moves before performance layout.

## Dissolving special cases (correctness shaping — do first)

| Smell you are about to code                                       | Representation move                                                                                       | Branch it deletes                                                            |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `if (node == head)` when removing/inserting in a linked structure | **Pointer-to-pointer** (indirect pointer): iterate `T **p = &head; while (*p != target) p = &(*p)->next;` | the head/first-element special case (Linus's canonical "good taste" example) |
| `if (list.empty())` scattered across operations                   | **Sentinel / dummy node** (dummy head and/or tail), or a **`NonEmpty`** type constructed at the boundary  | empty-collection checks                                                      |
| Off-by-one at range edges; inclusive/exclusive confusion          | **Half-open intervals** `[lo, hi)` everywhere                                                             | end-point special cases; makes empty range `lo == hi` natural                |
| Index wrap-around logic at buffer ends                            | **Circular / ring buffer** with modular index                                                             | wrap boundary branches                                                       |
| `flag` + fields that are only meaningful sometimes                | **Sum type / tagged union / discriminated union** naming each legal state                                 | illegal flag↔field combinations                                              |
| Nullable field re-checked on every use                            | **Option/Maybe parsed once** at the boundary into a non-null type                                         | downstream null checks                                                       |
| "is this value in range/valid?" re-asked everywhere               | **newtype + smart constructor** at the boundary (parse, don't validate)                                   | repeated validation                                                          |
| Many `bool`s describing one thing (`2^N` combos, most illegal)    | one **enum** of the legal states                                                                          | impossible-combination handling                                              |
| Membership / dedupe scans over a list                             | **`Set`**, or **`Map` keyed by identity**                                                                 | `O(n)` scans and duplicate-key bugs                                          |
| Nested loop searching one collection for another's keys           | **Index / hash map**, or **adjacency list** for graphs                                                    | the inner search loop (Pike: the algorithm becomes self-evident)             |
| Ad-hoc parent/child pointers chased by hand                       | explicit **tree/graph with typed edges**                                                                  | bespoke traversal special cases                                              |
| State machine encoded as scattered flags                          | explicit **state enum + transition table** (fold the logic into data)                                     | branchy transition code                                                      |
| Two copies of the same fact kept in step manually                 | **single source of truth + derived view** (generated, or one owner module)                                | desync bugs (SSOT)                                                           |

## Performance layout (do only AFTER measuring a bottleneck)

| Measured problem                                     | Move                                                       | Note                                                   |
| ---------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------ |
| Cache misses iterating one field across many records | **SoA** (struct-of-arrays) instead of AoS                  | data-oriented design; only when the hot loop is proven |
| Pointer-chasing a hot collection                     | **contiguous array / arena** + indices instead of pointers | improves locality; indices double as stable handles    |
| Repeated expensive derivation in a hot path          | **precomputed / memoized view** with one clear owner       | still SSOT: the view is derived, not authoritative     |

After each move, re-derive the core operation; if another branch appears, repeat because moves compose. Performance moves are permitted only after measurement identifies a bottleneck.
