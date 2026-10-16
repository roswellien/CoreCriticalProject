# Campaign and restart video fault — October 15, 2026

The user's r7 Remaster started successfully once, then failed when entering
the first campaign mission and on subsequent startups. All three saved logs
stop at reported PC `0x1103ac18`. This address belongs to the rebased Indeo
IV50 decoder, not MFC42; the old generic hardware-fault message mislabeled it.
The installed pilot and registry match the frozen baseline and are unchanged
by this investigation. No reset, save deletion or registry repair was needed.

## Cause and correction

The original codec calibration at `0x1103ab10` measures 500,000 iterations of
eighteen NOPs between real QPC/RDTSC readings. Optimization erased the loop.
Its elapsed-time denominator, corrected for back-to-back clock-call overhead,
could consequently become zero. `DIV ECX` at `0x1103ac16` then faults; the
reported address is its next PC. A private r7 run reproduces the exact fault;
two earlier attempts succeed, retaining evidence of its intermittent nature.
Virtual-clock regression tests use QPF 1 MHz, outside this calibration branch;
the normal host uses real QPF within its original 1–50 MHz bounds.

`tools/m4-crt-heap-carry/codec_timing.py` accepts only the complete pinned host
IR for this routine. Before optimization it preserves the eighteen native
NOPs in the original loop and disables loop unrolling/vectorization. It leaves
clock services, guest state, arithmetic, overflow checks and the original
unsupported-frequency fallback intact. Unrelated modules remain byte-identical;
changed known-target input fails visibly. `inline_objects.py` applies the fix
before any optimization recipe, including builds without ordinary IR cleanup.
Use a fresh output tree; existing cached objects are intentionally retained by
that tool and are not implicitly rebuilt. No delay/divisor/CPU value is invented,
and movies remain enabled. The generic divide-fault message now names lifted
x86 code rather than incorrectly attributing every module to MFC42.

Only one of r7's 37,201 optimized objects is replaced. Its speed improvements,
renderer, asset registrations, music and quality settings are retained. Generated
code/media remain local. The public and independently prepared private objects
have exactly matching disassembly and relocations; COFF metadata differs.

## Executed validation and publication

- Native assembly retains exactly 500,000 loop iterations, eighteen NOPs per
  iteration and both original RDTSC endpoints. Seven actual-input guard checks
  and three asset-free unit tests pass; an independent pipeline review found
  no blocking defect.
- Real-clock startup passes two eight-frame starts and a 128-frame decode.
  A separate visible run decodes 700 intro frames. These end at explicit
  budgets, not at movie completion.
- Original-compatible regressions pass **Training 116/116**, **mode 7 GPU draw
  stream 1150/1150**, and **Instant Action 116/116**, with actual gameplay reached.
  These deterministic comparisons retain their normal codec-disabled setup;
  the real-clock movie tests above cover the previously missed branch.
- Through the original Campaign UI, the retained pilot's **Operation 1,
  Mission 1** briefing/map/launch path reaches 1,800 native presented frames,
  including 1,001 frames with 3D, plus third-person and forward movement.
  Movies and real clocks are enabled alongside all current Remaster assets,
  music, HUD, **3440x1440, FXAA and 16x AF**. Intro and briefing skips use ordinary
  buffered DirectInput after initial decoding. Exit is the deliberate frame
  budget, not mission completion.

Both existing root Remaster launchers now resolve through `launcher.json` to
`local/remaster/gpu-native-r8-codec/build/entry_commandline.exe`, SHA256
`0c3bab3516a2f43f9bc642c5e4403b4c057a12abdd3a52ed4d36a7f9aa76d152`.
The r7 profile is retained as `launcher.r7-backup-20261015-codec.json`.
The launcher read-only check confirms 39 texture banks, Bushwacker/Mad Cat/
Vulture/Thor, local music and the existing quality profile. Avatar remains
excluded. Main `Play-MW3.cmd` is not repointed by this change.

Local evidence: `local/campaign-startup-crash-r1/validation.json`, its named
`runs/`, and `local/remaster/gpu-native-r8-codec/source-snapshot.json`. Runs use
copied installations/pilots and private registry overlays. Actual installed
registry/pilot and the acceptance receipt hashes are unchanged. No desktop
screenshots, original-code fallback, commit or strict-acceptance run.

This closes the observed decoder divide fault and advances real-clock campaign
entry into first-mission gameplay. Whole-mission completion, later campaign,
save/load, hardware SEH and existing model damage/LOD/muzzle/normal-map limits
remain open. Acceptance stays **131/144, paused**. Next is sustained first-mission
play and later mission/movie transitions, independently of the remaining model
fidelity work.
