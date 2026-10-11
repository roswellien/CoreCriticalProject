"""Package one strictly bounded recovered profile for the Vulkan replay experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from describe_capture import decode_rgb
from verify_capture import verify, verify_presentation_diagnostic


def legacy_filter(row):
    getters = row.get("legacy_filter_getters", [])
    history = row.get("filter_setter_history", {}).get("legacy_render", [])
    stages = row.get("filter_setter_history", {}).get("stage0", [])
    if len(getters) != 3 or len(history) != 3 or len(stages) != 3:
        raise ValueError("Legacy filtering evidence missing")
    for i, state_id in enumerate((17, 18)):
        getter, setter = getters[i], history[i]
        if getter["state"] != state_id or getter["hresult"] < 0 or not setter or setter["serial"] <= 0 or getter["value"] != setter["value"]:
            raise ValueError("Legacy getter/setter disagreement or failed evidence")
        if stages[i] and stages[i]["serial"] > setter["serial"]:
            raise ValueError("Later stage setter makes legacy precedence ambiguous")
    if getters[0]["value"] != getters[1]["value"] or getters[0]["value"] not in (1, 2):
        raise ValueError("Mixed or mipmapped legacy filtering is not supported")
    return int(getters[0]["value"] == 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument('--diagnostic-presentation', action='store_true',
                        help='Package only observed draws from an explicitly incomplete flip interval; grants no acceptance')
    parser.add_argument("--filter-source", choices=("stage", "legacy"), default="stage",
                        help="Legacy requires successful legacy getter and setter evidence on every draw")
    args = parser.parse_args()
    receipt = (verify_presentation_diagnostic if args.diagnostic_presentation else verify)(args.directory)
    rows = [json.loads(line) for line in (args.directory / "capture.jsonl").read_text().splitlines()]
    image = next(r["surface"] for r in rows if r["event"] == "initial_target")
    depth = next(r["surface"] for r in rows if r["event"] == "initial_depth")
    width, height = image["width"], image["height"]
    if depth["bits"] != 16 or depth["flags"] != 1024 or depth["g_mask"] != 65535:
        raise ValueError("Only the captured 16-bit Z profile is admitted")
    initial = decode_rgb(image, (args.directory / image["file"]).read_bytes())
    z = b"".join(struct.pack("<f", value / 65535) for (value,) in struct.iter_unpack("<H", (args.directory / depth["file"]).read_bytes()))
    textures = [(1, 1, b"\xff\xff\xff\xff")]
    texture_ids = {}
    draws = []
    for row in rows:
        if row["event"] != "draw":
            continue
        state = row["render_states"]
        required = {"7":1,"23":7,"15":0,"19":5,"20":6,"22":1,"28":1,"35":0,"29":0,"4":1,"2":0,"40":0,"41":0,"47":0,"52":0}
        if any(state[key] != value for key, value in required.items()) or state["9"] not in (1,2) or state["14"] not in (0,1):
            raise ValueError("Render state outside recovered replay profile")
        if row["fvf"] != 452 or row["index_count"] or row["primitive"] not in (5,6):
            raise ValueError("Draw outside TL triangle-fan/strip profile")
        viewport = row["viewport"]
        if (viewport["x"],viewport["y"],viewport["width"],viewport["height"],viewport["min_z_bits"],viewport["max_z_bits"]) != (0,0,width,height,0,1065353216):
            raise ValueError("Viewport outside recovered profile")
        stage = row["stages"][0]
        ss = stage["states"]
        expected = {"1":4,"2":2,"3":0,"5":2,"6":0,"11":0,"16":1,"17":1,"18":1,"19":0,"20":0}
        if any(ss[key] != value for key,value in expected.items()) or ss["4"] not in (2,4) or ss["13"] not in (1,3) or ss["14"] not in (1,3):
            raise ValueError("Texture stage outside recovered profile")
        if any(s["states"]["1"] != 1 for s in row["stages"][1:]):
            raise ValueError("Additional texture stages active")
        texture_id = 0
        info = stage["texture"]
        if info:
            key = json.dumps(info,sort_keys=True)
            if key not in texture_ids:
                texture_ids[key] = len(textures)
                textures.append((info["width"],info["height"],decode_rgb(info,(args.directory/info["file"]).read_bytes())))
            texture_id = texture_ids[key]
        original = (args.directory/row["vertices"]).read_bytes()
        vertices = [original[i:i+32] for i in range(0,len(original),32)]
        for vertex in vertices:
            x,y,depth_value,rhw = struct.unpack_from("<4f",vertex)
            import math
            if not all(map(math.isfinite,(x,y,depth_value,rhw))) or rhw <= 0:
                raise ValueError("Nonfinite/nonpositive transformed vertex")
        triangles = []
        for i in range(len(vertices)-2):
            order = (0,i+1,i+2) if row["primitive"] == 6 else ((i,i+1,i+2) if i%2==0 else (i,i+2,i+1))
            triangles.extend(vertices[index] for index in order)
        settings = (texture_id,len(triangles),state["9"],ss["4"]==4,state["28"],state["27"],ss["13"],ss["14"],state["34"])
        filtering = 0
        if args.filter_source == "legacy":
            filtering = legacy_filter(row)
        draws.append(struct.pack("<11I",*settings,filtering,state["14"])+b"".join(triangles))
    blob = bytearray(b"MW34SCN3"+struct.pack("<4I",width,height,len(textures),len(draws))+initial+z)
    for w,h,rgba in textures:
        blob += struct.pack("<2I",w,h)+rgba
    for draw in draws:
        blob += draw
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(blob)
    receipt.update({"package_sha256":hashlib.sha256(blob).hexdigest(),"package_bytes":len(blob),"textures":len(textures),
                    "filter_source":args.filter_source,
                    "profile":"TL32, triangle fans/strips, single texture, vertex fog, alpha blend, greater Z; raster equivalence unproven"})
    args.output.with_suffix(".json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2))


if __name__ == "__main__":
    main()
