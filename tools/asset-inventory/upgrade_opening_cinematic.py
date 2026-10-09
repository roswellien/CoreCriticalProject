"""Resume the hash-bound MW3 opening cinematic workflow in ignored local storage."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

from validate_video_pilot import digest_file, verify_grid, verify_audio_grid
from video_probe import avi_metadata

SOURCE_HASH = '8a4276231b81a2edc064f3c88af1ee5aa780e080e2e00a9f5c43711ec62891e4'
FRAMES = 2737
SAMPLES = 4023397


def check_source(path):
    if path.stat().st_size != 82169804 or digest_file(path) != SOURCE_HASH:
        raise ValueError('Opening movie source identity mismatch')
    payload = path.read_bytes()
    info = avi_metadata(payload, 0, len(payload))
    video, audio = info['streams']
    fmt = dict(audio['audio_format'])
    fmt.pop('extra_format_bytes', None)
    if (video['type'] != 'vids' or video['handler'] != 'IV50'
            or video['length'] != FRAMES or video['rate'] != 15
            or video['scale'] != 1 or video['start'] != 0
            or audio['type'] != 'auds' or audio['start'] != 0
            or audio['length'] != SAMPLES or fmt != {
                'format_tag': 1, 'channels': 2, 'sample_rate': 22050,
                'byte_rate': 88200, 'block_align': 4, 'bits_per_sample': 16}):
        raise ValueError('Opening movie stream contract mismatch')


def pcm(path, ffmpeg):
    result = subprocess.run([ffmpeg, '-v', 'error', '-i', str(path), '-map', '0:a:0',
                             '-c:a', 'pcm_s16le', '-f', 's16le', 'pipe:1'],
                            capture_output=True, check=True).stdout
    if len(result) != SAMPLES * 4:
        raise ValueError(f'Unexpected PCM length: {len(result)}')
    return hashlib.sha256(result).hexdigest()


def inspect(path, size, ffprobe, ffmpeg, expected_pcm, lossless=True):
    probe = json.loads(subprocess.run([
        ffprobe, '-v', 'error', '-show_frames', '-show_streams', '-show_format',
        '-of', 'json', str(path)], capture_output=True, text=True, check=True).stdout)
    videos = [s for s in probe['streams'] if s['codec_type'] == 'video']
    audios = [s for s in probe['streams'] if s['codec_type'] == 'audio']
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError('One video and audio stream required')
    video, audio = videos[0], audios[0]
    if (video['width'], video['height']) != size or video['r_frame_rate'] != '15/1':
        raise ValueError('Unexpected dimensions or frame rate')
    vf = [f for f in probe['frames'] if f['media_type'] == 'video']
    error = verify_grid([f['best_effort_timestamp_time'] for f in vf], FRAMES)
    duration = float(probe['format']['duration'])
    if abs(duration - SAMPLES / 22050) > (0.001 if lossless else 0.1):
        raise ValueError('Unexpected complete movie duration')
    record = {'file': path.name, 'bytes': path.stat().st_size,
              'sha256': digest_file(path), 'dimensions': list(size),
              'frames': len(vf), 'frame_rate': '15/1', 'duration_seconds': duration,
              'max_video_timestamp_error_seconds': error}
    if lossless:
        if audio['codec_name'] != 'pcm_s16le' or audio['channels'] != 2 or audio['sample_rate'] != '22050':
            raise ValueError('Original stereo PCM format required')
        record['max_audio_timestamp_error_seconds'] = verify_audio_grid(
            [f for f in probe['frames'] if f['media_type'] == 'audio'], 22050, SAMPLES)
        record['pcm_sha256'] = pcm(path, ffmpeg)
        if record['pcm_sha256'] != expected_pcm:
            raise ValueError('Master PCM differs from source')
        record['pcm_sample_frames'] = SAMPLES
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    directory = args.directory.resolve()
    if not directory.is_relative_to((root / 'local/work-ahead').resolve()):
        parser.error('Outputs must remain under local/work-ahead')
    if directory.is_symlink() or directory.is_junction():
        parser.error('Output directory cannot be a link')
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    pilot = json.loads((root / 'local/work-ahead/video-pilot-v2/manifest.json').read_text())
    video2x = next(t['path'] for t in pilot['tools'] if t['name'] == 'video2x')
    for tool in pilot['tools']:
        if digest_file(Path(tool['path'])) != tool['sha256']:
            raise ValueError('Installed tool differs from verified pilot')
    for model in pilot['models']:
        if 'realesrgan-plus-x4' in model['file'] and digest_file(Path(model['path'])) != model['sha256']:
            raise ValueError('Selected model differs from verified pilot')
    if not ffmpeg or not ffprobe:
        parser.error('Installed FFmpeg and FFprobe required')
    source = directory / 'source.avi'
    check_source(source)
    expected_pcm = pcm(source, ffmpeg)
    state_path = directory / 'processing.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {
        'source_pcm_sha256': expected_pcm, 'commands': [], 'checks': [],
        'tools': pilot['tools'], 'models': [m for m in pilot['models'] if 'realesrgan-plus-x4' in m['file']],
        'workflow_sha256': digest_file(Path(__file__))}

    def save():
        state_path.write_text(json.dumps(state, indent=2) + '\n')

    def stage(name, executable, argv, size, lossless=True):
        output = directory / name
        if not output.exists():
            state['status'] = 'processing ' + name
            save()
            command = [str(executable), *argv, str(output)]
            print('Starting ' + name, flush=True)
            started = time.monotonic()
            with (directory / (name + '.log')).open('w') as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            state['commands'].append({'argv': command, 'seconds': time.monotonic() - started,
                                      'exit_code': result.returncode})
            save()
            if result.returncode:
                raise RuntimeError('Processing failed; see ' + name + '.log')
        print('Validating ' + name, flush=True)
        record = inspect(output, size, ffprobe, ffmpeg, expected_pcm, lossless)
        state['checks'] = [r for r in state['checks'] if r['file'] != name] + [record]
        save()

    stage('reference.mkv', ffmpeg, ['-hide_banner', '-nostdin', '-n', '-xerror', '-i', str(source),
          '-vf', 'fps=15,trim=end_frame=2737,setpts=N/(15*TB)', '-map', '0:v:0', '-map', '0:a:0',
          '-c:v', 'ffv1', '-level', '3', '-c:a', 'copy', '-fps_mode', 'passthrough'], (640, 480))
    reference = str(directory / 'reference.mkv')
    stage('ai-general4x-intermediate.mkv', video2x, ['-i', reference, '-p', 'realesrgan', '-s', '4',
          '--realesrgan-model', 'realesrgan-plus', '-d', '0', '-c', 'ffv1', '--pix-fmt', 'yuv444p',
          '--no-progress', '-o'], (2560, 1920))
    stage('opening-2160p-master.mkv', ffmpeg, ['-hide_banner', '-nostdin', '-n', '-i',
          str(directory / 'ai-general4x-intermediate.mkv'), '-map', '0:v:0', '-map', '0:a:0',
          '-vf', 'scale=2880:2160:flags=lanczos,setsar=1', '-c:v', 'ffv1', '-level', '3',
          '-c:a', 'copy', '-fps_mode', 'passthrough'], (2880, 2160))
    for name, input_path, scale in [('opening-2160p-review.mp4', str(directory / 'opening-2160p-master.mkv'), []),
                                    ('original-review.mp4', reference, [])]:
        stage(name, ffmpeg, ['-hide_banner', '-nostdin', '-n', '-i', input_path, '-map', '0:v:0',
              '-map', '0:a:0', *scale, '-c:v', 'libx264', '-preset', 'slow', '-crf', '16',
              '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
              '-fps_mode', 'passthrough'], (2880, 2160) if name.startswith('opening') else (640, 480), False)
    state['status'] = 'technical validation passed; full-speed perceptual review pending'
    save()
    manifest_path = directory / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['status'] = state['status']
    manifest['processing_report'] = 'processing.json'
    manifest['outputs'] = state['checks']
    manifest['next'] = ['Full-speed motion, lettering, transition and audio synchronization review',
                        'Playback integration after review']
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(state['status'], flush=True)


if __name__ == '__main__':
    main()
