"""Split a local movie into exact byte parts; verify reconstruction without re-encoding."""
import argparse
import hashlib
import json
from pathlib import Path
import re

PART_BYTES = 90 * 1024 * 1024

JOIN_SCRIPT = '''"""Reassemble the movie and verify all parts. No existing files are overwritten."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / "parts.json").read_text())
output = root / manifest["output_filename"]
if output.exists():
    raise SystemExit("Output already exists; refusing overwrite: " + str(output))
for part in manifest["parts"]:
    path = root / part["file"]
    if path.name != part["file"] or not path.is_file():
        raise SystemExit("Missing or invalid part: " + part["file"])
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != part["sha256"] or path.stat().st_size != part["bytes"]:
        raise SystemExit("Part integrity check failed: " + part["file"])
digest = hashlib.sha256()
with output.open("xb") as destination:
    for part in manifest["parts"]:
        with (root / part["file"]).open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                destination.write(block)
                digest.update(block)
if digest.hexdigest() != manifest["sha256"]:
    raise SystemExit("Final SHA-256 verification failed")
print("Verified full-quality movie: " + str(output))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('movie', type=Path)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--basename', default='opening-2160p-30fps')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.basename):
        parser.error('Package basename must contain only letters, digits, underscores or hyphens')
    movie_name = args.basename + '.mp4'
    local = (Path(__file__).resolve().parents[2] / 'local/work-ahead').resolve()
    source, output = args.movie.resolve(), args.directory.resolve()
    if not source.is_relative_to(local) or not output.is_relative_to(local) or output.exists():
        parser.error('Source and fresh package must be under local/work-ahead')
    output.mkdir()
    records = []
    total = hashlib.sha256()
    with source.open('rb') as stream:
        while data := stream.read(PART_BYTES):
            name = f'{movie_name}.part{len(records) + 1:03}'
            with (output / name).open('xb') as part:
                part.write(data)
            records.append({'file': name, 'bytes': len(data),
                            'sha256': hashlib.sha256(data).hexdigest()})
            total.update(data)
    manifest = {'source_filename': source.name, 'output_filename': movie_name,
                'bytes': source.stat().st_size, 'sha256': total.hexdigest(),
                'part_bytes': PART_BYTES, 'parts': records,
                'policy': 'Exact byte splitting; no additional compression or re-encoding.'}
    reconstructed = hashlib.sha256()
    for record in records:
        with (output / record['file']).open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                reconstructed.update(block)
    if reconstructed.hexdigest() != total.hexdigest():
        raise ValueError('Package reconstruction differs from movie')
    (output / 'parts.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'reassemble.py').write_text(JOIN_SCRIPT)
    concat = '+'.join('"' + r['file'] + '"' for r in records)
    (output / 'Reassemble.cmd').write_text(
        '@echo off\ncd /d "%~dp0"\n'
        f'if exist "{movie_name}" (echo Output already exists. & pause & exit /b 1)\n'
        'copy /b ' + concat + f' "{movie_name}"\n'
        'if errorlevel 1 (echo Reassembly failed. & pause & exit /b 1)\n'
        f'certutil -hashfile "{movie_name}" SHA256\n'
        'echo Expected SHA256: ' + total.hexdigest() + '\npause\n')
    (output / 'README.txt').write_text(
        f'MechWarrior 3 {args.basename} - 2880x2160, 30 fps\n\n'
        'Download this entire folder from Google Drive, then extract its ZIP.\n'
        'Keep every .part file and the reassembly files together in one folder.\n'
        'Windows: double-click Reassemble.cmd. Compare its printed SHA256 with the value below.\n'
        'With Python 3: run python reassemble.py (automatically verifies all hashes).\n'
        f'The result is {movie_name}, playable as one complete movie.\n\n'
        'The parts are exact bytes of the full-quality CRF16 export. No extra compression.\n'
        'The .part files cannot be played separately. Existing outputs are not overwritten.\n'
        f'Total bytes: {manifest["bytes"]}\nSHA256: {manifest["sha256"]}\n')
    print(json.dumps({'directory': str(output), 'parts': len(records),
                      'bytes': manifest['bytes'], 'reconstruction_verified': True}))


if __name__ == '__main__':
    main()
