# Full opening cinematic at 30 fps

Completed 2026-10-08 after the user selected the
[30 fps pilot](opening-cinematic-30fps-pilot.md). The existing general-model
2880x2160 lossless upscale was identity-checked and processed using the pilot's
installed RIFE v4.6 weights, UHD mode, multiplier 2, scene threshold 20, and
RX 9070 Vulkan device 0. No additional tools or models were downloaded.

The full RIFE pass took 874.47 seconds, reporting 5473 output frames. One final
held picture was appended, as in the pilot, yielding 5474 frames at 30/1 fps and
the original 182.466667-second video timeline. The original seven-sample-frame
audio tail is retained. The lossless master contains all 4023397 stereo 22050 Hz
16-bit PCM sample frames, byte-identical to the original source. PCM SHA-256:
`27e76684cec7fe93684d2ba9bf16fde87c245c52006626fa0efe7e909f8d68f6`.

Outputs remain under ignored `local/work-ahead/opening-cinematic-30fps-full-v1/`:

| File | Purpose | Bytes |
| --- | --- | ---: |
| `rife-30fps-raw.mkv` | Raw FFV1 RIFE result | 11409645218 |
| `opening-2160p-30fps-master.mkv` | Final FFV1 and original PCM master | 11416514846 |
| `opening-2160p-30fps-review.mp4` | Full-quality H.264/AAC review export | 638541662 |

The master timeline checks allow 1 ms for Matroska timestamp rounding. Observed
maximum video error was 0.333334 ms and maximum continuous PCM timestamp error
was 0.480726 ms. Header duration rounding is within 1 ms of the exact complete
audio duration. The final MP4 has 5474 fully decoded video frames, exact 30/1
fps, 2880x2160 dimensions and 182.466984-second duration. Normalization and
review encoding decode their inputs with FFmpeg `-xerror`.

The final master render took 142.82 seconds; the review encode took 305.82
seconds. The review retains the sample's H.264 CRF16, slow preset, yuv420p and
AAC 192k settings, without a bitrate cap or extra compression for transfer.
Review MP4 SHA-256:
`aa7b96adff393f21d6a17d52bf56320687bd611ff5f84331dc54c00d2cf7302b`.

`manifest.json` records exact command vectors, measured stage times, installed
tool and model hashes, validated source identity and output checks/hashes.
`interpolate_opening_cinematic.py` is the full-movie preparation workflow.
Eight opening-source and interpolation tests pass, including the new full-length
30 fps grid, missing endpoint, timestamp-gap, rate and offset checks.

## Remote download

The connector's 100 MiB limit is handled with seven exact byte parts: six of
94371840 bytes and one of 72310622 bytes. No re-encoding occurs during packaging.
Concatenated part SHA-256 matches the validated MP4. `parts.json` contains
per-part hashes; `reassemble.py` verifies parts before writing and verifies the
finished movie. `Reassemble.cmd` provides Windows binary concatenation and
prints the final checksum. Neither script overwrites an existing output.
Two authored package round-trip/corruption tests pass.

The [private download folder](https://drive.google.com/drive/folders/1P1AvKsOllFM649BY7gL1RuXJV7YJCjGy)
contains all seven parts, both reassembly scripts, the part manifest and a
README. All eleven uploads were read back; part sizes and folder placement
match the local package. `upload-receipt.json` records file IDs and verification.
Download the whole folder, extract Drive's ZIP, and run the reassembly script
to obtain a single full-quality MP4. Parts cannot be played independently.

Status: technical validation passed; full-speed whole-movie perceptual review
and game playback integration remain pending. Scene detection is heuristic;
review cuts, moving edges, weapons, explosions and audio sync before integration.
