# Opening cinematic: GPU AV1 compression

Completed the full opening movie from its validated 2880x2160, 30 fps FFV1/PCM
master. The user selected a GPU encode tuned against the prior SVT-AV1 CRF24
sample after clarification that AMD AMF has no CRF control. Integration remains
deferred until the native recompile is ready.

Output: `local/work-ahead/opening-cinematic-av1-gpu-v1/opening-2160p-30fps-av1-gpu.mkv`.
344887895 bytes (328.91 MiB), compared with the prior 638541662-byte H.264/AAC
review export: approximately 46% smaller, despite lossless rather than AAC audio.
Encoder pass: 80.53 seconds. Encoder is `av1_amf`, 10-bit 4:2:0, transcoding usage,
quality preset, CQP72 for I/P pictures and a 60-frame GOP. This is not CRF24.
PCM is encoded as FLAC with the original 22050 Hz stereo sample contract.

AMF QVBR failed encoder initialization with error 10 in both tested quality
presets. A 10-bit CQP capability test succeeded. Six-second INTRO samples tested
QP64/72/80/88/96/112/128 against the same source section. At QP72 the common
8-bit 4:2:0 SSIM was 0.982830 versus 0.982728 for the SVT-AV1 CRF24 sample;
sample sizes were 20174861 and 14965846 bytes respectively. That comparison
guided conservative calibration but does not prove perceptual equivalence or
equal quality over the whole movie. Logs and both calibration JSONs are local.

Full validation: 5474 decoded frames, 2880x2160, 30/1 fps, 10-bit AV1, complete
182.467-second Matroska timeline, packet presentation grid within 1 ms and a
successful complete FFmpeg `-xerror` decode. All 4023397 source audio sample
frames are preserved: decoded PCM SHA-256
`27e76684cec7fe93684d2ba9bf16fde87c245c52006626fa0efe7e909f8d68f6`.
Output SHA-256:
`30bb5dc615b2c9e2e2cacf5ffba31f10f4827628ab7e36e1d7920143ba4f1705`.

`manifest.json` records exact commands, encoder control, source/output hashes,
installed tool identities, duration and validation results. `encode_full.py`
records the local workflow. Full-speed visual review remains pending. Original
master, earlier H.264 export and software CRF24 samples are unchanged. The GPU
encode was not uploaded during this compression-only request.
