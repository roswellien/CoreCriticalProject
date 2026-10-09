"""Hash-admitted static graphics GUID leads; presence is not observed API use."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
from pe import PEImage, load_manifest, validate_identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("sdk_um", type=Path, help="Windows SDK um header directory")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    protected = [args.binary, args.sdk_um / "ddraw.h", args.sdk_um / "d3d.h"]
    if args.output.resolve() in {path.resolve() for path in protected}:
        raise ValueError("Output must differ from binary and SDK headers")
    data = args.binary.read_bytes()
    image = PEImage(data)
    manifest = Path(__file__).resolve().parents[2] / "games/mw3/config/supported-binaries.json"
    admitted = validate_identity(data, load_manifest(manifest), image)
    matches, headers = [], []
    for filename in ("ddraw.h", "d3d.h"):
        source = (args.sdk_um / filename).read_bytes()
        headers.append({"name": filename, "sha256": hashlib.sha256(source).hexdigest()})
        definitions = re.findall(r"DEFINE_GUID\s*\(\s*(IID_IDirect(?:Draw|3D)\w*)\s*,([^)]*)\)", source.decode("utf-8", errors="strict"))
        for name, values in definitions:
            numbers = [int(value.strip(), 0) for value in values.split(",")]
            if len(numbers) != 11:
                raise ValueError(f"Unexpected GUID definition: {name}")
            pattern = struct.pack("<IHH8B", *numbers)
            offset = data.find(pattern)
            while offset != -1:
                locations = []
                for section in image.sections:
                    if section["raw_offset"] <= offset and offset + 16 <= section["raw_offset"] + section["raw_size"]:
                        rva = section["virtual_address"] + offset - section["raw_offset"]
                        locations.append({"section": section["name"], "rva": rva, "va": image.image_base + rva})
                matches.append({"name": name, "file_offset": offset, "locations": locations})
                offset = data.find(pattern, offset + 1)
    report = {"schema_version": 1, "binary_id": admitted["id"], "sha256": hashlib.sha256(data).hexdigest(),
              "headers": headers, "matches": matches,
              "scope": "Exact static GUID byte matches only. No call reachability, interface creation, runtime use or renderer compatibility established."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{len(matches)} static graphics GUID leads; report: {args.output}")
    for match in matches:
        print(match["name"], match["locations"])


if __name__ == "__main__":
    main()
