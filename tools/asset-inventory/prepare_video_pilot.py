"""Hash-bound local extraction and exact-frame/sample short-video preparation."""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
import shutil
import subprocess

from video_probe import avi_metadata, iso_files, span_hash


def extract_selected(iso, expected_iso_hash, disc_path, expected_asset_hash):
    with iso.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        if span_hash(data, 0, len(data)) != expected_iso_hash:
            raise ValueError("ISO identity differs from expected source")
        matches = [item for item in iso_files(data)["files"] if item["path"] == disc_path]
        if len(matches) != 1:
            raise ValueError("Exactly one requested disc entry required")
        entry = matches[0]
        if entry["bytes"] > 64 * 1024 * 1024:
            raise ValueError("Pilot input exceeds bounded extraction limit")
        payload = data[entry["offset"]:entry["offset"] + entry["bytes"]]
        if hashlib.sha256(payload).hexdigest() != expected_asset_hash:
            raise ValueError("Selected file identity differs from expected source")
    return entry, payload


def run_tool(executable, arguments, log_path):
    command = [str(executable), *arguments]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log_path.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Tool failed with exit {result.returncode}; see {log_path}")
    return command


def validate_contract(payload, start_frame, frames):
    metadata = avi_metadata(payload, 0, len(payload))
    videos = [s for s in metadata["streams"] if s["type"] == "vids"]
    audio = [s for s in metadata["streams"] if s["type"] == "auds"]
    if len(videos) != 1 or len(audio) != 1:
        raise ValueError("One video and one audio stream required")
    video = videos[0]
    if video["rate"] != 15 * video["scale"] or video["start"]:
        raise ValueError("Pilot requires the observed zero-start 15 fps stream")
    if audio[0]["audio_format"] != {"format_tag": 1, "channels": 1, "sample_rate": 22050,
                                    "byte_rate": 22050, "block_align": 1, "bits_per_sample": 8}:
        # A WAVEFORMATEX zero-sized extension is equivalent to bare PCM.
        fmt = dict(audio[0]["audio_format"])
        fmt.pop("extra_format_bytes", None)
        if fmt != {"format_tag": 1, "channels": 1, "sample_rate": 22050,
                   "byte_rate": 22050, "block_align": 1, "bits_per_sample": 8}:
            raise ValueError("Pilot requires the observed mono 22050 Hz 8-bit PCM")
    if (audio[0]["start"] or audio[0]["scale"] != 1 or audio[0]["rate"] != 22050
            or audio[0]["sample_size"] != 1 or (start_frame + frames) * 1470 > audio[0]["length"]
            or start_frame < 0 or frames < 1 or start_frame + frames > video["length"]):
        raise ValueError("Pilot range exceeds source or source audio has an offset")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--expect-iso-sha256", required=True)
    parser.add_argument("--disc-path", required=True)
    parser.add_argument("--expect-asset-sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=75)
    parser.add_argument("--ffmpeg", type=Path, default=shutil.which("ffmpeg"))
    args = parser.parse_args()
    local = (Path(__file__).resolve().parents[2] / "local/work-ahead").resolve()
    output = args.output_dir.resolve()
    if not output.is_relative_to(local) or output == local or output.exists():
        parser.error("Output must be a fresh subdirectory of ignored local/work-ahead")
    if not args.ffmpeg or not args.ffmpeg.is_file():
        parser.error("A local FFmpeg executable is required")
    if args.start_frame < 0 or not 1 <= args.frames <= 150:
        parser.error("Pilot requires a nonnegative start and 1-150 frames")
    entry, payload = extract_selected(args.iso, args.expect_iso_sha256.lower(), args.disc_path,
                                     args.expect_asset_sha256.lower())
    source_metadata = validate_contract(payload, args.start_frame, args.frames)
    output.mkdir(parents=True)
    with (output / "source.avi").open("xb") as stream:
        stream.write(payload)
    ffmpeg = args.ffmpeg.resolve()
    version = subprocess.run([str(ffmpeg), "-version"], capture_output=True, text=True, check=True).stdout
    # This first pilot contract is the observed 15/1 fps, 22050 Hz mono 8-bit PCM.
    # Source headers and output validation are recorded separately; unsupported
    # inputs must not be assumed to satisfy these timing/audio constants.
    start_sample = args.start_frame * 1470
    end_sample = (args.start_frame + args.frames) * 1470
    filters = (f"[0:v]fps=15,trim=start_frame={args.start_frame}:end_frame={args.start_frame + args.frames},setpts=N/(15*TB)[v];"
               f"[0:a]atrim=start_sample={start_sample}:end_sample={end_sample},asetpts=PTS-STARTPTS[a]")
    commands = []
    commands.append(run_tool(ffmpeg, ["-hide_banner", "-nostdin", "-n", "-xerror", "-i", str(output / "source.avi"),
                                     "-filter_complex", filters, "-map", "[v]", "-map", "[a]", "-c:v", "ffv1",
                                     "-level", "3", "-c:a", "pcm_u8", "-fps_mode", "passthrough",
                                     str(output / "source-5s.mkv")], output / "decode.log"))
    commands.append(run_tool(ffmpeg, ["-hide_banner", "-nostdin", "-n", "-i", str(output / "source-5s.mkv"),
                                     "-vf", "select=eq(n\\,0)+eq(n\\,15)+eq(n\\,30)+eq(n\\,45)+eq(n\\,60),tile=5x1",
                                     "-frames:v", "1", "-an", str(output / "source-contact-sheet.png")], output / "contact-sheet.log"))
    report = {"status": "decoded-reference; validation pending", "iso_sha256": args.expect_iso_sha256.lower(),
              "disc_path": args.disc_path, "source_asset_sha256": args.expect_asset_sha256.lower(),
              "source_entry": entry, "start_frame": args.start_frame, "frames": args.frames,
              "source_metadata": source_metadata,
              "timing_policy": "Reconstruct display holds on original 15 fps grid before frame trim; no motion interpolation",
              "frame_rate": "15/1", "audio_sample_rate": 22050, "audio_samples": args.frames * 1470,
              "ffmpeg_version": version, "ffmpeg_sha256": hashlib.sha256(ffmpeg.read_bytes()).hexdigest(),
              "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "commands": commands}
    (output / "preparation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {args.frames} frames from {args.disc_path} in {output}")


if __name__ == "__main__":
    main()
