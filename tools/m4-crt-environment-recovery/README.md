# Environment source recovery

This read-only workahead decodes the original environment-block acquisition,
vector construction and remaining `__getmainargs` return unit. It executes only
the pinned static decoder; it never loads the provider, invokes an API, lifts
code or runs a native worker. Accepted namespaces remain unchanged.

Run `python tools/m4-crt-environment-recovery/recover.py recovery-r1` once into
the fresh report directory. The receipt includes exact source spans, complete
instruction bytes, imported names, direct and indirect edges, raw pages and
permissions. The ANSI `memcpy` dependency is recovered for disjoint forward
copies; its overlap/backward path is explicitly outside the planned domain.
Fatal `_amsg_exit` is an explicit unresolved dependency.

The next integration must carry the live heap, locale, lazy lock and builder
allocations. `BA9E` is a live source boundary, not a reusable cleaned snapshot.
The external environment helper schedule is a research seam and does not
establish original DLL attach, complete CRT startup or a game launch.
