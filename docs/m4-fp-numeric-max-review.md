# Numeric-max initializer independent review

The bounded standalone initializer at `0x4C19F0`, its complete body at
`0x4C1A00`, and the MSVCP50 provider at `0x780C10F0` pass independent review.
The actual table slot `0x5E016C`, named IAT `0x5BB4FC`, provider export and all
23 source instructions are independently checked against the exact files.

The [original input-derived model](../reports/m4-fp-numeric-max/independent-original-model-r1/report.json)
checks 14,688 original observations. The
[independent native comparison](../reports/m4-fp-numeric-max/independent-native-review-r6/report.json)
passes 29,376 O0/O2 records, including complete CPU, four memory pages, seeded
and protected 3,504-byte State, 352,512 ordered memory events and 29,376 call/RET
routes. There are 7,344 actual original debugger checkpoints. Their literal
zero FP metadata remains separate from direct leaf/wrapper FNSTENV. Native
checkpoint legacy metadata uses the paired original leaf and the independently
checked integer return route; it is explicitly an inference.

The [independent closure](../reports/m4-fp-numeric-max/independent-closure-r1/report.json)
also verifies exact guest-to-host transformation reversal, the two physical
tag commits and sticky-DE repair, all type layouts, linked/verified bodies,
six freshly decoded objects, 547 literal sources and 570 actual compiler read
dependencies. It independently reruns 144 compiled context checks, four
nonoverwrite publisher controls and six changed-input denials. All 2,480
closure bindings are recorded in its
[pins](../reports/m4-fp-numeric-max/independent-closure-r1/pins.json).
Reviewer failures and their exact source versions are preserved separately;
they changed no author production source or accepted guest artifact.

The admitted domain is sixteen declared binary32 words, twelve masked PC/RC
control words, TOP 0/7, contiguous live depths 0/1/7, sticky states 0/DE/DE+PE,
and two repeats under serial fixed frames and mappings. Finite promotion and
same-value stores are exact, including C1=0. Special C1, C0/C2/C3 and dead
register storage remain observations. Full-stack, pending/unmasked exceptions
and general incoming live values are outside this gate. Original Remill State
and event logs are unobserved; the complete native projections are checked
against inputs, hardware observations and the recovered instructions.

This acceptance does not integrate MSVCP50 with shared Runtime r9 or complete
the startup ledger. The connected 26-root gate is unchanged. Full CRT/SEH,
remaining initializers, application services and a native menu remain open M4
requirements. All original capture and baseline repair failures stay preserved.
