"""Explicit parent permission type and complete locale-header dependencies."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];parent=Path(__file__).parent/'connected_controls.inc';target=parent.with_name('connected_controls_v2.inc')
assert not target.exists();text=parent.read_text();text=text.replace('#include "locale_batch.hpp"','#include "carry.hpp"\n#include "locale_batch.hpp"').replace('m4_runtime::Permissions::','mw34::Permissions::');target.write_text(text)
print(json.dumps({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
