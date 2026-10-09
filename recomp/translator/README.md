# Translation integration boundary

No translator is implemented yet. See [the research decision](../../docs/recompilation-research.md).
The first adapter must accept a validated executable identity, explicit function
entry and recovered control flow; emit native-compilable IR; and record its tool
commit, target, flags, unsupported instructions, and source address mapping.
Fail on unresolved edges or semantics. Never silently fall back to an interpreter.
