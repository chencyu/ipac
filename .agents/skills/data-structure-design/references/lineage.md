# Lineage — Why Data Structure Design Comes First

The methodology distills one idea voiced repeatedly across four decades: **data is more tractable than logic, so shift complexity out of code and into the representation.** Each rule in `SKILL.md` traces to a source below. Read this when you need the rationale or a citable origin.

## The core claim

> "I will, in fact, claim that the difference between a bad programmer and a good one is whether he considers his code or his data structures more important. Bad programmers worry about the code. Good programmers worry about data structures and their relationships." — Linus Torvalds [1]

This is the root of the whole skill. The rest are corollaries.

## Good taste = dissolving special cases

In his 2016 TED talk, Torvalds contrasts two implementations of singly-linked-list removal. The naive one branches on whether the target is the head; the elegant one uses an **indirect pointer** (`list_item **p = &head`) so the head is no longer special [2]:

> "...sometimes you can see a problem in a different way and rewrite it so that a special case goes away and becomes the normal case, and that's good code." — Linus Torvalds [2]

The Unix tradition states the same defensively:

> "One very important tactic for being robust under odd inputs is to avoid having special cases in your code. Bugs often lurk in the code for handling special cases, and in the interactions among parts of the code intended to handle different special cases." — Eric S. Raymond, *The Art of Unix Programming*, Rule of Robustness [3]

→ Powers **Step 4** and the first gotcha.

## The algorithm is downstream of the representation

> "Rule 5. Data dominates. If you've chosen the right data structures and organized things well, the algorithms will almost always be self-evident. Data structures, not algorithms, are central to programming." — Rob Pike, *Notes on Programming in C* [3][4]

> "Rule 3. Fancy algorithms are slow when *n* is small, and *n* is usually small. ... Rule 4. Fancy algorithms are buggier than simple ones ... Use simple algorithms as well as simple data structures." — Rob Pike [3][4]

→ Powers **Step 6** (re-derive the operation as the acceptance test) and the "don't reach for a cleverer algorithm" gotcha.

## Tables before flowcharts

> "Show me your flowcharts and conceal your tables, and I shall continue to be mystified. Show me your tables, and I won't usually need your flowcharts; they'll be obvious." — Fred Brooks, *The Mythical Man-Month* (1975), pp. 102–3 [5]

> "The programmer's primary weapon in the never-ending battle against slow systems is to change the intramodular structure. Our first response should be to reorganize the modules' data structures." — Fred Brooks [5]

→ Powers **Step 1** (model entities and relationships first).

## Fold knowledge into data

> "Fold knowledge into data, so program logic can be stupid and robust." ... "Data is more tractable than program logic. It follows that where you see a choice between complexity in data structures and complexity in code, choose the former. More: in evolving a design, you should actively seek ways to shift complexity from code to data." — Eric S. Raymond, Rule of Representation [3]

→ Powers **Step 2** and the two-phase gotcha.

## Make illegal states unrepresentable (the modern, type-driven form)

> "Use a data structure that makes illegal states unrepresentable. Model your data using the most precise data structure you reasonably can." ... "write functions on the data representation you wish you had, not the data representation you are given." — Alexis King, *Parse, don't validate* (2019) [6]

The same essay names the failure mode of validation-without-refinement — **shotgun parsing** (from LangSec [7]) — where checks get sprayed across processing code, and warns:

> "Avoid denormalized representations of data... Duplicating the same data in multiple places introduces a trivially representable illegal state: the places getting out of sync. Strive for a single source of truth." — Alexis King [6]

The slogan "make illegal states unrepresentable" was popularized in ML/functional practice by **Yaron Minsky** (Jane Street) [8].

→ Powers **Step 2**, the "validation throws away what it learned" gotcha, and the SSOT gotcha (which also ties to *skill: design-principles* → Single Source of Truth).

## Practice beats theory; layout comes last

> "Theory and practice sometimes clash. And when that happens, theory loses. Every single time." — Linus Torvalds, on the Linux 2.6.29 release [9]

The performance-layout phase (AoS↔SoA, cache-aware packing) belongs to **data-oriented design**: shape data for the real hardware and the common-case data, after measuring — Mike Acton, "Data-Oriented Design and C++", CppCon 2014 [10]. This is the *second* phase precisely because of Knuth's warning that premature optimization is the root of all evil [3].

→ Powers the "theory loses to practice" and "two phases, in order" gotchas.

## Sources

[1] Linus Torvalds, linux-kernel / git mailing list, 2006-06-27 — https://lore.kernel.org/all/Pine.LNX.4.64.0607270936200.4168@g5.osdl.org/
[2] Linus Torvalds, "The mind behind Linux", TED 2016 (≈14:10) — https://www.ted.com/talks/linus_torvalds_the_mind_behind_linux ; worked explanation: M. Kirchner, "Linked lists, pointer tricks and good taste" — https://github.com/mkirchner/linked-list-good-taste
[3] Eric S. Raymond, *The Art of Unix Programming* (2003), "Basics of the Unix Philosophy" (Rule of Representation, Rule of Robustness; quotes Pike's rules and Knuth in full) — http://www.catb.org/~esr/writings/taoup/html/ch01s06.html
[4] Rob Pike, *Notes on Programming in C* (1989), Rules 1–6.
[5] Fred Brooks, *The Mythical Man-Month* (1975, Anniversary ed. 1995), pp. 102–3 and ch. 9 — https://en.wikiquote.org/wiki/Fred_Brooks
[6] Alexis King, "Parse, don't validate" (2019-11-05) — https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/
[7] Bratus et al., "The Seven Turrets of Babel: A Taxonomy of LangSec Errors" (2016) — http://langsec.org/papers/langsec-cwes-secdev2016.pdf
[8] Yaron Minsky, "Effective ML" / *Real World OCaml* — "make illegal states unrepresentable".
[9] Linus Torvalds, Linux 2.6.29 announcement, 2009-03-25 — https://lore.kernel.org/all/alpine.LFD.2.00.0903252017100.3032@localhost.localdomain/
[10] Mike Acton, "Data-Oriented Design and C++", CppCon 2014.
