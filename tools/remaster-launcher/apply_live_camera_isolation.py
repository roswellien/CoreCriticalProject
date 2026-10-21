"""Install the validated render-only camera scope after photo/distance adapters.

Use a private copy of the current host. Validate both files before writing;
unknown photo revisions must be merged explicitly rather than overwritten.
"""
from pathlib import Path
import argparse
import hashlib

SOURCE = Path(__file__).parent / 'native-overrides'
PHOTO_BASE = '7bdbb27216314e99c333e2ce15f372e7a76ad554a01fc9da1f7ef9f7ea3eaa97'


def apply(host: Path):
    photo = host / 'photo_replay_stage.inc'
    replacement = (SOURCE / photo.name).read_bytes()
    current = photo.read_bytes()
    if current != replacement and hashlib.sha256(current).hexdigest() != PHOTO_BASE:
        raise ValueError('Unknown photo adapter revision; preserve and merge its changes first')
    mfc = host / 'mfc_stage.hpp'
    text = mfc.read_text()
    old = '  if((target==0x4b52c0||target==0x4f6dc0||target==0x4f7030||target==0x4f73f0)&&(distance_requested()>800||distance_fog_requested()||distance_log()))return distance_camera_body(s,target,p,body);'
    new = '  if((target==0x4b52c0||target==0x4f6dc0||target==0x4f7030||target==0x4f73f0)&&(distance_requested()>800||distance_fog_requested()||distance_log())){if(target==0x4b52c0||target==0x4f6dc0||target==0x4f7030)return photo_replay_body(s,target,p,[&]{return distance_camera_body(s,target,p,body);});return distance_camera_body(s,target,p,body);}'
    if new not in text:
        if text.count(old) != 1:
            raise ValueError('Unknown distance/render dispatch; no files changed')
        text = text.replace(old, new, 1)
    elif text.count(new) != 1:
        raise ValueError('Duplicate render scope; no files changed')
    photo.write_bytes(replacement)
    mfc.write_text(text)
    print('Installed render-only camera isolation in', host)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-source', type=Path, required=True)
    apply(parser.parse_args().host_source)
