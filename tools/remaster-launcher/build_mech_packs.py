"""Build local prepared-runtime mech packs; never modify the selected launcher.

Schema 2 is a new content contract, not supported by the existing schema-1 UI.
Only registered mech bindings are packaged; no executable or world bank enters
the output. Private provenance stays beside, rather than inside, the archives.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from content_capabilities import measured_donor_hinges

ROOT = Path(__file__).resolve().parents[2]
MW3 = {"strider", "avatar", "owens", "firefly"}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def bindings(model):
    """Exact existing preparer key set, including LODs and alternate skins."""
    result = dict(model["environment"])
    textures = [model["texture_environment"]]
    textures += [v["texture_environment"] for v in model.get("texture_variants", [])]
    for skin in model.get("skins", []):
        textures.append(skin["texture_environment"])
        textures += [v["texture_environment"] for v in skin.get("texture_variants", [])]
    result.update({key: None for key in textures})
    if "normal_textures" in model:
        for key in [model["texture_environment"]] + [
            v["texture_environment"] for v in model.get("texture_variants", [])
        ]:
            result[key[:-9] + "_NORMALS"] = None
    return result


def file_format(path):
    with path.open("rb") as stream:
        magic = stream.read(8)
    if magic.startswith(b"BWMESH") and magic[6:7] in b"123456" and magic[7:] == b"\0":
        return "BWMESH" + magic[6:7].decode()
    if magic in (b"BWTEX1\0\0", b"BWNRM2\0\0"):
        return magic.rstrip(b"\0").decode()
    raise ValueError(f"Unsupported prepared payload magic: {path}: {magic!r}")


def verify_archive(path):
    """Read every member, verify hashes/closure, and reject leaked absolute paths."""
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("pack.json"))
        assert manifest["schema_version"] == 2
        declared = manifest["files"]
        assert len(archive.namelist()) == len(set(archive.namelist()))
        assert set(archive.namelist()) == {"pack.json", *declared}
        for name, pin in declared.items():
            assert not name.startswith("/") and ":" not in name and "\\" not in name
            assert ".." not in name.split("/")
            with archive.open(name) as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            assert actual == pin["sha256"], name
            assert archive.getinfo(name).file_size == pin["bytes"], name
        registry = json.loads(archive.read(manifest["native_payload"]["registry"]))
        used = {manifest["native_payload"]["registry"]}
        for model in registry["models"]:
            assert model["backend"] == "native"
            for key, name in model["environment"].items():
                assert key.startswith("MW34_") and name in declared
                used.add(name)
                with archive.open(name) as stream:
                    magic = stream.read(8).rstrip(b"\0").decode()
                assert magic == declared[name]["format"]
        assert used == set(declared)
        for name in ("pack.json", manifest["native_payload"]["registry"]):
            raw = archive.read(name)
            assert b"D:\\" not in raw and b"C:\\" not in raw and b"C:/" not in raw
        return manifest


def build(profile_path, output):
    if output.exists():
        raise ValueError("Output must be a fresh directory")
    profile_pin = digest(profile_path)
    config = json.loads(profile_path.read_text(encoding="utf-8-sig"))["native"]
    registry_path = ROOT / config["model_registry"]
    registry_pin = digest(registry_path)
    models = json.loads(registry_path.read_text(encoding="utf-8-sig"))["models"]
    assert len(models) == 18 and len({m["id"] for m in models}) == 18
    assert MW3 <= {m["id"] for m in models}
    output.mkdir(parents=True)
    provenance = []
    frozen = {}
    summaries = []
    with tempfile.TemporaryDirectory(prefix="mw3-pack-", dir=output) as temp:
        work = Path(temp)

        def freeze(value):
            source = (ROOT / value).resolve()
            if source in frozen:
                return frozen[source]
            before = source.stat()
            target = work / "frozen" / str(len(frozen)) / source.name
            target.parent.mkdir(parents=True)
            shutil.copyfile(source, target)
            pin = digest(target)
            after = source.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError(f"Source changed while copying: {source}")
            if pin != digest(source):
                raise RuntimeError(f"Source copy identity mismatch: {source}")
            provenance.append(dict(source=str(source), sha256=pin, bytes=after.st_size))
            frozen[source] = target
            return target

        selected = {}
        for model in models:
            ident = model["id"]
            keys = bindings(model)
            generated = {}
            if any(value is None and key not in config["runtime_environment"] for key, value in keys.items()):
                # Prepare only missing model resources from frozen inputs. The
                # existing encoder couples banks to models; this private empty
                # bank list avoids accessing world assets. Its index is discarded.
                from native_assets import prepare

                snapshot = copy.deepcopy(model)

                def relocate(record):
                    record.pop("required_files", None)
                    for field in ("textures", "normal_textures", "environment"):
                        if field in record:
                            record[field] = {
                                k: str(freeze(v)) if v is not None else None
                                for k, v in record[field].items()
                            }
                    if "batch_metadata" in record:
                        record["batch_metadata"] = str(freeze(record["batch_metadata"]))
                    for field in ("skins", "texture_variants"):
                        for child in record.get(field, []):
                            relocate(child)

                relocate(snapshot)
                prep_root = work / (ident + "-prep-root")
                write_json(prep_root / "local/work-ahead/texture-launcher-audit-v2/configured-banks.json", [])
                generated = prepare(prep_root, [snapshot], output=work / (ident + "-prepared"))
            selected[ident] = {}
            for key, fallback in keys.items():
                override = config["runtime_environment"].get(key)
                if override is not None:
                    path = freeze(override)
                elif fallback is not None:
                    path = freeze(fallback)
                else:
                    path = Path(generated[key])
                selected[ident][key] = path
            print(f"Frozen {ident}: {len(keys)} native bindings", flush=True)

        for suffix, title, is_mw3 in (
            ("mw5-mechs", "MW5 Replacement Mechs", False),
            ("updated-mw3-mechs", "Updated MW3 Mechs", True),
        ):
            pack_id = "com.mw3remaster." + suffix
            stage = work / suffix
            stage.mkdir()
            files = {}
            records = []
            for model in models:
                ident = model["id"]
                if (ident in MW3) != is_mw3:
                    continue
                environment = {}
                formats = set()
                for key, source in selected[ident].items():
                    fmt = file_format(source)
                    if key.endswith("_NORMALS") and fmt != "BWNRM2":
                        raise ValueError(f"Wrong normal format: {key}")
                    if key.endswith("_TEXTURES") and fmt != "BWTEX1":
                        raise ValueError(f"Wrong color format: {key}")
                    pin = digest(source)
                    name = "payload/" + pin + ".bin"
                    if name not in files:
                        target = stage / name
                        target.parent.mkdir(exist_ok=True)
                        shutil.copyfile(source, target)
                        files[name] = dict(sha256=pin, bytes=target.stat().st_size, format=fmt)
                    environment[key] = name
                    formats.add(fmt)
                records.append(dict(
                    id=ident, name=model["name"], backend="native", status=model["status"],
                    environment=environment, required_formats=sorted(formats),
                    skin_ids=[s["id"] for s in model.get("skins", [])],
                ))
            registry_name = "models/models.json"
            write_json(stage / registry_name, dict(schema_version=2, payload_profile="prepared-native-v1", models=records))
            files[registry_name] = dict(sha256=digest(stage / registry_name), bytes=(stage / registry_name).stat().st_size)
            manifest = dict(
                schema_version=2, game_id="mw3", id=pack_id, name=title, version="0.1.0-local.20261021",
                author="MW3 Remaster Project", category="Mechs",
                description="Local prepared native visual assets; original gameplay remains in control.",
                distribution="local-only; no redistribution clearance",
                provides=dict(mechs=[m["id"] for m in records], textures=True, normal_maps=True),
                native_payload=dict(profile="prepared-native-v1", registry=registry_name,
                    path_base="pack-root", required_capabilities={'prepared-mechs':1}, reference_host_sha256=config["executable_sha256"],
                    required_formats=sorted({f for m in records for f in m["required_formats"]})),
                files=files,
            )
            if any(pin.get('format') == 'BWMESH4' and measured_donor_hinges(stage / name)
                   for name, pin in files.items()):
                manifest['native_payload']['required_capabilities']['donor-rig-hinges'] = 1
            write_json(stage / "pack.json", manifest)
            archive_path = output / (pack_id + ".mw3pack")
            partial = archive_path.with_suffix(".partial")
            with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
                for path in sorted(stage.rglob("*")):
                    if path.is_file():
                        archive.write(path, path.relative_to(stage).as_posix())
            verify_archive(partial)
            partial.rename(archive_path)
            summaries.append(dict(file=archive_path.name, sha256=digest(archive_path),
                bytes=archive_path.stat().st_size, installed_bytes=sum(f["bytes"] for f in files.values()) + (stage / "pack.json").stat().st_size,
                models=[r["id"] for r in records], payload_files=len(files)))
            print(json.dumps(summaries[-1]), flush=True)
        if digest(profile_path) != profile_pin or digest(registry_path) != registry_pin:
            raise RuntimeError("Selected configuration changed during packaging")
        for entry in provenance:
            if digest(Path(entry["source"])) != entry["sha256"]:
                raise RuntimeError("Source changed during packaging: " + entry["source"])
    write_json(output / "private-build-provenance.json", dict(
        profile=str(profile_path), profile_sha256=profile_pin,
        registry=str(registry_path), registry_sha256=registry_pin, sources=provenance))
    write_json(output / "packs.json", dict(schema_version=1, verified=True, packs=summaries))
    return summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=ROOT / "local/remaster/launcher.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.profile.resolve(), args.output.resolve())
