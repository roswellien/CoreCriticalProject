"""Apply launcher graphics choices after content composition, never from a pack.

Profiles without this versioned policy retain the explicit research/preview
workflow. Normal launcher sessions always supply it and require its coordinator.
"""
from pathlib import Path
import hashlib


def choice(host):
    policy = host.get('presentation')
    if policy is None:
        return None
    if (not isinstance(policy, dict) or not {'schema_version', 'dynamic_lighting'} <= policy.keys()
            or policy.keys() - ({'schema_version', 'dynamic_lighting', 'shadows', 'headlights'} if policy.get('schema_version') == 2 else {'schema_version', 'dynamic_lighting', 'shadows'})
            or type(policy['schema_version']) is not int or policy['schema_version'] not in (1, 2)
            or type(policy['dynamic_lighting']) is not bool
            or type(policy.get('shadows', False)) is not bool
            or type(policy.get('headlights', False)) is not bool):
        raise ValueError('Unsupported launcher presentation settings')
    if policy['schema_version'] not in host.get('stock_presentation_versions', []):
        raise ValueError('Install the stock presentation runtime update before using these graphics settings')
    return policy['dynamic_lighting']


def catalog(host):
    pin = host.get('stock_effect_lighting', {})
    path = Path(pin.get('catalog', ''))
    if (not path.is_file() or path.stat().st_size != pin.get('bytes')
            or not 12 <= path.stat().st_size <= 4 * 1024**2):
        raise ValueError('The dynamic lighting runtime material catalogue is missing or invalid')
    with path.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != pin.get('sha256'):
            raise ValueError('The dynamic lighting runtime material catalogue changed')
    return str(path.resolve())


def environment(host, selected, bindings):
    """Pure flag/resource selection; run again after loading any cached bindings."""
    enabled = choice(host)
    result = dict(bindings)
    if enabled is None:
        return result
    defaults = host.get('dynamic_lighting_defaults', {})
    normal_strength = str(defaults.get('normal_strength', bindings.get('MW34_SUN_NORMAL_STRENGTH', '1')))
    ground_strength = str(defaults.get('ground_normal_strength', bindings.get('MW34_SUN_GROUND_NORMAL_STRENGTH', '1')))
    # The old global night/manual preview must never be a no-pack fallback.
    for key in list(result):
        if key.startswith(('MW34_SKY_', 'MW34_HAZE_', 'MW34_SUN_')):
            result.pop(key)
    result.update(MW34_CAMPAIGN_LIGHTING='0', MW34_MANUAL_LIGHTING='0',
                  MW34_WEATHER='0', MW34_SKY_AUTO='0', MW34_NIGHT_WORLD_GAIN='1',
                  MW34_SUN_SHADOWS='0', MW34_FIXTURE_SHADOWS='0',
                  MW34_MECH_HEADLIGHTS='0', MW34_HEADLIGHT_AI='0',
                  MW34_MISSILE_EXHAUST='0', MW34_SUN='0', MW34_NORMAL_MAPS='0',
                  MW34_EFFECT_LIGHTS='0', MW34_FIXTURE_LIGHTS='0',
                  MW34_WATER_DETAIL='0', MW34_SURF_DETAIL='0', MW34_CLOUD_DETAIL='0')
    result.pop('MW34_EFFECT_LIGHT_CATALOG', None)
    result.pop('MW34_MISSION_ENVIRONMENTS', None)
    if not enabled:
        return result
    # Before a campaign map loads, the receiver starts at identity and adds
    # actual dynamic lights. Campaign maps use the host's authored settings.
    # The native host contains validated built-in settings for each campaign
    # map. A selected environment pack may replace them, but does not enable
    # per-map lighting itself. Without this flag the global Training/IA preview
    # values can darken C1M1 and every other campaign map.
    result.update(MW34_SUN='1', MW34_SUN_STRENGTH='0', MW34_SUN_AMBIENT='1',
                  MW34_SUN_COLOR='1,1,1', MW34_SUN_AMBIENT_COLOR='1,1,1',
                  MW34_CAMPAIGN_LIGHTING='1',
                  MW34_MECH_HEADLIGHTS='1' if host['presentation'].get('headlights', False) else '0',
                  MW34_WEATHER='1',
                  MW34_EFFECT_LIGHTS='1', MW34_FIXTURE_LIGHTS='1',
                  MW34_FIXTURE_SHADOWS='1' if host['presentation'].get('shadows', False) else '0')
    pack = next((p for p in selected.values() if 'effects' in p['registry']), None)
    if pack:
        result['MW34_EFFECT_LIGHT_CATALOG'] = pack['paths'][pack['registry']['effects']]
    else:
        result['MW34_EFFECT_LIGHT_CATALOG'] = catalog(host)
    if any(key in result for key in ('MW34_WORLD_NORMALS', 'MW34_SURFACE_NORMALS')):
        # SUN_NORMALS selects RGB diagnostic visualization (ambient.w), not
        # perturbation. Normal textures are enabled independently by NORMAL_MAPS.
        result.update(MW34_NORMAL_MAPS='1', MW34_SUN_NORMALS='0',
                      MW34_SUN_NORMAL_STRENGTH=normal_strength,
                      MW34_SUN_GROUND_NORMAL_STRENGTH=ground_strength)
    # Existing v1 environment packs bundle their authored conditions. Separating
    # those components is a later pack-format migration, not an implicit default.
    missions = any(p.get('lighting', {}).get('missions') for p in selected.values()
                   if p.get('lighting'))
    if missions and bindings.get('MW34_MISSION_ENVIRONMENTS'):
        result.update(MW34_CAMPAIGN_LIGHTING='1', MW34_WEATHER='1',
                      MW34_MISSION_ENVIRONMENTS=bindings['MW34_MISSION_ENVIRONMENTS'])
        result['MW34_SUN_SHADOWS'] = '1' if host['presentation'].get('shadows', False) else '0'
    for role in ('water', 'surf', 'cloud'):
        if 'MW34_' + role.upper() + '_NORMALS' in result:
            result['MW34_' + role.upper() + '_DETAIL'] = '1'
    return result


def apply(host, selected):
    enabled = choice(host)
    if enabled is None:
        return
    # An old Training preset is another route to force lighting after Python.
    # Explicit v1 environment-pack presets are restored only in the on path.
    if not enabled or not selected.get('training', {}).get('lighting'):
        host.pop('sun_preset', None)
    host['runtime_environment'] = environment(host, selected, host.get('runtime_environment', {}))
    path = host['runtime_environment'].get('MW34_EFFECT_LIGHT_CATALOG')
    if path:
        with Path(path).open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        host['effect_lighting'] = dict(catalog=path, sha256=digest)
