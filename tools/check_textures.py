import json

with open("local/remaster/runs/20261019-204423-011/mesh-runtime.jsonl", "r") as f:
    for line in f:
        d = json.loads(line)
        if d.get("event") == "surface_normal_bound":
            w = d.get("source_width")
            h = d.get("source_height")
            fmt = d.get("source_format")
            shash = hex(d.get("source_hash"))
            print(f"{w}x{h} fmt={fmt} hash={shash}")
