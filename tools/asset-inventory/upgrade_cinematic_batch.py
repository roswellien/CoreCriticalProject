"""Hash-bound, resumable MW3 disc-video batch: general 4x, 2160p, RIFE 30 fps."""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from interpolate_opening_cinematic import check_grid
from validate_video_pilot import digest_file, verify_audio_grid
from video_probe import avi_metadata, iso_files, span_hash


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def contract(metadata, expected):
    videos = [s for s in metadata['streams'] if s['type'] == 'vids']
    audios = [s for s in metadata['streams'] if s['type'] == 'auds']
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError('One original video/audio stream required')
    video, audio = videos[0], audios[0]
    fmt = dict(audio['audio_format'])
    fmt.pop('extra_format_bytes', None)
    if (video['handler'] != 'IV50' or video['start'] != 0
            or video['rate'] != 15 * video['scale'] or video['length'] != expected['frames']
            or video['video_format']['width'] != 640 or video['video_format']['height'] != 480
            or audio['start'] != 0 or fmt != expected['audio']
            or fmt['format_tag'] != 1 or fmt['sample_rate'] != 22050
            or (fmt['channels'], fmt['bits_per_sample']) not in ((1, 8), (2, 16))
            or audio['sample_size'] != fmt['block_align']
            or audio['rate'] != audio['scale'] * 22050
            or audio['length'] * fmt['block_align'] != audio['observed_data_bytes'].get('01wb')):
        raise ValueError('Disc-video stream contract differs from inventory')
    return {'frames': video['length'], 'samples': audio['length'],
            'channels': fmt['channels'], 'bits': fmt['bits_per_sample'],
            'align': fmt['block_align'], 'rate': 22050,
            'codec': 'pcm_u8' if fmt['bits_per_sample'] == 8 else 'pcm_s16le',
            'raw_format': 'u8' if fmt['bits_per_sample'] == 8 else 's16le',
            'duration': max(video['length'] / 15, audio['length'] / 22050)}


def pcm_hash(path, audio, ffmpeg):
    data = subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(path),
        '-map', '0:a:0', '-c:a', audio['codec'], '-f', audio['raw_format'], 'pipe:1'],
        capture_output=True, check=True).stdout
    if len(data) != audio['samples'] * audio['align']:
        raise ValueError('Decoded PCM size differs from complete original stream')
    return hashlib.sha256(data).hexdigest()


def inspect(path, size, frames, rate, audio, expected_pcm, ffprobe, ffmpeg, lossless):
    info = json.loads(subprocess.run([ffprobe, '-v', 'error', '-show_packets',
        '-show_streams', '-show_format', '-of', 'json', str(path)],
        capture_output=True, text=True, check=True).stdout)
    vs = [s for s in info['streams'] if s['codec_type'] == 'video']
    aus = [s for s in info['streams'] if s['codec_type'] == 'audio']
    if len(vs) != 1 or len(aus) != 1:
        raise ValueError('Unexpected output stream count')
    v, a = vs[0], aus[0]
    if (v['width'], v['height'], v['r_frame_rate']) != (*size, f'{rate}/1'):
        raise ValueError('Unexpected output dimensions/rate')
    error = check_grid([p['pts_time'] for p in info['packets']
                        if p['stream_index'] == v['index']], frames, rate)
    if abs(float(info['format']['duration']) - audio['duration']) > 0.002:
        raise ValueError('Output duration differs from original complete timeline')
    if a['channels'] != audio['channels'] or a['sample_rate'] != '22050':
        raise ValueError('Output channel count/sample rate differs')
    record = {'file': path.name, 'bytes': path.stat().st_size, 'sha256': digest_file(path),
              'frames': frames, 'rate': rate, 'dimensions': list(size),
              'duration_seconds': float(info['format']['duration']),
              'max_video_timestamp_error_seconds': error}
    if lossless:
        if a['codec_name'] != audio['codec'] or pcm_hash(path, audio, ffmpeg) != expected_pcm:
            raise ValueError('Original PCM identity/format differs')
        af = json.loads(subprocess.run([ffprobe, '-v', 'error', '-select_streams', 'a:0',
            '-show_frames', '-of', 'json', str(path)],
            capture_output=True, text=True, check=True).stdout)['frames']
        record['max_audio_timestamp_error_seconds'] = verify_audio_grid(af, 22050, audio['samples'])
        record['pcm_sha256'] = expected_pcm
        record['pcm_samples'] = audio['samples']
    else:
        decoded = json.loads(subprocess.run([ffprobe, '-v', 'error', '-select_streams',
            'v:0', '-count_frames', '-show_streams', '-of', 'json', str(path)],
            capture_output=True, text=True, check=True).stdout)['streams'][0]
        if int(decoded['nb_read_frames']) != frames or a['codec_name'] != 'aac':
            raise ValueError('Review decoded frames/audio codec differ')
        record['decoded_frames'] = frames
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    local = (root / 'local/work-ahead').resolve()
    output = args.directory.resolve()
    if output == local or not output.is_relative_to(local) or (output.exists() and not args.resume):
        parser.error('Use a fresh local/work-ahead directory, or --resume its existing batch')
    summary = json.loads((local / 'video-discovery/video-summary.json').read_text())
    inventory = json.loads((local / 'video-discovery/disc-video-inventory.json').read_text())
    pilot = json.loads((local / 'opening-cinematic-30fps-v1/manifest.json').read_text())
    upscale = json.loads((local / 'video-pilot-v2/manifest.json').read_text())
    verified_tools = pilot['tools_and_weights'] + [m for m in upscale['models']
                                                  if 'realesrgan-plus-x4' in m['file']]
    for item in verified_tools:
        if digest_file(Path(item['path'])) != item['sha256']:
            raise ValueError('Installed tool/model differs from admitted pilot')
    ffmpeg = next(x['path'] for x in verified_tools if Path(x['path']).name.lower() == 'ffmpeg.exe')
    ffprobe = next(x['path'] for x in verified_tools if Path(x['path']).name.lower() == 'ffprobe.exe')
    video2x = next(x['path'] for x in verified_tools if Path(x['path']).name.lower() == 'video2x.exe')
    files = [f for f in summary['files'] if f['path'] != 'VIDEO/INTRO.AVI;1']
    priorities = {'VIDEO/C4WIN.AVI;1': 0, 'VIDEO/CAMPAIGN.AVI;1': 1,
                  'VIDEO/C1.AVI;1': 2, 'VIDEO/C2.AVI;1': 3, 'VIDEO/C3.AVI;1': 4}
    files.sort(key=lambda f: (priorities.get(f['path'], 5), f['path']))
    if len(files) != 18 or sum(f['frames'] for f in files) != 13674:
        raise ValueError('Remaining disc-video inventory differs')
    output.mkdir(exist_ok=args.resume)
    batch_path = output / 'batch.json'
    state = json.loads(batch_path.read_text()) if args.resume else {
        'status': 'verifying and extracting sources', 'source_iso_sha256': summary['source_sha256'],
        'tools_and_weights': verified_tools, 'workflow_sha256': digest_file(Path(__file__)),
        'target': {'dimensions': [2880, 2160], 'fps': 30, 'review_crf': 16,
                   'realesrgan': 'realesrgan-plus 4x', 'rife': 'v4.6 UHD 2x threshold 20'},
        'jobs': []}
    write_json(batch_path, state)
    iso = root / 'MW3/MechWarrior-3_Win_EN_ISO-Version/Mechwarrior 3.iso'
    with iso.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        if len(data) != summary['source_bytes'] or span_hash(data, 0, len(data)) != summary['source_sha256']:
            raise ValueError('ISO identity mismatch')
        entries = {x['path']: x for x in iso_files(data)['files']}
        recorded = {x['path']: x for x in inventory['files']}
        for expected in files:
            clip = expected['path'].split('/')[1].split('.')[0]
            if not re.fullmatch(r'[A-Z0-9]+', clip):
                raise ValueError('Invalid clip identifier')
            entry = entries[expected['path']]
            evidence = recorded[expected['path']]
            if entry['offset'] != evidence['offset'] or entry['bytes'] != expected['bytes']:
                raise ValueError('Disc entry bounds differ from inventory')
            payload = data[entry['offset']:entry['offset'] + entry['bytes']]
            if hashlib.sha256(payload).hexdigest() != expected['sha256']:
                raise ValueError('Disc-video identity mismatch')
            audio = contract(avi_metadata(payload, 0, len(payload)), expected)
            folder = output / clip
            folder.mkdir(exist_ok=True)
            source = folder / 'source.avi'
            if source.exists():
                if digest_file(source) != expected['sha256']:
                    raise ValueError('Existing extracted source identity mismatch')
            else:
                with source.open('xb') as extracted:
                    extracted.write(payload)
            if not any(j['id'] == clip for j in state['jobs']):
                state['jobs'].append({'id': clip, 'source': expected, 'entry': entry,
                                      'contract': audio, 'status': 'source verified'})
    write_json(batch_path, state)

    for job in state['jobs']:
        if job['status'] == 'technical validation passed; download ready':
            continue
        clip, audio = job['id'], job['contract']
        folder = output / clip
        source = folder / 'source.avi'
        manifest_path = folder / 'manifest.json'
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
            'source': job['source'], 'contract': audio, 'commands': [], 'checks': [],
            'source_pcm_sha256': pcm_hash(source, audio, ffmpeg)}
        expected_pcm = manifest['source_pcm_sha256']
        n = audio['frames']

        def save():
            write_json(manifest_path, manifest)
            write_json(batch_path, state)

        def stage(name, executable, argv, size, count, rate, lossless=True):
            path = folder / name
            existing = next((c for c in manifest['checks'] if c['file'] == name), None)
            if path.exists() and existing and digest_file(path) == existing['sha256']:
                return
            if path.exists():
                raise ValueError('Unvalidated or changed output exists: ' + str(path))
            job['status'] = 'processing ' + name
            state['status'] = clip + ': ' + job['status']
            save()
            command = [executable, *argv, str(path)]
            print(clip + ': ' + job['status'], flush=True)
            started = time.monotonic()
            with (folder / (name + '.log')).open('w') as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            manifest['commands'].append({'argv': command, 'seconds': time.monotonic() - started,
                                          'exit_code': result.returncode})
            job['status'] = 'validating ' + name
            state['status'] = clip + ': ' + job['status']
            save()
            if result.returncode:
                raise RuntimeError('Stage failed: ' + name)
            manifest['checks'].append(inspect(path, size, count, rate, audio, expected_pcm,
                                               ffprobe, ffmpeg, lossless))
            save()

        try:
            stage('reference.mkv', ffmpeg, ['-hide_banner', '-nostdin', '-n', '-xerror',
                '-i', str(source), '-vf', f'fps=15,tpad=stop_mode=clone:stop_duration={n/15},trim=end_frame={n},setpts=N/(15*TB)',
                '-map', '0:v:0', '-map', '0:a:0', '-c:v', 'ffv1', '-level', '3',
                '-c:a', 'copy', '-fps_mode', 'passthrough'], (640, 480), n, 15)
            stage('general4x.mkv', video2x, ['-i', str(folder / 'reference.mkv'), '-p',
                'realesrgan', '-s', '4', '--realesrgan-model', 'realesrgan-plus', '-d', '0',
                '-c', 'ffv1', '--pix-fmt', 'yuv444p', '--no-progress', '-o'], (2560, 1920), n, 15)
            stage('upscaled-2160p-15fps.mkv', ffmpeg, ['-hide_banner', '-nostdin', '-n',
                '-xerror', '-i', str(folder / 'general4x.mkv'), '-map', '0:v:0', '-map', '0:a:0',
                '-vf', 'scale=2880:2160:flags=lanczos,setsar=1', '-c:v', 'ffv1', '-level', '3',
                '-c:a', 'copy', '-fps_mode', 'passthrough'], (2880, 2160), n, 15)
            stage('rife-30fps-raw.mkv', video2x, ['-i', str(folder / 'upscaled-2160p-15fps.mkv'),
                '-p', 'rife', '--rife-model', 'rife-v4.6', '--rife-uhd', '-m', '2', '-t', '20',
                '-d', '0', '-c', 'ffv1', '--pix-fmt', 'yuv444p', '--no-progress', '-o'],
                (2880, 2160), n * 2 - 1, 30)
            stage('master-2160p-30fps.mkv', ffmpeg, ['-hide_banner', '-nostdin', '-n', '-xerror',
                '-i', str(folder / 'rife-30fps-raw.mkv'), '-map', '0:v:0', '-map', '0:a:0',
                '-vf', f'tpad=stop_mode=clone:stop_duration=0.033333334,trim=end_frame={n*2},setpts=N/(30*TB)',
                '-c:v', 'ffv1', '-level', '3', '-c:a', 'copy', '-fps_mode', 'passthrough'],
                (2880, 2160), n * 2, 30)
            review_name = clip + '-2160p-30fps.mp4'
            stage(review_name, ffmpeg, ['-hide_banner', '-nostdin', '-n', '-xerror', '-i',
                str(folder / 'master-2160p-30fps.mkv'), '-map', '0:v:0', '-map', '0:a:0',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '192k', '-fps_mode', 'passthrough', '-movflags', '+faststart'],
                (2880, 2160), n * 2, 30, False)
            review = folder / review_name
            if review.stat().st_size < 104857600:
                deliveries = [review]
            else:
                package = folder / 'download-package'
                if not package.exists():
                    subprocess.run([sys.executable, str(Path(__file__).with_name('package_movie_download.py')),
                        str(review), str(package), '--basename', clip + '-2160p-30fps'], check=True)
                parts = json.loads((package / 'parts.json').read_text())
                if parts['sha256'] != digest_file(review):
                    raise ValueError('Package identity differs from validated review')
                deliveries = sorted(package.iterdir())
            job['delivery_files'] = [{'path': str(f), 'name': f.name, 'bytes': f.stat().st_size}
                                     for f in deliveries]
            job['review'] = manifest['checks'][-1]
            job['status'] = 'technical validation passed; download ready'
            manifest['status'] = job['status']
            save()
            print(clip + ': completed and ready for upload', flush=True)
        except Exception as error:
            job['status'] = 'failed'
            job['error'] = str(error)
            manifest['status'] = 'failed: ' + str(error)
            save()
            print(clip + ': FAILED: ' + str(error), flush=True)
    failed = [j['id'] for j in state['jobs'] if j['status'] == 'failed']
    state['status'] = 'batch finished; failures require repair' if failed else 'all 18 videos technically validated and ready'
    write_json(batch_path, state)
    print(state['status'], flush=True)
    if failed:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
