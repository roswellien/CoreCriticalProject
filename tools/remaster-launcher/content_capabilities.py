"""Versioned resource contracts from an authored runtime profile, not pack identity.

The frozen legacy table migrates already reviewed runtimes only. New runtimes
advertise content_capabilities in their integrity-pinned profile. Pack reference
host hashes are historical metadata and never grant a capability.
"""
import json
from pathlib import Path

PROFILES = {
    'prepared-ui-v1': 'ui-artwork',
    'prepared-cinematic-v1': 'cinematic-replacements',
    'prepared-native-v1': 'prepared-mechs',
    'prepared-environment-v1': 'environment-resources',
    'prepared-music-v1': 'soundtrack',
    'prepared-skins-v1': 'additional-mech-skins',
    'additional-chassis-v1': 'additional-mech-chassis',
}


def advertised(host):
    if 'content_capabilities' in host:
        table = host['content_capabilities']
    else:
        legacy = json.loads(Path(__file__).with_name('legacy_content_capabilities.json').read_text())
        table = legacy['hosts'].get(host.get('executable_sha256', '').lower(), {})
    if not isinstance(table, dict) or len(table) > 64:
        raise ValueError('Invalid runtime content capabilities')
    for name, versions in table.items():
        if (not isinstance(versions, list) or not 1 <= len(versions) <= 16 or
                any(type(v) is not int or v < 1 for v in versions) or len(set(versions)) != len(versions)):
            raise ValueError('Invalid runtime capability versions: ' + name)
    return {name: list(versions) for name, versions in table.items()}


def require(host, payload, ident):
    profile = payload.get('profile')
    if profile not in PROFILES:
        raise ValueError('Unsupported content profile: ' + str(profile))
    extra = payload.get('required_capabilities', {})
    if (not isinstance(extra, dict) or len(extra) > 32 or any(
            name not in {*PROFILES.values(), 'mech-headlights', 'legacy-mech-skins', 'surface-materials', 'donor-rig-hinges'}
            or type(version) is not int or version < 1
            for name, version in extra.items())):
        raise ValueError('Invalid content capability requirements')
    table = advertised(host)
    for name, version in [(PROFILES[profile], 1), *extra.items()]:
        if version not in table.get(name, []):
            raise ValueError(f"Pack '{ident}' requires {name} version {version}. Update the game runtime or choose a compatible pack.")


def measured_donor_hinges(path):
    """Inspect the optional wire flag without loading a large geometry payload."""
    with Path(path).open('rb') as stream:
        header = stream.read(24)
    return (len(header) == 24 and header[:8] == b'BWMESH4\0'
            and bool(int.from_bytes(header[20:24], 'little') & 2))


def require_measured_donor_hinges(path, payload):
    if (measured_donor_hinges(path)
            and payload.get('required_capabilities', {}).get('donor-rig-hinges') != 1):
        raise ValueError('Measured hinge rig requires donor-rig-hinges version 1')
