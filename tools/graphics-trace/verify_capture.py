"""Verify exact payloads and selected scene data; not a proof of frame equivalence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


def verify(directory, allow_authored=False):
    rows = [json.loads(line) for line in (directory / "capture.jsonl").read_text().splitlines()]
    if rows and (rows[0].get('scope') != 'one_BeginScene_EndScene_interval' or rows[0].get('command_coverage_complete') is False):
        raise ValueError('Presentation interval is diagnostic only; full command coverage/replay is not recovered')
    return _verify_payload(directory, rows, allow_authored)


def verify_presentation_diagnostic(directory):
    """Validate observed payload/order without granting scene acceptance."""
    rows = [json.loads(line) for line in (directory / 'capture.jsonl').read_text().splitlines()]
    if not rows or rows[0].get('scope') != 'bounded_primary_flip_interval' or rows[0].get('command_coverage_complete') is not False:
        raise ValueError('Expected explicitly incomplete presentation diagnostic')
    if rows[-1].get('command_coverage_complete') is not False:
        raise ValueError('Diagnostic footer overstates command coverage')
    opened = False
    scenes = draws = 0
    allowed = {'begin', 'initial_target', 'initial_depth', 'scene_begin', 'draw', 'scene_end', 'final_target', 'end', 'depth_fill', 'cpu_write'}
    for row in rows:
        event = row['event']
        if event not in allowed:
            raise ValueError('Unsupported diagnostic event')
        if event == 'scene_begin':
            if opened: raise ValueError('Nested diagnostic scene')
            opened = True
            scenes += 1
        elif event == 'scene_end':
            if not opened or row['draws_so_far'] != draws: raise ValueError('Diagnostic scene accounting')
            opened = False
        elif event == 'draw':
            if not opened: raise ValueError('Draw outside diagnostic scene')
            draws += 1
        elif event in ('depth_fill', 'cpu_write') and row['draws_so_far'] != draws:
            raise ValueError('Surface command draw-order mismatch')
        elif event in ('final_target', 'end') and opened:
            raise ValueError('Open scene at final boundary')
    if opened or not scenes:
        raise ValueError('Missing diagnostic scene closure')
    receipt = _verify_payload(directory, rows, False)
    receipt.update(scope='Observed presentation payloads only; no complete command coverage or frame equivalence',
                   scene_intervals=scenes, diagnostic_only=True, command_coverage_complete=False)
    return receipt


def depth_fill_command(row, width, height, effects):
    """Only the observed null-source D16 zero-depth profile is supported."""
    if (row['flags'], row['fill_depth'], row['bits'], row['depth_bits']) != (0x2000000, 0, 16, 0) or row['hresult'] < 0:
        raise ValueError('Depth fill outside observed profile')
    if len(effects) != 100 or struct.unpack_from('<I', effects)[0] != 100 or struct.unpack_from('<I', effects, 80)[0] != 0:
        raise ValueError('Depth fill input disagreement')
    rect = row['rectangle']
    if len(rect) != 4 or any(type(value) is not int for value in rect):
        raise ValueError('Depth rectangle shape')
    left, top, right, bottom = rect
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError('Depth rectangle bounds')
    return (2, 2, left, top, right-left, bottom-top, 0, 0, 0, 0)


def cpu_write_regions(row, width, height, before, after):
    """Copy only pixels changed by the observed CPU interval, preserving others."""
    if row['format'] != 'RGB565' or row['unlock_hresult'] < 0 or (row['width'], row['height']) != (width, height) or row['source_pitch'] < width*2:
        raise ValueError('CPU write outside observed profile')
    if len(before) != width*height*2 or len(after) != len(before):
        raise ValueError('CPU pixel payload size mismatch')
    regions = []
    for y in range(height):
        x = 0
        while x < width:
            position = (y*width+x)*2
            if before[position:position+2] == after[position:position+2]:
                x += 1
                continue
            start = x
            x += 1
            while x < width:
                position = (y*width+x)*2
                if before[position:position+2] == after[position:position+2]:
                    break
                x += 1
            regions.append((start, y, x-start, 1))
    if len(regions) > 4096:
        raise ValueError('CPU write copy-command budget')
    return regions


def _verify_payload(directory, rows, allow_authored):
    if not rows or rows[0]["event"] != "begin" or rows[-1]["event"] != "end" or rows[-1]["complete"] is not True:
        raise ValueError("Capture did not complete; partial/aborted data cannot pass")
    if not allow_authored and rows[0]["live"] is not True:
        raise ValueError("Authored fixture cannot satisfy a live capture gate")
    if "requested_skip" in rows[0] and (rows[0]["requested_skip"] != rows[0].get("skipped_scenes") or not 0 <= rows[0]["requested_skip"] <= 36000):
        raise ValueError("Delayed capture scene accounting mismatch")
    references = set()

    def payload(filename, size):
        if not re.fullmatch(r"[0-9a-f]{64}\.bin", filename):
            raise ValueError("Invalid content-addressed payload filename")
        data = (directory / filename).read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != filename[:-4]:
            raise ValueError("Payload size/hash mismatch")
        references.add(filename)
        return data

    def surface(info):
        if info["bits"] not in (8, 16, 24, 32) or not (0 < info["width"] <= 4096 and 0 < info["height"] <= 4096):
            raise ValueError("Unsupported surface layout")
        expected = info["width"] * (info["bits"] // 8)
        if info["row_bytes"] != expected or abs(info["source_pitch"]) < expected:
            raise ValueError("Invalid surface row/pitch metadata")
        payload(info["file"], expected * info["height"])
        if info["fourcc"] and info["flags"] & 4:
            raise ValueError("Compressed/FOURCC layout is not recovered")
        if info["flags"] & 0x20:
            raise ValueError("Palette contents are not captured yet")

    initial = [row for row in rows if row["event"] == "initial_target"]
    final = [row for row in rows if row["event"] == "final_target"]
    depth = [row for row in rows if row["event"] == "initial_depth"]
    if len(initial) != 1 or len(final) != 1 or len(depth) != 1:
        raise ValueError("Missing or duplicate target/depth boundary")
    surface(initial[0]["surface"]); surface(final[0]["surface"])
    if not depth[0].get("absent"):
        surface(depth[0]["surface"])
    draws = [row for row in rows if row["event"] == "draw"]
    if not draws or len(draws) != rows[-1]["draws"] or len(draws) > 2048:
        raise ValueError("Missing/inconsistent bounded draw sequence")
    if len(draws) < rows[0].get("minimum_draws", 0):
        raise ValueError("Interval did not meet the requested scene selection minimum")
    texture_snapshots = 0
    fills = [row for row in rows if row['event'] == 'depth_fill']
    for row in fills:
        if depth[0].get('absent') or (depth[0]['surface']['bits'], depth[0]['surface']['flags'], depth[0]['surface']['g_mask']) != (16, 1024, 65535):
            raise ValueError('Depth fill lacks observed D16 backing')
        if not depth[0].get('object') or row['destination'] != depth[0]['object']:
            raise ValueError('Depth fill attachment identity mismatch')
        if (depth[0]['surface']['width'], depth[0]['surface']['height']) != (initial[0]['surface']['width'], initial[0]['surface']['height']):
            raise ValueError('Depth fill backing size mismatch')
        depth_fill_command(row, initial[0]['surface']['width'], initial[0]['surface']['height'], payload(row['effects'], 100))
    writes = [row for row in rows if row['event'] == 'cpu_write']
    for ordinal, row in enumerate(writes, 1):
        target_info = initial[0]['surface']
        if tuple(target_info[key] for key in ('flags', 'bits', 'r_mask', 'g_mask', 'b_mask', 'a_mask')) != (64, 16, 0xf800, 0x7e0, 0x1f, 0):
            raise ValueError('CPU write requires observed RGB565 target')
        if row['ordinal'] != ordinal or not initial[0].get('object') or row['surface'] != initial[0]['object']:
            raise ValueError('CPU write target identity/ordinal mismatch')
        size = row['width']*row['height']*2
        cpu_write_regions(row, initial[0]['surface']['width'], initial[0]['surface']['height'], payload(row['before'], size), payload(row['after'], size))
    for ordinal, draw in enumerate(draws, 1):
        if draw["ordinal"] != ordinal:
            raise ValueError("Dropped or reordered draw")
        fvf = draw["fvf"]
        position, textures = fvf & 14, (fvf >> 8) & 15
        if position not in (2, 4) or textures > 8 or fvf & ~0xFDE:
            raise ValueError("Unrecovered vertex format")
        stride = (16 if position == 4 else 12) + (12 if fvf & 16 else 0) + (4 if fvf & 64 else 0) + (4 if fvf & 128 else 0) + textures * 8
        if stride != draw["stride"]:
            raise ValueError("Vertex stride mismatch")
        payload(draw["vertices"], draw["vertex_count"] * stride)
        if draw["index_count"]:
            indices = payload(draw["indices"], draw["index_count"] * 2)
            if any(index >= draw["vertex_count"] for (index,) in struct.iter_unpack("<H", indices)):
                raise ValueError("Index out of vertex range")
        elif draw["indices"] is not None:
            raise ValueError("Unexpected index payload")
        if depth[0].get("absent") and draw["render_states"]["7"]:
            raise ValueError("Depth is enabled but initial depth was not captured")
        if [stage["stage"] for stage in draw["stages"]] != list(range(8)):
            raise ValueError("Missing texture stages")
        for stage in draw["stages"]:
            if stage["texture"]:
                surface(stage["texture"]); texture_snapshots += 1
                if stage["texture"]["caps"] & 0x400000 and stage["states"]["18"]:
                    raise ValueError("Mip filtering enabled but mip chain not captured")
    actual = {path.name for path in directory.glob("*.bin")}
    if actual != references or len(actual) != rows[-1]["resource_files"]:
        raise ValueError("Missing/unreferenced resource payload")
    total = sum((directory / filename).stat().st_size for filename in references)
    if total != rows[-1]["stored_bytes"] or total > 64 * 1024 * 1024:
        raise ValueError("Storage budget/accounting mismatch")
    return {"live": rows[0]["live"], "pid": rows[0]["pid"], "draws": len(draws),
            "skipped_scenes": rows[0].get("skipped_scenes", 0),
            "texture_snapshots": texture_snapshots, "depth_fills": len(fills), "cpu_writes": len(writes), "payload_files": len(actual), "stored_bytes": total,
            "target_size": [initial[0]["surface"]["width"], initial[0]["surface"]["height"]],
            "manifest_sha256": hashlib.sha256((directory / "capture.jsonl").read_bytes()).hexdigest(),
            "scope": "Selected draw/state/resource snapshots; command closure, clear/presentation coverage and Vulkan equivalence unproven"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-authored", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.directory, args.allow_authored), indent=2))


if __name__ == "__main__":
    main()
