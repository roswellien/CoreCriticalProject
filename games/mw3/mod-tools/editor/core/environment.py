"""Environment, Atmospheric Lighting, and Weather Engine.

Implements the time-of-day solver, atmospheric sky/fog models, dynamic weather channels,
and binary serialization for the native engine's MW34ENV1 binary lighting catalog.
"""

import json
import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Field definition matching tools/remaster-launcher/mission_lighting.py wire contract
ENV_FIELDS = [
    ('azimuth', 1, -360.0, 360.0),
    ('elevation', 1, 0.0, 90.0),
    ('sun_color', 3, 0.0, 4.0),
    ('sun_strength', 1, 0.0, 4.0),
    ('ambient_color', 3, 0.0, 4.0),
    ('ambient_strength', 1, 0.0, 2.0),
    ('night_world_gain', 1, 0.0, 1.0),
    ('sky_tint', 3, 0.0, 4.0),
    ('sky_brightness', 1, 0.0, 4.0),
    ('sky_glow_color', 3, 0.0, 4.0),
    ('sky_glow_strength', 1, 0.0, 4.0),
    ('sky_glow_focus', 1, 0.0, 20.0),
    ('sky_grade', 3, 0.0, 1.0),
    ('horizon_low', 1, 0.0, 0.9),
    ('horizon_high', 1, 0.0, 1.0),
    ('haze_color', 3, 0.0, 1.0),
    ('haze_scale', 3, 0.0, 4.0),
    ('fog_distance', 1, 0.0, 10000.0),
    ('shadows', 0, 0, 1),
    ('shadow_range', 1, 0.0, 10000.0),
    ('shadow_bias', 1, 0.0, 10.0),
    ('shadow_darkness', 1, 0.0, 1.0),
    ('rain_intensity', 1, 0.0, 1.0),
    ('wet_reflection', 1, 0.0, 1.0),
    ('has_lightning', 0, 0, 1),
    ('valley_fog_altitude', 1, -10000.0, 10000.0),
    ('valley_fog_density', 1, 0.0, 4.0),
    ('dust_intensity', 1, 0.0, 1.0),
    ('smog_intensity', 1, 0.0, 1.0),
    ('heat_shimmer', 1, 0.0, 1.0),
    ('volcanic_ash', 1, 0.0, 1.0),
    ('lava_glow', 1, 0.0, 1.0),
    ('is_interior', 0, 0, 1),
]


def _clamp(v: float, low: float, high: float) -> float:
    return max(low, min(high, float(v)))


@dataclass
class EnvironmentConfig:
    """Full atmosphere, lighting and dynamic weather configuration."""

    preset_name: str = "sunset"
    time_of_day: float = 18.0  # Hours [0.0 .. 24.0]

    # Sun / Moon Direction & Lighting
    azimuth: float = 235.0
    elevation: float = 28.0
    sun_color: List[float] = field(default_factory=lambda: [1.0, 0.75, 0.5])
    sun_strength: float = 0.90
    ambient_color: List[float] = field(default_factory=lambda: [0.38, 0.32, 0.45])
    ambient_strength: float = 0.22
    night_world_gain: float = 0.0

    # Sky & Horizon
    sky_tint: List[float] = field(default_factory=lambda: [0.38, 0.28, 0.48])
    sky_brightness: float = 1.0
    sky_glow_color: List[float] = field(default_factory=lambda: [1.0, 0.55, 0.25])
    sky_glow_strength: float = 1.2
    sky_glow_focus: float = 3.5
    sky_grade: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    horizon_low: float = 0.0
    horizon_high: float = 0.45

    # Haze & Distance Fog
    haze_color: List[float] = field(default_factory=lambda: [0.65, 0.45, 0.35])
    haze_scale: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    fog_distance: float = 1200.0

    # Shadows
    shadows: bool = True
    shadow_range: float = 400.0
    shadow_bias: float = 0.005
    shadow_darkness: float = 0.75

    # Dynamic Weather Effects
    rain_intensity: float = 0.0        # 0.0 to 1.0
    wet_reflection: float = 0.0        # 0.0 to 1.0
    has_lightning: bool = False
    valley_fog_altitude: float = 0.0
    valley_fog_density: float = 0.0
    dust_intensity: float = 0.0        # 0.0 to 1.0
    smog_intensity: float = 0.0        # 0.0 to 1.0
    heat_shimmer: float = 0.0          # 0.0 to 1.0
    volcanic_ash: float = 0.0          # 0.0 to 1.0
    lava_glow: float = 0.0             # 0.0 to 1.0
    is_interior: bool = False

    # Environmental point/directional light sources
    env_lights: List[List[List[float]]] = field(default_factory=list)

    # Legacy compatibility aliases
    @property
    def strength(self) -> float:
        return self.sun_strength

    @strength.setter
    def strength(self, val: float) -> None:
        self.sun_strength = val

    @property
    def ambient(self) -> float:
        return self.ambient_strength

    @ambient.setter
    def ambient(self, val: float) -> None:
        self.ambient_strength = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preset_name": self.preset_name,
            "time_of_day": round(self.time_of_day, 2),
            "azimuth": round(self.azimuth, 2),
            "elevation": round(self.elevation, 2),
            "sun_color": [round(c, 3) for c in self.sun_color],
            "sun_strength": round(self.sun_strength, 3),
            "ambient_color": [round(c, 3) for c in self.ambient_color],
            "ambient_strength": round(self.ambient_strength, 3),
            "night_world_gain": round(self.night_world_gain, 3),
            "sky_tint": [round(c, 3) for c in self.sky_tint],
            "sky_brightness": round(self.sky_brightness, 3),
            "sky_glow_color": [round(c, 3) for c in self.sky_glow_color],
            "sky_glow_strength": round(self.sky_glow_strength, 3),
            "sky_glow_focus": round(self.sky_glow_focus, 3),
            "sky_grade": [round(c, 3) for c in self.sky_grade],
            "horizon_low": round(self.horizon_low, 3),
            "horizon_high": round(self.horizon_high, 3),
            "haze_color": [round(c, 3) for c in self.haze_color],
            "haze_scale": [round(c, 3) for c in self.haze_scale],
            "fog_distance": round(self.fog_distance, 1),
            "shadows": bool(self.shadows),
            "shadow_range": round(self.shadow_range, 1),
            "shadow_bias": round(self.shadow_bias, 4),
            "shadow_darkness": round(self.shadow_darkness, 3),
            "rain_intensity": round(self.rain_intensity, 3),
            "wet_reflection": round(self.wet_reflection, 3),
            "has_lightning": bool(self.has_lightning),
            "valley_fog_altitude": round(self.valley_fog_altitude, 1),
            "valley_fog_density": round(self.valley_fog_density, 3),
            "dust_intensity": round(self.dust_intensity, 3),
            "smog_intensity": round(self.smog_intensity, 3),
            "heat_shimmer": round(self.heat_shimmer, 3),
            "volcanic_ash": round(self.volcanic_ash, 3),
            "lava_glow": round(self.lava_glow, 3),
            "is_interior": bool(self.is_interior),
            "env_lights": self.env_lights,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvironmentConfig":
        return cls(
            preset_name=data.get("preset_name", "sunset"),
            time_of_day=float(data.get("time_of_day", 18.0)),
            azimuth=float(data.get("azimuth", 235.0)),
            elevation=float(data.get("elevation", 28.0)),
            sun_color=list(data.get("sun_color", [1.0, 0.75, 0.5])),
            sun_strength=float(data.get("sun_strength", data.get("strength", 0.90))),
            ambient_color=list(data.get("ambient_color", [0.38, 0.32, 0.45])),
            ambient_strength=float(data.get("ambient_strength", data.get("ambient", 0.22))),
            night_world_gain=float(data.get("night_world_gain", 0.0)),
            sky_tint=list(data.get("sky_tint", [0.38, 0.28, 0.48])),
            sky_brightness=float(data.get("sky_brightness", 1.0)),
            sky_glow_color=list(data.get("sky_glow_color", [1.0, 0.55, 0.25])),
            sky_glow_strength=float(data.get("sky_glow_strength", 1.2)),
            sky_glow_focus=float(data.get("sky_glow_focus", 3.5)),
            sky_grade=list(data.get("sky_grade", [0.0, 0.0, 0.0])),
            horizon_low=float(data.get("horizon_low", 0.0)),
            horizon_high=float(data.get("horizon_high", 0.45)),
            haze_color=list(data.get("haze_color", [0.65, 0.45, 0.35])),
            haze_scale=list(data.get("haze_scale", [1.0, 1.0, 1.0])),
            fog_distance=float(data.get("fog_distance", 1200.0)),
            shadows=bool(data.get("shadows", True)),
            shadow_range=float(data.get("shadow_range", 400.0)),
            shadow_bias=float(data.get("shadow_bias", 0.005)),
            shadow_darkness=float(data.get("shadow_darkness", 0.75)),
            rain_intensity=float(data.get("rain_intensity", 0.0)),
            wet_reflection=float(data.get("wet_reflection", 0.0)),
            has_lightning=bool(data.get("has_lightning", False)),
            valley_fog_altitude=float(data.get("valley_fog_altitude", 0.0)),
            valley_fog_density=float(data.get("valley_fog_density", 0.0)),
            dust_intensity=float(data.get("dust_intensity", 0.0)),
            smog_intensity=float(data.get("smog_intensity", 0.0)),
            heat_shimmer=float(data.get("heat_shimmer", 0.0)),
            volcanic_ash=float(data.get("volcanic_ash", 0.0)),
            lava_glow=float(data.get("lava_glow", 0.0)),
            is_interior=bool(data.get("is_interior", False)),
            env_lights=list(data.get("env_lights", [])),
        )


def solve_time_of_day(hour: float, base_azimuth: float = 180.0) -> EnvironmentConfig:
    """Compute realistic sun position, sky temperature, and ambient bounce from 24-hr time."""
    h = hour % 24.0

    # Solar calculation:
    # 06:00 is sunrise (elevation 0 deg, east azimuth 90)
    # 12:00 is solar noon (elevation 75 deg, south azimuth 180)
    # 18:00 is sunset (elevation 0 deg, west azimuth 270)
    # 00:00 is midnight (elevation -60 deg, north azimuth 0)
    sun_progress = (h - 6.0) / 12.0  # 0.0 at dawn, 0.5 at noon, 1.0 at dusk

    if 0.0 <= sun_progress <= 1.0:
        # Daytime solar arc
        el = math.sin(sun_progress * math.pi) * 75.0
        az = 90.0 + sun_progress * 180.0
    else:
        # Nighttime moon position
        night_progress = (h - 18.0) % 24.0 / 12.0
        el = math.sin(night_progress * math.pi) * 35.0  # Moon reaches 35 deg
        az = (270.0 + night_progress * 180.0) % 360.0

    cfg = EnvironmentConfig(time_of_day=h, azimuth=az, elevation=max(1.0, el))

    if 5.0 <= h < 7.0:
        # Dawn / Twilight
        t = (h - 5.0) / 2.0
        cfg.preset_name = "dawn"
        cfg.sun_strength = 0.4 + t * 0.4
        cfg.sun_color = [1.0, 0.55 + t * 0.25, 0.3 + t * 0.3]
        cfg.ambient_strength = 0.15 + t * 0.10
        cfg.ambient_color = [0.45, 0.35, 0.60]
        cfg.sky_tint = [0.40, 0.30, 0.55]
        cfg.sky_glow_color = [1.0, 0.45, 0.20]
        cfg.fog_distance = 1100.0
    elif 7.0 <= h < 11.0:
        # Morning
        cfg.preset_name = "morning"
        cfg.sun_strength = 0.95
        cfg.sun_color = [1.0, 0.92, 0.80]
        cfg.ambient_strength = 0.28
        cfg.ambient_color = [0.40, 0.50, 0.65]
        cfg.sky_tint = [0.42, 0.62, 0.90]
        cfg.fog_distance = 1800.0
    elif 11.0 <= h < 15.0:
        # High Noon
        cfg.preset_name = "noon"
        cfg.sun_strength = 1.15
        cfg.sun_color = [1.0, 1.0, 0.95]
        cfg.ambient_strength = 0.35
        cfg.ambient_color = [0.45, 0.55, 0.70]
        cfg.sky_tint = [0.45, 0.65, 0.95]
        cfg.fog_distance = 2500.0
    elif 15.0 <= h < 17.5:
        # Afternoon
        cfg.preset_name = "afternoon"
        cfg.sun_strength = 1.0
        cfg.sun_color = [1.0, 0.90, 0.75]
        cfg.ambient_strength = 0.30
        cfg.ambient_color = [0.42, 0.48, 0.62]
        cfg.sky_tint = [0.40, 0.58, 0.88]
        cfg.fog_distance = 1900.0
    elif 17.5 <= h < 19.5:
        # Golden Hour / Sunset
        t = (h - 17.5) / 2.0
        cfg.preset_name = "sunset"
        cfg.sun_strength = 1.0 - t * 0.3
        cfg.sun_color = [1.0, 0.70 - t * 0.3, 0.40 - t * 0.2]
        cfg.ambient_strength = 0.22 - t * 0.05
        cfg.ambient_color = [0.45, 0.30, 0.45]
        cfg.sky_tint = [0.38, 0.28, 0.48]
        cfg.sky_glow_color = [1.0, 0.50, 0.20]
        cfg.fog_distance = 1200.0
    elif 19.5 <= h < 21.5:
        # Dusk / Twilight
        cfg.preset_name = "dusk"
        cfg.sun_strength = 0.25
        cfg.sun_color = [0.65, 0.35, 0.45]
        cfg.ambient_strength = 0.12
        cfg.ambient_color = [0.22, 0.22, 0.38]
        cfg.sky_tint = [0.18, 0.16, 0.30]
        cfg.night_world_gain = 0.35
        cfg.fog_distance = 900.0
    else:
        # Night / Midnight
        cfg.preset_name = "night"
        cfg.sun_strength = 0.18  # Soft moon light
        cfg.sun_color = [0.55, 0.65, 0.85]
        cfg.ambient_strength = 0.08
        cfg.ambient_color = [0.12, 0.15, 0.25]
        cfg.sky_tint = [0.08, 0.10, 0.18]
        cfg.night_world_gain = 0.70
        cfg.fog_distance = 800.0

    return cfg


def get_environment_preset(name: str) -> EnvironmentConfig:
    """Return configured atmosphere & weather for a named preset."""
    n = name.lower().strip()
    if n == "dawn":
        return solve_time_of_day(6.0)
    elif n == "morning":
        return solve_time_of_day(9.0)
    elif n == "noon":
        return solve_time_of_day(12.5)
    elif n == "afternoon":
        return solve_time_of_day(15.5)
    elif n in ("sunset", "golden_hour"):
        return solve_time_of_day(18.2)
    elif n == "dusk":
        return solve_time_of_day(20.0)
    elif n == "night":
        return solve_time_of_day(23.5)
    elif n in ("pitch_black", "stealth"):
        cfg = solve_time_of_day(1.0)
        cfg.preset_name = "pitch_black"
        cfg.sun_strength = 0.04
        cfg.ambient_strength = 0.03
        cfg.night_world_gain = 0.95
        cfg.sky_tint = [0.03, 0.04, 0.07]
        cfg.fog_distance = 500.0
        return cfg
    elif n in ("rain", "storm", "thunderstorm"):
        cfg = solve_time_of_day(14.0)
        cfg.preset_name = "storm"
        cfg.sun_strength = 0.45
        cfg.sun_color = [0.75, 0.80, 0.85]
        cfg.ambient_strength = 0.25
        cfg.ambient_color = [0.35, 0.40, 0.45]
        cfg.sky_tint = [0.25, 0.30, 0.38]
        cfg.fog_distance = 700.0
        cfg.rain_intensity = 0.85
        cfg.wet_reflection = 0.90
        cfg.has_lightning = True
        return cfg
    elif n in ("dust", "sandstorm"):
        cfg = solve_time_of_day(13.0)
        cfg.preset_name = "dust"
        cfg.sun_strength = 0.55
        cfg.sun_color = [1.0, 0.85, 0.60]
        cfg.ambient_strength = 0.35
        cfg.ambient_color = [0.65, 0.50, 0.35]
        cfg.sky_tint = [0.60, 0.48, 0.32]
        cfg.fog_distance = 450.0
        cfg.dust_intensity = 0.80
        cfg.heat_shimmer = 0.50
        return cfg
    elif n in ("smog", "industrial"):
        cfg = solve_time_of_day(11.0)
        cfg.preset_name = "smog"
        cfg.sun_strength = 0.50
        cfg.sun_color = [0.85, 0.80, 0.65]
        cfg.ambient_strength = 0.28
        cfg.ambient_color = [0.42, 0.45, 0.38]
        cfg.sky_tint = [0.35, 0.38, 0.32]
        cfg.fog_distance = 600.0
        cfg.smog_intensity = 0.75
        cfg.wet_reflection = 0.40
        return cfg
    elif n in ("volcanic", "caldera"):
        cfg = solve_time_of_day(19.0)
        cfg.preset_name = "volcanic"
        cfg.sun_strength = 0.40
        cfg.sun_color = [1.0, 0.50, 0.25]
        cfg.ambient_strength = 0.20
        cfg.ambient_color = [0.35, 0.22, 0.20]
        cfg.sky_tint = [0.22, 0.15, 0.15]
        cfg.fog_distance = 650.0
        cfg.volcanic_ash = 0.70
        cfg.lava_glow = 0.85
        return cfg
    elif n in ("interior", "bunker", "sealed"):
        cfg = EnvironmentConfig(preset_name="interior", is_interior=True)
        cfg.sun_strength = 0.0
        cfg.ambient_strength = 0.15
        cfg.ambient_color = [0.30, 0.32, 0.35]
        cfg.sky_tint = [0.0, 0.0, 0.0]
        cfg.fog_distance = 300.0
        cfg.horizon_low = 0.0
        cfg.horizon_high = 0.0
        cfg.rain_intensity = 0.0
        cfg.has_lightning = False
        return cfg
    else:
        return solve_time_of_day(18.0)


def encode_mw34env1(mission_ident: str, env: EnvironmentConfig) -> bytes:
    """Encode an EnvironmentConfig into the byte-exact native MW34ENV1 wire format."""
    ident_ascii = mission_ident.strip().lower().encode("ascii")
    if not (1 <= len(ident_ascii) <= 16):
        raise ValueError(f"Mission identifier must be 1-16 ASCII bytes: {mission_ident}")

    # Build binary stream
    buf = bytearray(b"MW34ENV1")
    buf += struct.pack("<I", 1)  # 1 mission entry

    # Mission ID
    buf += struct.pack("<I", len(ident_ascii))
    buf += ident_ascii

    # 33 Bounded Fields
    raw_dict = {
        "azimuth": _clamp(env.azimuth, -360.0, 360.0),
        "elevation": _clamp(env.elevation, 0.0, 90.0),
        "sun_color": [_clamp(c, 0.0, 4.0) for c in env.sun_color],
        "sun_strength": _clamp(env.sun_strength, 0.0, 4.0),
        "ambient_color": [_clamp(c, 0.0, 4.0) for c in env.ambient_color],
        "ambient_strength": _clamp(env.ambient_strength, 0.0, 2.0),
        "night_world_gain": _clamp(env.night_world_gain, 0.0, 1.0),
        "sky_tint": [_clamp(c, 0.0, 4.0) for c in env.sky_tint],
        "sky_brightness": _clamp(env.sky_brightness, 0.0, 4.0),
        "sky_glow_color": [_clamp(c, 0.0, 4.0) for c in env.sky_glow_color],
        "sky_glow_strength": _clamp(env.sky_glow_strength, 0.0, 4.0),
        "sky_glow_focus": _clamp(env.sky_glow_focus, 0.0, 20.0),
        "sky_grade": [_clamp(c, 0.0, 1.0) for c in env.sky_grade],
        "horizon_low": _clamp(env.horizon_low, 0.0, 0.9),
        "horizon_high": _clamp(env.horizon_high, 0.0, 1.0),
        "haze_color": [_clamp(c, 0.0, 1.0) for c in env.haze_color],
        "haze_scale": [_clamp(c, 0.0, 4.0) for c in env.haze_scale],
        "fog_distance": _clamp(env.fog_distance, 0.0, 10000.0),
        "shadows": bool(env.shadows),
        "shadow_range": _clamp(env.shadow_range, 0.0, 10000.0),
        "shadow_bias": _clamp(env.shadow_bias, 0.0, 10.0),
        "shadow_darkness": _clamp(env.shadow_darkness, 0.0, 1.0),
        "rain_intensity": _clamp(env.rain_intensity, 0.0, 1.0),
        "wet_reflection": _clamp(env.wet_reflection, 0.0, 1.0),
        "has_lightning": bool(env.has_lightning),
        "valley_fog_altitude": _clamp(env.valley_fog_altitude, -10000.0, 10000.0),
        "valley_fog_density": _clamp(env.valley_fog_density, 0.0, 4.0),
        "dust_intensity": _clamp(env.dust_intensity, 0.0, 1.0),
        "smog_intensity": _clamp(env.smog_intensity, 0.0, 1.0),
        "heat_shimmer": _clamp(env.heat_shimmer, 0.0, 1.0),
        "volcanic_ash": _clamp(env.volcanic_ash, 0.0, 1.0),
        "lava_glow": _clamp(env.lava_glow, 0.0, 1.0),
        "is_interior": bool(env.is_interior),
    }

    # Ensure horizon interval is valid
    if raw_dict["horizon_low"] >= raw_dict["horizon_high"] and not (
        raw_dict["is_interior"] and raw_dict["horizon_low"] == raw_dict["horizon_high"] == 0.0
    ):
        raw_dict["horizon_high"] = min(1.0, raw_dict["horizon_low"] + 0.1)

    for name, count, low, high in ENV_FIELDS:
        val = raw_dict[name]
        if count == 0:
            buf += struct.pack("<I", 1 if val else 0)
        elif count == 1:
            buf += struct.pack("<f", float(val))
        else:
            buf += struct.pack("<" + "f" * count, *[float(x) for x in val])

    # Environment lights (0 by default)
    buf += struct.pack("<I", len(env.env_lights))
    for light in env.env_lights:
        for vec in light:
            buf += struct.pack("<4f", *vec)

    return bytes(buf)
