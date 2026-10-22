"""Build a local soundtrack .mw3pack from user-supplied audio; never downloads inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import wave
import zipfile

from local_music import stream_info


def build(first, second, output, pack_id="local.cd-soundtrack", name="CD Audio Soundtrack"):
    sources = [Path(first).resolve(strict=True), Path(second).resolve(strict=True)]
    output = Path(output).resolve()
    if sources[0] == sources[1]:
        raise ValueError("Select two different soundtrack files")
    import re
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,127}", pack_id) or pack_id.endswith('.'):
        raise ValueError("Invalid pack ID")
    members = {}
    tracks = []
    for number, source in zip((2, 3), sources):
        suffix = source.suffix.lower()
        if suffix == '.flac':
            stream_info(source)
        elif suffix == '.wav':
            with wave.open(str(source), 'rb') as audio:
                if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getcomptype()) != (2, 2, 44100, 'NONE') or not audio.getnframes():
                    raise ValueError("Soundtrack WAV must be nonempty stereo 16-bit/44100 Hz PCM")
        else:
            raise ValueError("Soundtrack sources must be FLAC or PCM WAV")
        relative = f"music/track{number:02}{suffix}"
        members[relative] = source.read_bytes()
        tracks.append(dict(cd_track=number, source=relative))
    members['music/music.json'] = json.dumps(dict(schema_version=2, payload_profile='prepared-music-v1', tracks=tracks), indent=2).encode()
    manifest = dict(schema_version=2, id=pack_id, name=name, version='1.0.0', category='Music',
                    provides=dict(cd_music=True), native_payload=dict(profile='prepared-music-v1', registry='music/music.json', path_base='pack-root'),
                    files={key: dict(bytes=len(value), sha256=hashlib.sha256(value).hexdigest()) for key, value in members.items()})
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects both prior packs and the user's source files.
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED) as archive:
        archive.writestr('pack.json', json.dumps(manifest, indent=2))
        for relative, content in members.items():
            archive.writestr(relative, content)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--track-2', type=Path, required=True)
    parser.add_argument('--track-3', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--id', default='local.cd-soundtrack')
    parser.add_argument('--name', default='CD Audio Soundtrack')
    args = parser.parse_args()
    print(build(args.track_2, args.track_3, args.output, args.id, args.name))
