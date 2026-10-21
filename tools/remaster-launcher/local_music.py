"""Prepare user-supplied FLAC music for the native CD-audio service.

Configuration lives in local/remaster/music.json. Sources remain read-only;
decoded WAVs, their receipt and the MW3CD1 tracklist stay in local storage.
CD tracks 2/3 correspond to the first/second audio tracks; the data track is 1.
"""

from pathlib import Path
import hashlib, json, os, struct, subprocess, wave


def sha(path):
    """Stream a file's SHA-256 without retaining its audio samples in memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def atomic(path, data):
    """Replace one owned output through a sibling file; callers serialize writers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def configuration(root):
    """Return enabled schema-v1 settings, None when disabled, or raise on bad inputs."""
    path = root / "local/remaster/music.json"
    if not path.exists():
        return None
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    if not config.get("enabled", False):
        return None
    if config.get("schema_version") != 1:
        raise RuntimeError("Unsupported local music configuration")
    if [t["cd_track"] for t in config["tracks"]] != [2, 3]:
        raise RuntimeError("MW3 local music requires CD tracks 2 and 3")
    for track in config["tracks"]:
        if not (root / track["source"]).is_file():
            raise RuntimeError("Local music source is missing: " + track["source"])
    if not (root / config["decoder"]).is_file():
        raise RuntimeError("The local music preparation tool is missing")
    return config


def stream_info(path):
    """Read FLAC STREAMINFO; return stereo PCM frame count and its declared MD5.

    Frames contain one sample for each channel, so 16-bit stereo consumes four
    PCM bytes per frame. The MD5 identifies decoded PCM, not the FLAC container.
    """
    with path.open("rb") as stream:
        if stream.read(4) != b"fLaC":
            raise RuntimeError("Local music source must be FLAC: " + str(path))
        header = stream.read(4)
        if len(header) != 4 or header[0] & 127 or int.from_bytes(header[1:], "big") != 34:
            raise RuntimeError("Invalid FLAC stream information: " + str(path))
        block = stream.read(34)
    if len(block) != 34:
        raise RuntimeError("Truncated FLAC stream information: " + str(path))
    packed = int.from_bytes(block[10:18], "big")
    rate = packed >> 44
    channels = ((packed >> 41) & 7) + 1
    bits = ((packed >> 36) & 31) + 1
    frames = packed & ((1 << 36) - 1)
    if (rate, channels, bits) != (44100, 2, 16) or not frames:
        raise RuntimeError("Local music must be stereo 16-bit/44100 Hz FLAC")
    return frames, block[18:34].hex()


def verify_wav(path, expected_frames, expected_md5):
    """Check decoded PCM format/length and return its MD5.

    FLAC permits an all-zero checksum when no source checksum was supplied;
    format and sample-count checks still apply in that case. MD5 here is the
    format's PCM identity, not a trust or executable-admission mechanism.
    """
    digest = hashlib.md5()
    with wave.open(str(path), "rb") as stream:
        if (
            stream.getnchannels(),
            stream.getsampwidth(),
            stream.getframerate(),
            stream.getnframes(),
            stream.getcomptype(),
        ) != (2, 2, 44100, expected_frames, "NONE"):
            raise RuntimeError("Prepared music format/sample count mismatch: " + str(path))
        total = 0
        while chunk := stream.readframes(65536):
            digest.update(chunk)
            total += len(chunk)
    if total != expected_frames * 4:
        raise RuntimeError("Prepared music is truncated: " + str(path))
    actual = digest.hexdigest()
    if expected_md5 != "0" * 32 and actual != expected_md5:
        raise RuntimeError("Decoded music does not match its FLAC PCM checksum: " + str(path))
    return actual


def prepare_music(root):
    """Reuse verified WAVs or decode locally, then return the native tracklist binding.

    Source, decoder and cached-output identities all participate in reuse.
    Decode/verification failures raise before publishing the new tracklist.
    """
    config = configuration(root)
    if config is None:
        return {}
    decoder = root / config["decoder"]
    decoder_sha = sha(decoder)
    directory = root / "local/remaster/prepared/music"
    directory.mkdir(parents=True, exist_ok=True)
    receipt_path = directory / "receipt.json"
    previous = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    records = []
    # MW3CD1: magic[8], version/count:u32, then track/rate/channels/bits:u32,
    # sample_frames:u64, UTF-8 path length:u32 and the absolute WAV path bytes.
    manifest = bytearray(b"MW3CD1\0\0" + struct.pack("<II", 1, 2))
    for track in config["tracks"]:
        source = (root / track["source"]).resolve()
        frames, pcm_md5 = stream_info(source)
        source_sha = sha(source)
        destination = directory / f"track{track['cd_track']:02d}.wav"
        cached = next(
            (item for item in previous.get("tracks", []) if item["cd_track"] == track["cd_track"]),
            {},
        )
        valid = (
            destination.exists()
            and cached.get("source_sha256") == source_sha
            and cached.get("decoder_sha256") == decoder_sha
            and cached.get("wav_sha256") == sha(destination)
        )
        if not valid:
            print("Preparing local music: " + source.name, flush=True)
            temporary = destination.with_suffix(".wav.tmp")
            result = subprocess.run(
                [str(decoder), str(source), str(temporary)], capture_output=True, text=True
            )
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or "Local music decoding failed")
            actual_pcm_md5 = verify_wav(temporary, frames, pcm_md5)
            if sha(source) != source_sha:
                raise RuntimeError("Music source changed during preparation: " + str(source))
            os.replace(temporary, destination)
        else:
            actual_pcm_md5 = cached["pcm_md5"]
        record = dict(
            cd_track=track["cd_track"],
            source=str(source),
            source_sha256=source_sha,
            decoder_sha256=decoder_sha,
            wav=str(destination),
            wav_sha256=sha(destination),
            sample_frames=frames,
            rate=44100,
            channels=2,
            bits=16,
            pcm_md5=actual_pcm_md5,
        )
        records.append(record)
        encoded = str(destination.resolve()).encode("utf-8")
        manifest.extend(
            struct.pack("<IIIIQI", track["cd_track"], 44100, 2, 16, frames, len(encoded))
        )
        manifest.extend(encoded)
    manifest_path = directory / "tracklist.bin"
    atomic(manifest_path, manifest)
    atomic(
        receipt_path,
        (
            json.dumps(dict(schema_version=1, decoder=str(decoder), tracks=records), indent=2)
            + "\n"
        ).encode(),
    )
    return {"MW34_MUSIC_PACK": str(manifest_path)}
