import json

with open('local/remaster/runs/20261019-211434-555/mesh-runtime.jsonl') as f:
    for line in f:
        data = json.loads(line)
        if data.get('event') == 'surface_normal_bound':
            print(f"Texture {data.get('texture')}: {data.get('source_width')}x{data.get('source_height')} fmt={data.get('source_format')} hash={hex(data.get('source_hash'))}")
