"""Full-length, hash-bound 30 fps interpolation of the validated MW3 upscale."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from validate_video_pilot import digest_file, verify_audio_grid


def check_grid(timestamps, count, rate):
    if len(timestamps) != count:
        raise ValueError(f'Expected {count} frames, found {len(timestamps)}')
    error = max(abs(float(t) - i / rate) for i, t in enumerate(sorted(map(float, timestamps))))
    if error > 0.001:
        raise ValueError('Frame timestamps depart from original duration grid')
    return error


def inspect(path, count, rate, ffprobe, ffmpeg, expected_pcm, lossless):
    # FFV1 and H.264 here each carry one video picture per packet. Later encode
    # stages decode masters with -xerror; the final preview is also fully decoded.
    data = json.loads(subprocess.run([ffprobe, '-v', 'error', '-show_packets',
        '-show_streams', '-show_format', '-of', 'json', str(path)],
        capture_output=True, text=True, check=True).stdout)
    video = [s for s in data['streams'] if s['codec_type'] == 'video']
    audio = [s for s in data['streams'] if s['codec_type'] == 'audio']
    if len(video) != 1 or len(audio) != 1:
        raise ValueError('One video and one audio stream required')
    v, a = video[0], audio[0]
    if (v['width'], v['height'], v['r_frame_rate']) != (2880, 2160, f'{rate}/1'):
        raise ValueError('Unexpected dimensions or rate')
    error = check_grid([p['pts_time'] for p in data['packets']
                        if p['stream_index'] == v['index']], count, rate)
    if abs(float(data['format']['duration']) - 4023397 / 22050) > 0.001:
        raise ValueError('Original complete duration differs')
    record = {'file': path.name, 'bytes': path.stat().st_size, 'sha256': digest_file(path),
              'frames': count, 'frame_rate': rate, 'dimensions': [2880, 2160],
              'duration_seconds': float(data['format']['duration']),
              'max_video_timestamp_error_seconds': error}
    if lossless:
        if (a['codec_name'], a['channels'], a['sample_rate']) != ('pcm_s16le', 2, '22050'):
            raise ValueError('Original PCM format differs')
        pcm = subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(path),
            '-map', '0:a:0', '-c:a', 'pcm_s16le', '-f', 's16le', 'pipe:1'],
            capture_output=True, check=True).stdout
        if len(pcm) != 4023397 * 4 or hashlib.sha256(pcm).hexdigest() != expected_pcm:
            raise ValueError('Original PCM identity or complete audio tail differs')
        frames = json.loads(subprocess.run([ffprobe, '-v', 'error', '-select_streams',
            'a:0', '-show_frames', '-of', 'json', str(path)],
            capture_output=True, text=True, check=True).stdout)['frames']
        record['max_audio_timestamp_error_seconds'] = verify_audio_grid(frames, 22050, 4023397)
        record['pcm_sha256'] = expected_pcm
        record['pcm_sample_frames'] = 4023397
    else:
        decoded = json.loads(subprocess.run([ffprobe, '-v', 'error', '-select_streams',
            'v:0', '-count_frames', '-show_streams', '-of', 'json', str(path)],
            capture_output=True, text=True, check=True).stdout)['streams'][0]
        if int(decoded['nb_read_frames']) != count:
            raise ValueError('Decoded preview frame count differs')
        record['decoded_frames'] = count
        if (a['codec_name'], a['channels'], a['sample_rate']) != ('aac', 2, '22050'):
            raise ValueError('Review audio format differs')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = args.directory.resolve()
    local = (root / 'local/work-ahead').resolve()
    if output == local or not output.is_relative_to(local) or output.exists():
        parser.error('Use a fresh directory under local/work-ahead')
    pilot = json.loads((local / 'opening-cinematic-30fps-v1/manifest.json').read_text())
    tools = pilot['tools_and_weights']
    for item in tools:
        if digest_file(Path(item['path'])) != item['sha256']:
            raise ValueError('Tool or RIFE model differs from pilot')
    ffmpeg = next(t['path'] for t in tools if Path(t['path']).name.lower() == 'ffmpeg.exe')
    ffprobe = next(t['path'] for t in tools if Path(t['path']).name.lower() == 'ffprobe.exe')
    video2x = next(t['path'] for t in tools if Path(t['path']).name.lower() == 'video2x.exe')
    source = local / 'opening-cinematic-v1/opening-2160p-master.mkv'
    source_report = json.loads((local / 'opening-cinematic-v1/processing.json').read_text())
    source_record = next(c for c in source_report['checks'] if c['file'] == source.name)
    if digest_file(source) != source_record['sha256']:
        raise ValueError('Validated upscale identity differs')
    output.mkdir()
    state = {'status': 'source verified', 'source': source_record,
             'tools_and_weights': tools, 'interpolation': pilot['interpolation'],
             'workflow_sha256': digest_file(Path(__file__)), 'commands': [], 'checks': [],
             'end_policy': 'One held final frame fills last 1/30 second; preserve seven-sample audio tail.'}

    def save():
        (output / 'manifest.json').write_text(json.dumps(state, indent=2) + '\n')

    def stage(name, executable, args, frames, lossless):
        state['status'] = 'processing ' + name
        save()
        command = [executable, *args, str(output / name)]
        print('Starting ' + name, flush=True)
        start = time.monotonic()
        with (output / (name + '.log')).open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        state['commands'].append({'argv': command, 'seconds': time.monotonic() - start,
                                  'exit_code': result.returncode})
        state['status'] = 'validating ' + name if result.returncode == 0 else 'failed ' + name
        save()
        if result.returncode:
            raise RuntimeError('Processing failed; inspect stage log')
        print('Validating ' + name, flush=True)
        state['checks'].append(inspect(output / name, frames, 30, ffprobe, ffmpeg,
                                       source_record['pcm_sha256'], lossless))
        save()

    stage('rife-30fps-raw.mkv', video2x, ['-i', str(source), '-p', 'rife', '--rife-model',
        'rife-v4.6', '--rife-uhd', '-m', '2', '-t', '20', '-d', '0', '-c', 'ffv1',
        '--pix-fmt', 'yuv444p', '--no-progress', '-o'], 5473, True)
    stage('opening-2160p-30fps-master.mkv', ffmpeg, ['-hide_banner', '-nostdin', '-n',
        '-xerror', '-i', str(output / 'rife-30fps-raw.mkv'), '-map', '0:v:0', '-map', '0:a:0',
        '-vf', 'tpad=stop_mode=clone:stop_duration=0.033333334,trim=end_frame=5474,setpts=N/(30*TB)',
        '-c:v', 'ffv1', '-level', '3', '-c:a', 'copy', '-fps_mode', 'passthrough'], 5474, True)
    stage('opening-2160p-30fps-review.mp4', ffmpeg, ['-hide_banner', '-nostdin', '-n',
        '-xerror', '-i', str(output / 'opening-2160p-30fps-master.mkv'), '-map', '0:v:0',
        '-map', '0:a:0', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt',
        'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-fps_mode', 'passthrough',
        '-movflags', '+faststart'], 5474, False)
    state['status'] = 'technical validation passed; full-speed whole-movie review pending'
    save()
    print(state['status'], flush=True)


if __name__ == '__main__':
    main()
