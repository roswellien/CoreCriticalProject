"""Read-only frame-grid, duration and exact PCM verification for local pilot masters."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def verify_grid(timestamps, frame_count=75):
    if len(timestamps) != frame_count:
        raise ValueError(f"Expected {frame_count} display frames, found {len(timestamps)}")
    maximum_error = max(abs(float(timestamp) - index / 15) for index, timestamp in enumerate(timestamps))
    if maximum_error > 0.001:
        raise ValueError(f"Display-frame timestamps depart from 15 fps grid: {maximum_error}")
    return maximum_error


def verify_audio_grid(frames, sample_rate=22050, sample_count=110250):
    samples = 0
    maximum_error = 0
    for frame in frames:
        count = int(frame["nb_samples"])
        if count <= 0:
            raise ValueError("Audio frame has no samples")
        error = abs(float(frame["best_effort_timestamp_time"]) - samples / sample_rate)
        maximum_error = max(maximum_error, error)
        samples += count
    if samples != sample_count:
        raise ValueError("Audio-frame sample count differs from exact excerpt")
    if maximum_error > 0.001:
        raise ValueError("Audio-frame timestamps depart from continuous zero-start sample grid")
    return maximum_error


def digest_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect(path, ffprobe, ffmpeg, expected_size):
    probe = json.loads(subprocess.run([ffprobe, "-v", "error", "-count_frames", "-show_frames", "-show_streams",
                                      "-show_format", "-of", "json", str(path)], capture_output=True,
                                     text=True, check=True).stdout)
    frames = [f for f in probe["frames"] if f["media_type"] == "video"]
    error = verify_grid([f["best_effort_timestamp_time"] for f in frames])
    audio_frames = [f for f in probe["frames"] if f["media_type"] == "audio"]
    audio_error = verify_audio_grid(audio_frames)
    videos = [s for s in probe["streams"] if s["codec_type"] == "video"]
    audios = [s for s in probe["streams"] if s["codec_type"] == "audio"]
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError("Expected one video and one audio stream")
    video, audio = videos[0], audios[0]
    if (video["width"], video["height"]) != expected_size or video["r_frame_rate"] != "15/1":
        raise ValueError("Unexpected video dimensions/rate")
    if abs(float(probe["format"]["duration"]) - 5) > 0.001:
        raise ValueError("Pilot duration differs from five seconds")
    if audio["codec_name"] != "pcm_u8" or audio["channels"] != 1 or audio["sample_rate"] != "22050":
        raise ValueError("Lossless master audio format differs from source")
    pcm = subprocess.run([ffmpeg, "-v", "error", "-i", str(path), "-map", "0:a:0", "-c:a", "pcm_u8",
                          "-f", "u8", "pipe:1"], capture_output=True, check=True).stdout
    if len(pcm) != 110250:
        raise ValueError("Pilot PCM sample count differs from exact source excerpt")
    return {"file": path.name, "sha256": digest_file(path), "bytes": path.stat().st_size,
            "dimensions": list(expected_size), "frames": len(frames), "duration_seconds": 5,
            "frame_rate": "15/1", "max_timestamp_error_seconds": error,
            "max_audio_timestamp_error_seconds": audio_error,
            "pcm_samples": len(pcm), "pcm_sha256": hashlib.sha256(pcm).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    ffprobe, ffmpeg = shutil.which("ffprobe"), shutil.which("ffmpeg")
    if not ffprobe or not ffmpeg:
        parser.error("Local FFmpeg/FFprobe required")
    directory = args.directory.resolve()
    local = (Path(__file__).resolve().parents[2] / "local/work-ahead").resolve()
    if not directory.is_relative_to(local):
        parser.error("Reports belong in ignored local/work-ahead")
    records = [inspect(directory / "source-5s.mkv", ffprobe, ffmpeg, (640, 480))]
    for name in ("lanczos2x-master.mkv", "ai-native2x-master.mkv", "ai-general2x-master.mkv"):
        records.append(inspect(directory / name, ffprobe, ffmpeg, (1280, 960)))
    original_pcm = subprocess.run([ffmpeg, "-v", "error", "-i", str(directory / "source.avi"), "-map", "0:a:0",
                                   "-af", "atrim=start_sample=0:end_sample=110250", "-c:a", "pcm_u8",
                                   "-f", "u8", "pipe:1"], capture_output=True, check=True).stdout
    expected_audio = hashlib.sha256(original_pcm).hexdigest()
    if len(original_pcm) != 110250 or any(item["pcm_sha256"] != expected_audio for item in records):
        raise ValueError("Master audio differs from original excerpt")
    report = {"status": "frame-count/timing/audio checks passed; perceptual motion review pending",
              "source_excerpt_pcm_sha256": expected_audio, "masters": records,
              "validator_sha256": digest_file(Path(__file__)),
              "ffmpeg_sha256": digest_file(Path(ffmpeg)), "ffprobe_sha256": digest_file(Path(ffprobe))}
    with (directory / "validation.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
