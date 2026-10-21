"""Apply one reviewed water colour grade to the existing C1 surf animation.

The generated reference supplies colour statistics only. Original animation,
foam, sand, dimensions, entry headers and every unrelated bank byte are retained.
Prepared game assets remain local. Always select a fresh output directory.
"""

from pathlib import Path
import argparse
import hashlib
import json
import shutil
import struct

from prepare_surface_normals import bank_entries


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def prepare(banks, master, master_hash, reference, reference_hash, bank_map, output):
    import numpy as np
    from PIL import Image

    if sha(master) != master_hash or sha(reference) != reference_hash:
        raise ValueError("Reviewed colour reference changed")
    output = Path(output)
    if output.exists():
        raise ValueError("Choose a fresh shoreline candidate directory")

    def water_mean(path):
        image = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)
        h, w = image.shape[:2]
        return image[int(h * 0.05) : int(h * 0.95), int(w * 0.85) :].mean(axis=(0, 1))

    gain = water_mean(reference) / water_mean(master)
    if not np.isfinite(gain).all() or (gain < 0.35).any() or (gain > 1.25).any():
        raise ValueError("Unreviewed or excessive shoreline colour grade")
    selected = [b for b in json.loads(Path(banks).read_text()) if b["bank"].startswith("c1-")]
    if len(selected) != 6 or not all(b["installed_AI"] for b in selected):
        raise ValueError("Expected all six upgraded C1 banks")
    wanted = {f"wave{i:02}" for i in range(1, 14)}
    output.mkdir(parents=True)
    receipt = dict(
        method="One generated-reference palette grade; original animation pixels retained",
        master_sha256=master_hash,
        reference_sha256=reference_hash,
        channel_gain=gain.tolist(),
        banks=[],
        normal_maps_added=False,
    )
    redirects = {}
    for bank in selected:
        source = Path(bank["source"])
        if sha(source) != bank["expected_sha256"]:
            raise ValueError("Upgraded source bank changed: " + str(source))
        table = bank_entries(source)
        if not wanted <= table.keys():
            raise ValueError("Incomplete 13-frame surf sequence")
        target = output / (bank["bank"] + "-shore.zbd")
        shutil.copyfile(source, target)
        changed = []
        preserved = 0
        with source.open("rb") as old, target.open("r+b") as new:
            for name, (offset, span) in table.items():
                old.seek(offset)
                data = old.read(span)
                if name in wanted:
                    flags, w, h, zero, palette, stretch = struct.unpack_from("<IHHIHH", data)
                    if flags not in (3, 5, 0x23, 0x25) or zero or palette or span != 16 + w * h * 2:
                        raise ValueError("Unsupported surf pixel or alpha layout")
                    words = np.frombuffer(data[16:], dtype="<u2").reshape(h, w)
                    rgb = np.stack(
                        (
                            (words >> 11) * 255 // 31,
                            ((words >> 5) & 63) * 255 // 63,
                            (words & 31) * 255 // 31,
                        ),
                        axis=-1,
                    ).astype(np.float64)
                    # Blue/green water only: neutral foam and warm sand stay exact.
                    chroma = rgb[..., 1] - rgb[..., 0]
                    mask = np.clip((chroma - 3) / 12, 0, 1)
                    mask *= np.clip((np.arange(w) / w - 0.60) / 0.12, 0, 1)[None, :]
                    mask[np.min(rgb, axis=-1) > 140] = 0
                    graded = np.clip(rgb * (1 + mask[..., None] * (gain - 1)), 0, 255)
                    result = np.rint(graded[..., 0] * 31 / 255).astype("<u2") << 11
                    result |= np.rint(graded[..., 1] * 63 / 255).astype("<u2") << 5
                    result |= np.rint(graded[..., 2] * 31 / 255).astype("<u2")
                    if not np.array_equal(result[mask == 0], words[mask == 0]):
                        raise ValueError("Grade altered protected sand/foam pixels")
                    if not np.array_equal(result == 0, words == 0):
                        raise ValueError("Grade altered legacy black colour-key pixels")
                    payload = data[:16] + result.astype("<u2").tobytes()
                    new.seek(offset)
                    new.write(payload)
                    changed.append(
                        dict(
                            name=name,
                            width=w,
                            height=h,
                            input_sha256=hashlib.sha256(data).hexdigest(),
                            output_sha256=hashlib.sha256(payload).hexdigest(),
                            changed_pixels=int(np.count_nonzero(result != words)),
                        )
                    )
                else:
                    new.seek(offset)
                    if new.read(span) != data:
                        raise ValueError("Unrelated bank entry changed: " + name)
                    preserved += 1
        if sha(source) != bank["expected_sha256"] or target.stat().st_size != source.stat().st_size:
            raise ValueError("Source changed or output size differs")
        with target.open("rb") as new, source.open("rb") as old:
            if new.read(24 + len(table) * 40) != old.read(24 + len(table) * 40):
                raise ValueError("Bank table changed")
        receipt["banks"].append(
            dict(
                source=str(source),
                source_sha256=bank["expected_sha256"],
                output=str(target),
                output_sha256=sha(target),
                changed=changed,
                unchanged_entries=preserved,
            )
        )
        suffix = bank["bank"][3:]
        redirects["zbd/c1/" + suffix + ".zbd"] = str(target.resolve())
    data = Path(bank_map).read_bytes()
    if data[:8] != b"MWBANK1\0":
        raise ValueError("Invalid source bank map")
    count = struct.unpack_from("<I", data, 8)[0]
    at = 12
    result = bytearray(data[:12])
    replaced = set()
    for _ in range(count):
        a, b = struct.unpack_from("<II", data, at)
        at += 8
        key, path = data[at : at + a], data[at + a : at + a + b]
        at += a + b
        decoded = key.decode()
        if decoded in redirects:
            path = redirects[decoded].encode()
            replaced.add(decoded)
        result.extend(struct.pack("<II", len(key), len(path)))
        result.extend(key)
        result.extend(path)
    if at != len(data) or replaced != redirects.keys():
        raise ValueError("Expected exactly six C1 redirects")
    (output / "texture-banks.bin").write_bytes(result)
    receipt["bank_map_sha256"] = sha(output / "texture-banks.bin")
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ["banks", "master", "reference", "bank-map", "output"]:
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--master-hash", required=True)
    p.add_argument("--reference-hash", required=True)
    a = p.parse_args()
    result = prepare(
        a.banks, a.master, a.master_hash, a.reference, a.reference_hash, a.bank_map, a.output
    )
    print("Prepared six C1 banks; 78 animated surf entries graded; all unrelated entries retained")
