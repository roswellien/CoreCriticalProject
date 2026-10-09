"""Measure replay differences without claiming frame equivalence."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageChops


def compare(reference, candidate, difference, rgb565=False, resize_filter=None, initial_reference=None):
    original = Image.open(reference).convert('RGB')
    replay = Image.open(candidate).convert('RGB')
    source_size = replay.size
    if resize_filter:
        filters = {'nearest': Image.Resampling.NEAREST, 'box': Image.Resampling.BOX,
                   'bilinear': Image.Resampling.BILINEAR}
        replay = replay.resize(original.size, filters[resize_filter])
    if rgb565:
        data = bytearray(replay.tobytes())
        levels = (31, 63, 31)
        for i, value in enumerate(data):
            maximum = levels[i % 3]
            data[i] = round(round(value * maximum / 255) * 255 / maximum)
        replay = Image.frombytes('RGB', replay.size, bytes(data))
    if original.size != replay.size:
        raise ValueError('Image dimensions differ')
    errors = ImageChops.difference(original, replay)
    errors.save(difference)
    channel_bytes = errors.tobytes()
    pixels = zip(channel_bytes[0::3], channel_bytes[1::3], channel_bytes[2::3])
    maxima = [max(pixel) for pixel in pixels]
    histogram = errors.histogram()
    width, height = original.size
    outliers = [i for i, value in enumerate(maxima) if value > 8]
    bounds = None
    if outliers:
        bounds = [min(i % width for i in outliers), min(i // width for i in outliers),
                  max(i % width for i in outliers), max(i // width for i in outliers)]
    mask = Image.frombytes('L', original.size, bytes(255 if value > 8 else 0 for value in maxima))
    mask_path = difference.with_name(difference.stem + '-outliers.png')
    mask.save(mask_path)
    report = {
        'scope': 'image difference measurement; command closure and frame equivalence unproven',
        'dimensions': list(original.size),
        'candidate_postprocess': 'nearest RGB565 quantization' if rgb565 else 'none',
        'candidate_source_dimensions': list(source_size),
        'candidate_resize_filter': resize_filter,
        'pixels': len(maxima),
        'exact_pixels': sum(value == 0 for value in maxima),
        'pixels_within_8_per_channel': sum(value <= 8 for value in maxima),
        'mean_absolute_channel_error': sum((index % 256) * count for index, count in enumerate(histogram)) / (len(maxima) * 3),
        'maximum_channel_error': max(maxima),
        'pixels_exceeding_8_per_channel': len(outliers),
        'outlier_bounds_inclusive': bounds,
        'outlier_mask': str(mask_path),
        'difference_image': str(difference),
    }
    if initial_reference:
        initial = Image.open(initial_reference).convert('RGB')
        if initial.size != original.size:
            raise ValueError('Initial target dimensions differ')
        prior, final, output = initial.tobytes(), original.tobytes(), replay.tobytes()
        changed = [i for i in range(len(maxima)) if final[i*3:i*3+3] != prior[i*3:i*3+3]]
        union = [i for i in range(len(maxima)) if final[i*3:i*3+3] != prior[i*3:i*3+3] or output[i*3:i*3+3] != prior[i*3:i*3+3]]
        report['reference_changed_pixels'] = len(changed)
        report['changed_region_union'] = {'pixels': len(union),
            'scope': 'Union of reference and candidate changes relative to initial target; unchanged retained pixels excluded',
            'exact_pixels': sum(maxima[i] == 0 for i in union),
            'pixels_within_8_per_channel': sum(maxima[i] <= 8 for i in union),
            'mean_absolute_channel_error': sum(sum(channel_bytes[i*3:i*3+3]) for i in union) / (3*len(union)) if union else None}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('difference', type=Path)
    parser.add_argument('--rgb565', action='store_true', help='Experiment: quantize candidate once after rendering; does not model per-draw quantization or dithering')
    parser.add_argument('--resize-filter', choices=('nearest','box','bilinear'),
                        help='Explicit experiment: resize candidate to reference dimensions before comparison')
    parser.add_argument('--initial-reference', type=Path, help='Report errors in pixels changed from the initial target')
    args = parser.parse_args()
    print(json.dumps(compare(args.reference, args.candidate, args.difference, args.rgb565, args.resize_filter, args.initial_reference), indent=2))
