"""Stage registered texture/model sidecars without changing the game installation.

The caller supplies reviewed local registrations; this module neither discovers
nor downloads replacement content. ``prepare`` returns environment bindings for
the native host and records generated-file identities in its output directory.
Binary fields below use explicit little-endian layouts shared with the renderer.
"""

from pathlib import Path
import array, hashlib, json, os, struct, sys
from normal_materials import load_images, normal_environment, pack_normals, pixel_hash

try:
    from PIL import Image
except ImportError as exc:
    raise RuntimeError(
        "Pillow could not be loaded by "
        + sys.executable
        + f": {exc}. Launch through Play MW3Remaster.cmd to select a runtime with Pillow."
    ) from exc


def write_atomic(path, data):
    """Replace one output via a sibling temporary file, not an in-place write.

    Callers must own the output directory and serialize writers to the same
    filename; the fixed temporary name is not a cross-process locking mechanism.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def material_pixels(root, textures):
    """Encode ordered albedo materials as RGB565 records for BWTEX1 sidecars.

    Each record has a 32-byte padded name, width/height, a 64-bit identity from
    SHA-256 and little-endian pixel words. Images are capped at 2048 pixels per
    axis and flipped vertically to match the native texture-coordinate contract.
    Material insertion order must agree with the batch-to-material indices.
    """
    out = bytearray()
    for name, relative in textures.items():
        source = root / relative
        im = Image.open(source).convert("RGB")
        im.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
        im = im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        pixels = array.array(
            "H", (((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3) for r, g, b in im.getdata())
        )
        if sys.byteorder != "little":
            pixels.byteswap()
        data = pixels.tobytes()
        digest = hashlib.sha256(data).digest()
        out.extend(name.encode().ljust(32, b"\0"))
        out.extend(struct.pack("<IIQ", *im.size, int.from_bytes(digest[:8], "little")))
        out.extend(data)
    return out


def normal_source_identity(root, sources):
    """Hash each normal source, retaining None as an explicit disabled binding.

    The before/after stat check rejects files observed changing during hashing.
    Normal pixels are decoded separately; the caller checks their identities
    again after decoding before publishing a newly prepared sidecar.
    """
    identity = {}
    for name, relative in sources.items():
        if relative is None:
            identity[name] = None
            continue
        path = root / relative
        before = path.stat()
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError("Normal source changed during preparation")
        identity[name] = digest
    return identity


def prepare(root, models, *, output=None):
    """Write bank, texture and normal sidecars; return MW34_* path bindings.

    ``models`` contains already selected registry entries. Existing hash caches
    speed repeated preparation, but normal sidecar reuse also verifies its full
    stored SHA-256. This function writes several files and is not a transaction
    across the whole directory; callers must wait for success before launching.
    Source game files are opened for reading only.
    """
    folder = Path(output) if output is not None else root / "local/remaster/prepared"
    folder.mkdir(parents=True, exist_ok=True)
    manifest = root / "local/work-ahead/texture-launcher-audit-v2/configured-banks.json"
    rows = json.loads(manifest.read_text(encoding="utf-8-sig"))
    local_cache = folder / "bank-hashes.json"
    shared = root / "local/work-ahead/mw3-d7vk-wrapper/launcher-hash-cache.json"
    cache = (
        json.loads((local_cache if local_cache.exists() else shared).read_text())
        if local_cache.exists() or shared.exists()
        else {}
    )
    # MWBANK1: magic[8], count:u32, then (key bytes, absolute source path bytes),
    # each preceded by its u32 length. No texture pixels are embedded in this index.
    banks = bytearray(b"MWBANK1\0" + struct.pack("<I", len(rows)))
    receipt = []
    base = root / "local/work-ahead/training-terrain-game-test/install"
    for row in rows:
        relative = Path(row["target"]).relative_to(base).as_posix().lower()
        if not relative.startswith("zbd/") or ".." in relative.split("/"):
            raise RuntimeError("Invalid published bank target " + relative)
        source = Path(row["source"])
        source_stat = source.stat()
        source_key = str(source.resolve()).lower()
        cached_bank = cache.get(source_key, {})
        if (
            cached_bank.get("size") == source_stat.st_size
            and cached_bank.get("mtime_ns") == source_stat.st_mtime_ns
        ):
            digest = cached_bank["sha256"]
        else:
            print("Verifying texture bank " + relative, flush=True)
            with source.open("rb") as f:
                digest = hashlib.file_digest(f, "sha256").hexdigest()
            after = source.stat()
            if (source_stat.st_size, source_stat.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError("Texture bank changed during verification")
            cache[source_key] = dict(
                size=source_stat.st_size, mtime_ns=source_stat.st_mtime_ns, sha256=digest
            )
        if digest.lower() != row["expected_sha256"].lower():
            raise RuntimeError("Published texture bank hash mismatch: " + relative)
        target_bytes = relative.encode()
        source_path_bytes = str(source.resolve()).encode()
        banks.extend(struct.pack("<II", len(target_bytes), len(source_path_bytes)))
        banks.extend(target_bytes)
        banks.extend(source_path_bytes)
        receipt.append(dict(bank=relative, source=str(source), sha256=digest))
    write_atomic(local_cache, json.dumps(cache, indent=1).encode())
    bankfile = folder / "texture-banks.bin"
    write_atomic(bankfile, banks)
    environment = {"MW34_REMASTER_BANKS": str(bankfile)}
    normal_cache_path = folder / "normal-cache.json"
    normal_cache = json.loads(normal_cache_path.read_text()) if normal_cache_path.exists() else {}
    model_receipts = []
    for model in models:
        # An adapter can only be published once its executable implements these bindings.
        for key, value in model.get("environment", {}).items():
            if not key.startswith("MW34_"):
                raise RuntimeError("Invalid model environment binding")
            path = root / value
            if not path.is_file():
                raise RuntimeError("Model payload missing: " + str(path))
            environment[key] = str(path)
        if not model.get("textures"):
            continue
        metadata = json.loads((root / model["batch_metadata"]).read_text())
        names = list(model["textures"])
        count = len(metadata["batches"])
        if "normal_textures" in model:
            if set(model["normal_textures"]) != set(names):
                raise RuntimeError("Normal materials differ from albedo materials: " + model["id"])
            source_identity = normal_source_identity(root, model["normal_textures"])
            images = None
            bindings = [
                dict(
                    id="close",
                    texture_environment=model["texture_environment"],
                    batch_metadata=model["batch_metadata"],
                )
            ] + model.get("texture_variants", [])
            # Alternate skins share topology/material names and the same surface
            # detail; each original LOD receives its own exact batch order.
            for binding in bindings:
                if not binding["id"] or any(
                    c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in binding["id"]
                ):
                    raise RuntimeError("Invalid normal texture variant")
                key = normal_environment(binding["texture_environment"])
                if key in environment:
                    raise RuntimeError("Duplicate normal-map binding " + key)
                batches = json.loads((root / binding["batch_metadata"]).read_text())["batches"]
                material_order = [b["material"] for b in batches]
                identity = hashlib.sha256(
                    json.dumps(
                        dict(
                            format="BWNRM2-linear-opengl-v1",
                            sources=source_identity,
                            batches=material_order,
                        ),
                        sort_keys=True,
                    ).encode()
                ).hexdigest()
                path = folder / (model["id"] + "-" + binding["id"] + "-normals.bin")
                previous = normal_cache.get(key, {})
                digest = None
                if previous.get("identity") == identity and path.is_file():
                    with path.open("rb") as stream:
                        actual = hashlib.file_digest(stream, "sha256").hexdigest()
                    if actual == previous.get("sha256"):
                        digest = actual
                if digest is None:
                    if images is None:
                        images = load_images(root, model["normal_textures"])
                        if (
                            normal_source_identity(root, model["normal_textures"])
                            != source_identity
                        ):
                            raise RuntimeError("Normal source changed during decoding")
                    packed = pack_normals(material_order, images)
                    digest = hashlib.sha256(packed).hexdigest()
                    write_atomic(path, packed)
                normal_cache[key] = dict(identity=identity, sha256=digest)
                write_atomic(normal_cache_path, json.dumps(normal_cache, indent=1).encode())
                environment[key] = str(path)
                model_receipts.append(
                    dict(
                        id=model["id"],
                        variant=binding["id"],
                        normal_sidecar=str(path),
                        sha256=digest,
                        normal_sources=model["normal_textures"],
                        normal_format=2,
                    )
                )
        # BWTEX1: magic[8], batch/image counts, one image index per draw batch,
        # then material_pixels() records. LODs share pixels but not batch order.
        out = bytearray(b"BWTEX1\0\0" + struct.pack("<II", count, len(names)))
        out.extend(
            struct.pack(
                "<" + "I" * count, *[names.index(b["material"]) for b in metadata["batches"]]
            )
        )
        out.extend(material_pixels(root, model["textures"]))
        path = folder / (model["id"] + "-textures.bin")
        write_atomic(path, out)
        environment[model["texture_environment"]] = str(path)
        model_receipts.append(
            dict(
                id=model["id"],
                sidecar=str(path),
                sha256=hashlib.sha256(out).hexdigest(),
                texture_sources=model["textures"],
            )
        )
        # Distance meshes have different batches but use the same current
        # material pixels. Repack their indices on every launch as well.
        pixels = out[16 + 4 * count :]
        for variant in model.get("texture_variants", []):
            ident = variant["id"]
            if not ident or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in ident):
                raise RuntimeError("Invalid model texture variant")
            metadata = json.loads((root / variant["batch_metadata"]).read_text())
            batches = metadata["batches"]
            key = variant["texture_environment"]
            if not key.startswith("MW34_") or key in environment:
                raise RuntimeError("Invalid or duplicate texture variant binding")
            side = bytearray(b"BWTEX1\0\0" + struct.pack("<II", len(batches), len(names)))
            side.extend(
                struct.pack(
                    "<" + "I" * len(batches), *[names.index(b["material"]) for b in batches]
                )
            )
            side.extend(pixels)
            path = folder / (model["id"] + "-" + ident + "-textures.bin")
            write_atomic(path, side)
            environment[key] = str(path)
            model_receipts.append(
                dict(
                    id=model["id"],
                    variant=ident,
                    sidecar=str(path),
                    sha256=hashlib.sha256(side).hexdigest(),
                    texture_sources=model["textures"],
                )
            )
        # Original per-instance skin identity selects an alternate material set.
        # The same authored pixels are repacked for each original LOD's batches.
        for skin in model.get("skins", []):
            ident = skin["id"]
            skin_names = list(skin["textures"])
            if not ident or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in ident):
                raise RuntimeError("Invalid skin id")
            if skin_names != names:
                raise RuntimeError("Skin material order differs from primary materials")
            skin_pixels = material_pixels(root, skin["textures"])
            bindings = [
                dict(
                    texture_environment=skin["texture_environment"],
                    batch_metadata=model["batch_metadata"],
                    id="close",
                )
            ] + skin.get("texture_variants", [])
            for binding in bindings:
                key = binding["texture_environment"]
                if not key.startswith("MW34_") or key in environment:
                    raise RuntimeError("Invalid or duplicate skin binding")
                batches = json.loads((root / binding["batch_metadata"]).read_text())["batches"]
                side = bytearray(b"BWTEX1\0\0" + struct.pack("<II", len(batches), len(names)))
                side.extend(
                    struct.pack(
                        "<" + "I" * len(batches), *[names.index(b["material"]) for b in batches]
                    )
                )
                side.extend(skin_pixels)
                path = folder / (
                    model["id"] + "-skin-" + ident + "-" + binding["id"] + "-textures.bin"
                )
                write_atomic(path, side)
                environment[key] = str(path)
                model_receipts.append(
                    dict(
                        id=model["id"],
                        skin=ident,
                        variant=binding["id"],
                        sidecar=str(path),
                        sha256=hashlib.sha256(side).hexdigest(),
                        texture_sources=skin["textures"],
                    )
                )
    write_atomic(
        folder / "asset-receipt.json",
        json.dumps(dict(banks=receipt, models=model_receipts), indent=2).encode(),
    )
    # The launcher waits for gameplay in this process. Keep the LOD hash cache
    # useful during packing without retaining full source images during play.
    pixel_hash.cache_clear()
    return environment
