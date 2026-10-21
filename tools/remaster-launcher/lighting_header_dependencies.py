"""Shared authored dependencies of the campaign-aware sun header."""
from pathlib import Path
import shutil

def copy_lighting_dependencies(host):
    root=Path(__file__).resolve().parents[2]
    shared=Path(__file__).parent/'native-overrides'
    for name in ['campaign_lighting.hpp','fixture_lighting.hpp']:
        shutil.copyfile(shared/name,host/name)
    for name in ['effect_lighting.hpp','material_normals.hpp']:
        shutil.copyfile(root/'runtime/graphics'/name,host/name)
