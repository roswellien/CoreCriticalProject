# Current project direction

Read `docs/faithful-modernization-plan.md`, `docs/roadmap.md` and
`docs/m4-Codex-work-review-2026-10-11.md` before choosing implementation work.
The execution-first strategy was authorized on2026-10-11: preserve original
MW3 gameplay through recompilation, integrate modern platform services/Vulkan,
and advance native host -> live menu -> live Training. Do not restart as a remake.

Keep existing acceptance criteria and evidence intact. Last verified count is
131/144; probes, replay and original-game hooks do not grant native-game credit.
The detailed acceptance lane is retained in `docs/m4-execution-plan-r14.md`, but
it is not the sole implementation queue. Legacy priority text is historical
where it conflicts with the current strategy; guest ABI/FP/resource contracts
and required initialization effects still apply.

Inspect current process identities before expensive work. Protect the existing
controls composer/watcher and never open active SQLite or duplicate a long job.
Use admissionv2 after actual successful closure and independently review the
post-composer chain. Preserve uncommitted work and other graphics/asset writers.

State the execution boundary advanced by each change and run narrow meaningful
checks. Add no verifier/report layer without an identified missing criterion or
concrete defect. Fail unknown required services visibly; no AFTER seeding or fake
API success. No production interpreter/original-code fallback is authorized.

Read `CONTRIBUTING.md` and `docs/legal.md`; original media and generated game
code stay local. Full continuation instructions are in
`docs/Codex-m4-continuation-handoff.md`. Do not commit unless the user asks.
