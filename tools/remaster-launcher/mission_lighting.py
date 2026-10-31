"""Data-only mission presentation settings; no commands, paths or gameplay rules."""
import json
import math
from pathlib import Path
import struct

# Order is the MW34ENV1 wire contract, independent of C++ structure padding.
FIELDS = [
    ('azimuth', 1, -360, 360), ('elevation', 1, 0, 90),
    ('sun_color', 3, 0, 4), ('sun_strength', 1, 0, 4),
    ('ambient_color', 3, 0, 4), ('ambient_strength', 1, 0, 2),
    ('night_world_gain', 1, 0, 1), ('sky_tint', 3, 0, 4),
    ('sky_brightness', 1, 0, 4), ('sky_glow_color', 3, 0, 4),
    ('sky_glow_strength', 1, 0, 4), ('sky_glow_focus', 1, 0, 20),
    ('sky_grade', 3, 0, 1), ('horizon_low', 1, 0, .9), ('horizon_high', 1, 0, 1),
    ('haze_color', 3, 0, 1), ('haze_scale', 3, 0, 4), ('fog_distance', 1, 0, 10000),
    ('shadows', 0, 0, 1), ('shadow_range', 1, 0, 10000),
    ('shadow_bias', 1, 0, 10), ('shadow_darkness', 1, 0, 1),
    ('rain_intensity', 1, 0, 1), ('wet_reflection', 1, 0, 1),
    ('has_lightning', 0, 0, 1), ('valley_fog_altitude', 1, -10000, 10000),
    ('valley_fog_density', 1, 0, 4), ('dust_intensity', 1, 0, 1),
    ('smog_intensity', 1, 0, 1), ('heat_shimmer', 1, 0, 1),
    ('volcanic_ash', 1, 0, 1), ('lava_glow', 1, 0, 1), ('is_interior', 0, 0, 1),
]
MISSIONS = {f'operation{o}': {f'c{o}m{m}' for m in range(1, count + 1)}
            for o, count in ((1, 4), (2, 4), (3, 6), (4, 6))}
MISSIONS['training'] = {f't1m{mission}' for mission in range(1, 5)}


def number(value, low, high):
    if type(value) not in (int, float) or not low <= value <= high or not math.isfinite(value):
        raise ValueError('Invalid bounded lighting number')
    return value


def validate_mission(settings):
    if not isinstance(settings, dict) or set(settings) != {f[0] for f in FIELDS} | {'env_lights'}:
        raise ValueError('Unknown or missing mission lighting field')
    for name, count, low, high in FIELDS:
        value = settings[name]
        if count == 0:
            if type(value) is not bool: raise ValueError('Lighting flags must be boolean')
        elif count == 1: number(value, low, high)
        else:
            if not isinstance(value, list) or len(value) != count: raise ValueError('Invalid lighting RGB field')
            for component in value: number(component, low, high)
    if settings['horizon_low'] >= settings['horizon_high'] and not (settings['is_interior'] and settings['horizon_low'] == settings['horizon_high'] == 0):
        raise ValueError('Invalid lighting horizon interval')
    lights = settings['env_lights']
    if not isinstance(lights, list) or len(lights) > 64: raise ValueError('Too many environment lights')
    for light in lights:
        if not isinstance(light, list) or len(light) != 3: raise ValueError('Invalid environment light')
        for index, vector in enumerate(light):
            if not isinstance(vector, list) or len(vector) != 4: raise ValueError('Invalid light vector')
            for component in vector: number(component, 0 if index == 2 else -1000000, 64 if index == 2 else 1000000)
        number(light[0][3], 0, 10000)
    return settings


def validate_training(maps):
    if not isinstance(maps, dict) or set(maps) != {'BIG LAKE'}:
        raise ValueError('Training lighting requires the registered BIG LAKE map')
    config = maps['BIG LAKE']
    if not isinstance(config, dict) or set(config) != {'default', 'presets'}:
        raise ValueError('Invalid Training preset selection')
    if not isinstance(config['presets'], dict) or not isinstance(config['default'], str) or config['default'] not in config['presets'] or not 1 <= len(config['presets']) <= 32:
        raise ValueError('Invalid Training preset selection')
    scalar = {'azimuth': (-360, 360), 'elevation': (1, 89), 'strength': (0, 4), 'ambient': (0, 2),
              'sky_brightness': (0, 4), 'sky_glow': (0, 4), 'night_world_gain': (0, 1)}
    colors = {'sun_color': 4, 'ambient_color': 4, 'sky_tint': 4, 'haze_color': 1}
    required = {'azimuth', 'elevation', 'strength', 'ambient', 'sun_color', 'ambient_color'}
    import re
    for name, preset in config['presets'].items():
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,31}', name) or not isinstance(preset, dict) or not required <= preset.keys() or preset.keys() - (scalar.keys() | colors.keys() | {'sky_auto'}):
            raise ValueError('Unsupported Training lighting preset')
        for key, value in preset.items():
            if key in scalar: number(value, *scalar[key])
            elif key in colors:
                if not isinstance(value, list) or len(value) != 3: raise ValueError('Invalid Training RGB')
                for component in value: number(component, 0, colors[key])
            elif type(value) is not bool: raise ValueError('Invalid Training sky_auto flag')
    return maps


def validate(data, operation):
    if not isinstance(data, dict) or set(data) != {'schema_version', 'missions', 'maps'} or type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise ValueError('Unsupported lighting catalog')
    if not isinstance(data['missions'], dict) or (set(data['missions']) != MISSIONS[operation] and not (operation == 'training' and not data['missions'])):
        raise ValueError('Incomplete or out-of-operation mission lighting')
    for settings in data['missions'].values(): validate_mission(settings)
    if operation == 'training': validate_training(data['maps'])
    elif data['maps'] != {}: raise ValueError('Campaign packs cannot override Training lighting')
    return data


def encode(missions):
    result = bytearray(b'MW34ENV1' + struct.pack('<I', len(missions)))
    for ident, settings in sorted(missions.items()):
        validate_mission(settings)
        if ident not in set().union(*MISSIONS.values()): raise ValueError('Unknown mission identity')
        raw = ident.encode('ascii')
        result += struct.pack('<I', len(raw)) + raw
        for name, count, _, _ in FIELDS:
            value = settings[name]
            result += struct.pack('<I', int(value)) if count == 0 else struct.pack('<' + 'f' * count, *([value] if count == 1 else value))
        result += struct.pack('<I', len(settings['env_lights']))
        for light in settings['env_lights']:
            for vector in light: result += struct.pack('<4f', *vector)
    return bytes(result)


def apply_training(selected, native):
    pack = selected.get('training')
    if pack and pack.get('lighting'):
        config = pack['lighting']['maps']['BIG LAKE']
        native['sun_preset'] = dict(source=pack['paths'][pack['registry']['lighting']], map='BIG LAKE', default=config['default'])


def prepare(selected, output):
    missions = {}
    for pack in selected.values():
        if pack.get('lighting'): missions.update(pack['lighting']['missions'])
    if not missions: return {}
    path = Path(output) / 'mission-lighting.bin'
    path.write_bytes(encode(missions))
    return {'MW34_MISSION_ENVIRONMENTS': str(path.resolve())}
