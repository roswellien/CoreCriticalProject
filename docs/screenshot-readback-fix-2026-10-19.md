# Screenshot pixel-format repair

Follow-up: pixel-format correctness did not establish terrain appearance. The
remaining photo-mode streaks are addressed separately in
[the texture-state repair](photo-mode-texture-state-fix-2026-10-19.md).

The Material Normal Preview now saves correctly decoded F9 screenshots. The
reported double image, incorrect colors and black lower area came from the
capture readback path, not the displayed game frame.

The renderer normally uses packed RGB565: two bytes per pixel. Its old raw
capture function copied four bytes per pixel and passed the result to a BGRA8
consumer. That paired unrelated source pixels, read the unused buffer tail and
produced the wrong image layout and colors. The RGBA8 renderer fallback also
needed an explicit red/blue channel conversion for the BGRA consumer.

`capture_fullres_bgra` now sizes the transfer from the actual renderer format
and converts tightly packed RGB565 or RGBA8 into opaque BGRA8. PNG and video
consumers share that readback contract. Pixel-buffer extents are checked before
reading or writing. Rendering, surface lifetimes, photo cameras, texture assets,
normal strengths and the disabled replay-video default are unchanged.

## Verification

- C++ checks cover RGB565 and RGBA8 primary colors, odd-width two-row layout,
  output alpha, and malformed buffer extents without modifying the output.
- A PNG written through the real BGRA encoder decodes to the exact six expected
  color-chart pixels and row order.
- An ordinary Big Lake native control completes 1,300 Vulkan frames with every
  draw triple matching the preceding surface-lifetime build.
- A separate private test supplies held keys at the existing async polling
  boundary. It saves real F9 PNGs during live play, paused photo mode with the
  HUD/legend hidden, and resumed gameplay. All three are 3440 by 1440, visually
  inspected with correct colors and a single complete image.
- Every pixel outside the post-capture "Screenshot saved" notification matches
  the same-frame native PPM reference exactly: 4,935,512 pixels per image.
  The reference includes that 532 by 34 notification rectangle, while the PNG
  intentionally precedes it. There are no other pixel differences.
- Native testing used RGB565 on the AMD Radeon RX 9070. RGBA8 conversion is
  covered by the CPU/PNG fixture; native video encoding and another GPU were
  not exercised in this repair.

The installed executable SHA-256 is
`1d61f6e58811852092f0e4bd0ce03adb2d81b1a02cd1e7bbc2e969c2ebd8bc15`.
Its source changes are the renderer capture method, photo capture call site and
new conversion header. Source pins and launcher check match. The installed host
contains no private key injection. Use `Play MW3 - Material Normal Preview.cmd`,
then F9; the normal repository installation saves in `local/screenshots/`.

Evidence and corrected screenshots are indexed in
`reports/capture-readback-fix-20261019/verification.json`, on the Games-drive
report archive. Earlier F9 PNG checks established decoding and dimensions only;
they missed the pixel corruption. Those PNGs are not visual acceptance evidence.
The independent native PPM comparisons from the preceding photo/water repairs
remain valid. Formal acceptance stays 131/144. No commit or push is made.
