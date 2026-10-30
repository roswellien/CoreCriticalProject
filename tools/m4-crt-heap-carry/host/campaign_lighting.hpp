#pragma once
#include "fixture_lighting.hpp"
#include "mission_environment_pack.hpp"
#include "campaign_environment_policy.hpp"
#include <cstdlib>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>
#include <cstdio>

namespace mw34::campaign {

struct EnvLight {
    std::array<float,4> start{}; // xyz position, w radius
    std::array<float,4> end{};   // xyz direction/end, w unused
    std::array<float,4> color{}; // rgb linear color, w intensity
};

struct MissionEnvironment {
    const char* id;
    unsigned operation;
    unsigned mission;
    const char* name;
    const char* time_of_day;
    const char* weather_summary;

    // Sun / Moon Direction & Lighting
    float azimuth;
    float elevation;
    std::array<float,3> sun_color;
    float sun_strength;
    std::array<float,3> ambient_color;
    float ambient_strength;
    float night_world_gain;

    // Sky & Horizon
    std::array<float,3> sky_tint;
    float sky_brightness;
    std::array<float,3> sky_glow_color;
    float sky_glow_strength;
    float sky_glow_focus;
    std::array<float,3> sky_grade; // anti_brightness, anti_saturation, anti_haze
    float horizon_low;
    float horizon_high;

    // Haze & Distance Fog
    std::array<float,3> haze_color;
    std::array<float,3> haze_scale;
    float fog_distance;

    // Shadows
    bool shadows;
    float shadow_range;
    float shadow_bias;
    float shadow_darkness;

    // Weather Effects
    float rain_intensity;        // 0..1 (0.35 drizzle, 0.95 heavy downpour, 0.55 acid rain)
    float wet_reflection;        // 0..1 (sheen & wet specular reflections)
    bool has_lightning;          // Periodic lightning for outdoor storm missions
    float valley_fog_altitude;   // low-altitude fog base height (c1m4, c4m2, c3m5)
    float valley_fog_density;    // low-altitude fog density multiplier
    float dust_intensity;        // 0..1 (dust storm / particulate haze)
    float smog_intensity;        // 0..1 (industrial smog / heavy pollution)
    float heat_shimmer;          // 0..1 (mirage / rippling horizon)
    float volcanic_ash;          // 0..1 (ash canopy / soot)
    float lava_glow;             // 0..1 (underworld upward radiant orange light)
    bool is_interior;            // Sealed underground missions (c2m2, c2m4, c3m5)

    // Environmental light emitters
    std::vector<EnvLight> env_lights;
};

inline const std::vector<MissionEnvironment>& builtin_mission_database() {
    static const std::vector<MissionEnvironment> db = {
        // =========================================================================
        // Operation 1 — The Beachhead (Tropical/Coastal Basin)
        // =========================================================================
        {
            "c1m1", 1, 1, "Dropzone", "Dusk (Late Twilight)", "Clear but humid",
            245.0f, 7.0f,
            {1.0f, 0.45f, 0.20f}, 1.40f,
            {0.42f, 0.32f, 0.55f}, 0.25f,
            1.0f,
            {0.65f, 0.38f, 0.60f}, 0.75f,
            {1.0f, 0.50f, 0.20f}, 0.90f, 2.5f,
            {0.55f, 0.45f, 0.65f},
            0.02f, 0.25f,
            {0.28f, 0.18f, 0.25f}, {1.0f, 0.85f, 0.75f}, 1100.0f,
            true, 300.0f, 0.04f, 1.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, false,
            {}
        },
        {
            "c1m2", 1, 2, "Beachhead", "Nightfall / Early Night", "Light coastal drizzle",
            210.0f, 25.0f,
            {0.35f, 0.45f, 0.65f}, 0.28f,
            {0.18f, 0.22f, 0.32f}, 0.14f,
            0.24f,
            {0.08f, 0.12f, 0.22f}, 0.20f,
            {0.30f, 0.40f, 0.60f}, 0.10f, 1.5f,
            {0.70f, 0.60f, 0.80f},
            0.01f, 0.20f,
            {0.02f, 0.03f, 0.05f}, {0.35f, 0.45f, 0.65f}, 1100.0f,
            false, 200.0f, 0.05f, 0.8f,
            0.35f, 0.50f, false, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, false,
            {
                // Burning drop-pod wreckage (warm orange flickers)
                {{-80.0f, 12.0f, -450.0f, 75.0f}, {0,0,0,0}, {1.0f, 0.45f, 0.10f, 1.4f}},
                {{120.0f, 15.0f, -600.0f, 90.0f}, {0,0,0,0}, {1.0f, 0.50f, 0.12f, 1.6f}},
                // Base perimeter searchlights (cool beams)
                {{-300.0f, 28.0f, -950.0f, 110.0f}, {0,0,0,0}, {0.75f, 0.85f, 1.0f, 1.8f}},
                {{350.0f, 30.0f, -1050.0f, 120.0f}, {0,0,0,0}, {0.80f, 0.90f, 1.0f, 1.9f}}
            }
        },
        {
            "c1m3", 1, 3, "Bridgehead", "Dead of Night (Midnight)", "Heavy tropical downpour & lightning",
            180.0f, 40.0f,
            {0.20f, 0.28f, 0.45f}, 0.18f,
            {0.12f, 0.15f, 0.22f}, 0.10f,
            0.20f,
            {0.05f, 0.06f, 0.10f}, 0.12f,
            {0.20f, 0.30f, 0.50f}, 0.05f, 1.0f,
            {0.80f, 0.70f, 0.90f},
            0.01f, 0.18f,
            {0.015f, 0.02f, 0.03f}, {0.20f, 0.28f, 0.45f}, 950.0f,
            false, 200.0f, 0.05f, 0.8f,
            0.95f, 0.90f, true, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, false,
            {}
        },
        {
            "c1m4", 1, 4, "Hydro-Plant", "Dawn (Early Morning)", "Low-lying valley fog",
            65.0f, 5.0f,
            {0.92f, 0.78f, 0.68f}, 1.20f,
            {0.55f, 0.62f, 0.75f}, 0.32f,
            1.0f,
            {0.58f, 0.65f, 0.78f}, 0.85f,
            {1.0f, 0.80f, 0.60f}, 0.80f, 2.0f,
            {0.65f, 0.55f, 0.70f},
            0.03f, 0.30f,
            {0.52f, 0.58f, 0.68f}, {0.90f, 0.95f, 1.05f}, 1100.0f,
            true, 250.0f, 0.04f, 1.0f,
            0.0f, 0.15f, false, 45.0f, 0.040f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, false,
            {}
        },

        // =========================================================================
        // Operation 2 — The Industrial Sector (High-Plains Badlands)
        // =========================================================================
        {
            "c2m1", 2, 1, "Trainyard", "Early Morning", "High winds & localized windblown dust",
            80.0f, 18.0f,
            {1.0f, 0.88f, 0.65f}, 1.35f,
            {0.70f, 0.72f, 0.80f}, 0.28f,
            1.0f,
            {0.75f, 0.82f, 0.95f}, 1.05f,
            {1.0f, 0.90f, 0.70f}, 0.70f, 2.0f,
            {0.75f, 0.80f, 0.85f},
            0.03f, 0.28f,
            {0.55f, 0.52f, 0.45f}, {0.95f, 0.90f, 0.85f}, 1100.0f,
            true, 220.0f, 0.04f, 1.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.25f, 0.0f, 0.0f, 0.0f, 0.0f, false,
            {}
        },
        {
            "c2m2", 2, 2, "Industrial Complex", "Indoor / Sealed Environment", "Underground industrial lighting",
            0.0f, 90.0f,
            {0.0f, 0.0f, 0.0f}, 0.0f,       // No natural sunlight underground
            {0.65f, 0.62f, 0.52f}, 0.18f,   // Reduce ambient fill by 40 percent
            0.0f,
            {0.0f, 0.0f, 0.0f}, 0.0f,       // No outdoor sky or horizon glow
            {0.0f, 0.0f, 0.0f}, 0.0f, 1.8f,
            {1.0f, 1.0f, 1.0f},
            0.05f, 0.35f,
            {0.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}, 1000.0f,
            false, 180.0f, 0.05f, 0.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, true,
            {}
        },
        {
            "c2m3", 2, 3, "Mining Facility", "Early Afternoon", "Intense dust storm",
            220.0f, 42.0f,
            {0.98f, 0.82f, 0.58f}, 1.15f,
            {0.58f, 0.46f, 0.32f}, 0.24f,
            1.0f,
            {0.62f, 0.48f, 0.30f}, 0.70f,
            {0.90f, 0.70f, 0.45f}, 0.60f, 1.6f,
            {0.50f, 0.40f, 0.50f},
            0.04f, 0.32f,
            {0.52f, 0.38f, 0.22f}, {0.90f, 0.75f, 0.55f}, 850.0f,
            true, 200.0f, 0.05f, 1.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.85f, 0.20f, 0.0f, 0.0f, 0.0f, false,
            {}
        },
        {
            "c2m4", 2, 4, "Power Plant", "Indoor / Sealed Environment", "Underground industrial lighting",
            0.0f, 90.0f,
            {0.0f, 0.0f, 0.0f}, 0.0f,       // No natural sunlight underground
            {0.38f, 0.45f, 0.35f}, 0.40f, // User-selected per-map ambient level
            0.0f,
            {0.0f, 0.0f, 0.0f}, 0.0f,       // No outdoor sky or horizon glow
            {0.0f, 0.0f, 0.0f}, 0.0f, 2.2f,
            {1.0f, 1.0f, 1.0f},
            0.03f, 0.28f,
            {0.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}, 1050.0f,
            false, 220.0f, 0.04f, 0.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, true,
            {}
        },

        // =========================================================================
        // Operation 3 — The Desert Plain (Arid Canyonlands)
        // =========================================================================
        {
            "c3m1", 3, 1, "Canyon Approach", "High Noon", "Extreme heat shimmer & mirage",
            175.0f, 82.0f,
            {1.05f, 0.98f, 0.92f}, 1.70f,
            {0.85f, 0.68f, 0.58f}, 0.36f,
            1.0f,
            {0.85f, 0.90f, 0.98f}, 1.20f,
            {1.0f, 0.95f, 0.85f}, 0.30f, 2.0f,
            {0.85f, 0.85f, 0.85f},
            0.05f, 0.35f,
            {0.65f, 0.55f, 0.48f}, {1.05f, 0.95f, 0.90f}, 1100.0f,
            true, 240.0f, 0.04f, 1.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.10f, 0.0f, 0.80f, 0.0f, 0.0f, false,
            {}
        },
        {
            "c3m2", 3, 2, "Outpost", "Mid-Afternoon", "Canyon wind gusts & fine sand",
            225.0f, 48.0f,
            {1.0f, 0.88f, 0.72f}, 1.40f,
            {0.68f, 0.55f, 0.45f}, 0.28f,
            1.0f,
            {0.80f, 0.82f, 0.88f}, 1.00f,
            {0.95f, 0.85f, 0.65f}, 0.50f, 1.8f,
            {0.75f, 0.70f, 0.80f},
            0.04f, 0.30f,
            {0.58f, 0.48f, 0.38f}, {0.95f, 0.88f, 0.80f}, 1100.0f,
            true, 220.0f, 0.04f, 1.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.45f, 0.0f, 0.20f, 0.0f, 0.0f, false,
            {}
        },
        {
            "c3m3", 3, 3, "Fuel Depot", "Late Afternoon", "Fiery crimson sky & heavy unmoving dust",
            260.0f, 12.0f,
            {1.0f, 0.32f, 0.12f}, 1.50f,
            {0.58f, 0.32f, 0.38f}, 0.30f,
            1.0f,
            {0.85f, 0.28f, 0.22f}, 0.90f,
            {1.0f, 0.40f, 0.15f}, 1.20f, 2.5f,
            {0.55f, 0.40f, 0.60f},
            0.03f, 0.26f,
            {0.42f, 0.25f, 0.22f}, {0.90f, 0.70f, 0.65f}, 1050.0f,
            true, 250.0f, 0.04f, 1.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.50f, 0.0f, 0.15f, 0.0f, 0.0f, false,
            {}
        },
        {
            "c3m4", 3, 4, "Supply Depot", "Dusk", "Deep orange/purple twilight, sharp contrast",
            275.0f, 3.0f,
            {0.95f, 0.42f, 0.18f}, 0.90f,
            {0.32f, 0.25f, 0.42f}, 0.20f,
            1.0f,
            {0.45f, 0.28f, 0.52f}, 0.60f,
            {0.95f, 0.45f, 0.20f}, 0.80f, 2.2f,
            {0.55f, 0.45f, 0.65f},
            0.02f, 0.22f,
            {0.18f, 0.14f, 0.24f}, {0.70f, 0.65f, 0.85f}, 1100.0f,
            true, 280.0f, 0.04f, 1.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, false,
            {}
        },
        {
            "c3m5", 3, 5, "Underground Hangar", "Indoor / Sealed Environment", "Subterranean mist & emergency lighting",
            0.0f, 90.0f,
            {0.0f, 0.0f, 0.0f}, 0.0f,       // No natural sunlight
            {0.12f, 0.14f, 0.16f}, 0.18f,   // Dim industrial ambient
            0.30f,
            {0.0f, 0.0f, 0.0f}, 0.0f,       // No sky
            {0.0f, 0.0f, 0.0f}, 0.0f, 1.0f,
            {1.0f, 1.0f, 1.0f},
            0.0f, 0.0f,
            {0.08f, 0.10f, 0.12f}, {0.2f, 0.2f, 0.2f}, 900.0f,
            false, 100.0f, 0.05f, 0.0f,
            0.0f, 0.10f, false, 80.0f, 0.035f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, true,
            {
                // Emergency red beacons
                {{-50.0f, 18.0f, -200.0f, 50.0f}, {0,0,0,0}, {1.0f, 0.08f, 0.03f, 1.5f}},
                {{60.0f, 18.0f, -320.0f, 50.0f}, {0,0,0,0}, {1.0f, 0.08f, 0.03f, 1.5f}},
                // Mercury-vapor green industrial fixtures
                {{0.0f, 25.0f, -120.0f, 70.0f}, {0,0,0,0}, {0.20f, 0.90f, 0.55f, 1.2f}},
                {{-80.0f, 25.0f, -280.0f, 70.0f}, {0,0,0,0}, {0.20f, 0.90f, 0.55f, 1.2f}}
            }
        },
        {
            "c3m6", 3, 6, "Comm Array", "Nightfall", "Clear starlit freezing desert night",
            140.0f, 38.0f,
            {0.48f, 0.58f, 0.85f}, 0.42f,   // Strong lunar light from Tranquil's moons
            {0.22f, 0.26f, 0.38f}, 0.20f,
            0.26f,
            {0.12f, 0.18f, 0.32f}, 0.35f,
            {0.45f, 0.55f, 0.80f}, 0.25f, 1.8f,
            {0.80f, 0.75f, 0.90f},
            0.01f, 0.18f,
            {0.025f, 0.035f, 0.06f}, {0.45f, 0.55f, 0.80f}, 1100.0f,
            true, 220.0f, 0.04f, 0.8f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, false,
            {}
        },

        // =========================================================================
        // Operation 4 — The Core (Volcanic Caldera & City Center)
        // =========================================================================
        {
            "c4m1", 4, 1, "Caldera", "Midnight (Volcanic Glow)", "Ash fall & glowing lava illumination",
            180.0f, 20.0f,
            {0.10f, 0.10f, 0.10f}, 0.05f,   // Blotted out sky
            {0.35f, 0.14f, 0.05f}, 0.30f,   // Warm orange/red radiant underworld light
            0.22f,
            {0.08f, 0.06f, 0.06f}, 0.08f,
            {0.80f, 0.30f, 0.10f}, 0.15f, 1.2f,
            {0.60f, 0.40f, 0.70f},
            0.02f, 0.20f,
            {0.14f, 0.08f, 0.05f}, {0.40f, 0.25f, 0.15f}, 1000.0f,
            false, 200.0f, 0.05f, 0.6f,
            0.0f, 0.15f, false, 0.0f, 0.0f, 0.35f, 0.0f, 0.0f, 0.75f, 0.85f, false,
            {
                // Lava pool / crater glow hot-spots
                {{-150.0f, -10.0f, -300.0f, 120.0f}, {0,0,0,0}, {1.0f, 0.35f, 0.05f, 2.2f}},
                {{180.0f, -12.0f, -450.0f, 140.0f}, {0,0,0,0}, {1.0f, 0.38f, 0.06f, 2.4f}},
                {{0.0f, -15.0f, -600.0f, 160.0f}, {0,0,0,0}, {1.0f, 0.32f, 0.04f, 2.5f}}
            }
        },
        {
            "c4m2", 4, 2, "Fortress", "Pre-Dawn (Deep Night)", "Acid rain & caustic sulfuric mist",
            75.0f, 12.0f,
            {0.25f, 0.32f, 0.45f}, 0.20f,   // Darkest part before sun breaks
            {0.15f, 0.18f, 0.25f}, 0.15f,
            0.22f,
            {0.08f, 0.10f, 0.18f}, 0.18f,
            {0.25f, 0.35f, 0.50f}, 0.10f, 1.5f,
            {0.70f, 0.60f, 0.80f},
            0.02f, 0.22f,
            {0.08f, 0.12f, 0.10f}, {0.35f, 0.45f, 0.40f}, 900.0f,
            false, 200.0f, 0.05f, 0.8f,
            0.55f, 0.65f, false, 55.0f, 0.035f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, false,
            {
                // Exterior base floodlights
                {{-220.0f, 35.0f, -700.0f, 95.0f}, {0,0,0,0}, {0.85f, 0.95f, 1.0f, 1.9f}},
                {{240.0f, 35.0f, -720.0f, 95.0f}, {0,0,0,0}, {0.85f, 0.95f, 1.0f, 1.9f}}
            }
        },
        {
            "c4m3", 4, 3, "City Streets", "First Light (False Dawn)", "Silver-blue skyline, urban dust clouds",
            82.0f, 2.0f,
            {0.65f, 0.75f, 0.95f}, 0.80f,   // Thin horizontal strip of silver-blue
            {0.28f, 0.32f, 0.42f}, 0.20f,   // Street level in deep shadow
            0.80f,
            {0.38f, 0.48f, 0.65f}, 0.55f,
            {0.60f, 0.75f, 0.95f}, 0.90f, 2.8f,
            {0.60f, 0.50f, 0.65f},
            0.02f, 0.22f,
            {0.18f, 0.20f, 0.28f}, {0.60f, 0.70f, 0.85f}, 1050.0f,
            true, 280.0f, 0.04f, 1.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.40f, 0.0f, 0.0f, 0.0f, 0.0f, false,
            {}
        },
        {
            "c4m4", 4, 4, "Starport", "Dawn", "Vibrant pink & gold sunrise, windy open tarmac",
            88.0f, 8.0f,
            {1.0f, 0.65f, 0.45f}, 1.35f,
            {0.65f, 0.45f, 0.55f}, 0.32f,
            1.0f,
            {0.85f, 0.52f, 0.62f}, 0.95f,
            {1.0f, 0.68f, 0.45f}, 1.10f, 2.2f,
            {0.65f, 0.60f, 0.75f},
            0.03f, 0.28f,
            {0.42f, 0.32f, 0.38f}, {0.95f, 0.80f, 0.85f}, 1100.0f,
            true, 250.0f, 0.04f, 1.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.15f, 0.0f, 0.0f, 0.0f, 0.0f, false,
            {}
        },
        {
            "c4m5", 4, 5, "Control Tower", "Morning Sunrise", "Intense blinding gold glare & rocket heat haze",
            95.0f, 14.0f,
            {1.0f, 0.82f, 0.45f}, 1.65f,   // Blinding gold glare into optical view
            {0.72f, 0.68f, 0.60f}, 0.35f,
            1.0f,
            {0.82f, 0.85f, 0.92f}, 1.15f,
            {1.0f, 0.85f, 0.45f}, 1.40f, 2.0f,
            {0.75f, 0.70f, 0.85f},
            0.04f, 0.30f,
            {0.55f, 0.48f, 0.38f}, {1.0f, 0.90f, 0.80f}, 1100.0f,
            true, 240.0f, 0.04f, 1.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.10f, 0.0f, 0.70f, 0.0f, 0.0f, false,
            {}
        },
        {
            "c4m6", 4, 6, "Final Confrontation", "Final Full Sunrise", "Triumphant brilliant sky-blue & crisp daylight",
            110.0f, 28.0f,
            {1.0f, 0.95f, 0.88f}, 1.45f,
            {0.78f, 0.82f, 0.92f}, 0.35f,
            1.0f,
            {0.65f, 0.78f, 0.98f}, 1.10f,
            {1.0f, 0.95f, 0.85f}, 0.60f, 2.0f,
            {0.85f, 0.85f, 0.95f},
            0.03f, 0.28f,
            {0.45f, 0.55f, 0.72f}, {1.0f, 1.0f, 1.0f}, 1100.0f,
            true, 220.0f, 0.04f, 1.0f,
            0.0f, 0.0f, false, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, false,
            {}
        }
    };
    return db;
}

inline const std::vector<MissionEnvironment>& mission_database() {
    static const auto database=[] {
        auto result=builtin_mission_database();
        if(const auto* path=std::getenv("MW34_MISSION_ENVIRONMENTS");path && *path) {
            const auto count=mw34::packs::load_mission_environments(path,result);
            std::fprintf(stderr,"Mission lighting pack: loaded %u verified mission environments\n",count);
        }
        return result;
    }();
    return database;
}

class CampaignManager {
public:
    static CampaignManager& instance() {
        static CampaignManager mgr;
        return mgr;
    }

    void observe_file(const std::string& path, bool successful_read = true) {
        if (!successful_read) return;
        if (path.empty()) return;

        // Convert path to lowercase for canonical matching
        std::string lower = path;
        for (char& c : lower) {
            if (c == '\\') c = '/';
            else c = (char)std::tolower((unsigned char)c);
        }

        // Check for non-campaign modes first (Training, Instant Action, Multiplayer)
        if (lower.find("/t1/readerm") != std::string::npos && lower.ends_with(".zbd")) {
            ++reader_epoch_;
            reset("t1");
            return;
        }
        if (lower.find("readeria") != std::string::npos) {
            ++reader_epoch_;
            reset("ia");
            return;
        }
        if (lower.find("readermp") != std::string::npos) {
            ++reader_epoch_;
            reset("mp");
            return;
        }

        // Check for Campaign Operation 1..4 mission reader files
        // Pattern: /c1/readerm1.zbd through /c4b/readerm6.zbd
        const char* const campaign_patterns[] = {
            "/c1/readerm1.zbd", "c1m1",
            "/c1/readerm2.zbd", "c1m2",
            "/c1/readerm3.zbd", "c1m3",
            "/c1/readerm4.zbd", "c1m4",

            "/c2/readerm1.zbd", "c2m1",
            "/c2/readerm2.zbd", "c2m2",
            "/c2/readerm3.zbd", "c2m3",
            "/c2/readerm4.zbd", "c2m4",

            "/c3/readerm1.zbd", "c3m1",
            "/c3/readerm2.zbd", "c3m2",
            "/c3/readerm3.zbd", "c3m3",
            "/c3/readerm4.zbd", "c3m4",
            "/c3/readerm5.zbd", "c3m5",
            "/c3/readerm6.zbd", "c3m6",

            "/c4/readerm1.zbd",  "c4m1",
            "/c4/readerm2.zbd",  "c4m2",
            "/c4/readerm3.zbd",  "c4m3",
            "/c4b/readerm4.zbd", "c4m4",
            "/c4b/readerm5.zbd", "c4m5",
            "/c4b/readerm6.zbd", "c4m6"
        };

        for (size_t i = 0; i < sizeof(campaign_patterns) / sizeof(campaign_patterns[0]); i += 2) {
            if (lower.ends_with(campaign_patterns[i])) {
                ++reader_epoch_;
                set_active_mission(campaign_patterns[i + 1]);
                return;
            }
        }

        // Save names are not mission identities. The actual reader load selects the environment.
    }

    void set_active_mission(const std::string& id) {
        for (const auto& env : mission_database()) {
            if (env.id == id) {
                current_env_ = &env;
                active_mission_id_ = id;
                campaign_active_ = true;
                pending_world_ = true;
                ++generation_;
                std::fprintf(stderr,"Campaign lighting: selected %s from successful mission-reader open\n",id.c_str());
                mw34::fixtures::FixtureManager::instance().clear();
                return;
            }
        }
    }

    void reset(const std::string& mode = {}) {
        if(campaign_active_ || active_mission_id_ != mode) ++generation_;
        campaign_active_=false;pending_world_=false;current_env_=nullptr;active_mission_id_=mode;
        mw34::fixtures::FixtureManager::instance().clear();
    }
    void frontend() { if(!pending_world_) reset(); }
    void enter_world() { pending_world_=false; }
    std::uint64_t generation() const { return generation_; }
    std::uint64_t reader_epoch() const { return reader_epoch_; }

    bool is_campaign_active() const {
        return campaign_active_ && current_env_ != nullptr;
    }

    const std::string& active_mission_id() const {
        return active_mission_id_;
    }

    const MissionEnvironment* active_environment() const {
        return is_campaign_active() ? current_env_ : nullptr;
    }

    const MissionEnvironment* find_environment(const std::string& id) const {
        for (const auto& env : mission_database()) {
            if (env.id == id) return &env;
        }
        return nullptr;
    }

    // Dynamic weather state for current frame
    struct DynamicWeatherState {
        float lightning_flash{0.0f}; // 0 = none, 1..2.5 during strike
        float rain_intensity{0.0f};
        float wet_reflection{0.0f};
        float valley_fog_altitude{0.0f};
        float valley_fog_density{0.0f};
        float dust_intensity{0.0f};
        float smog_intensity{0.0f};
        float heat_shimmer{0.0f};
        float volcanic_ash{0.0f};
        float lava_glow{0.0f};
        bool is_interior{false};
    };

    DynamicWeatherState evaluate_weather(double time_sec) const {
        DynamicWeatherState s;
        if (!is_campaign_active() || !current_env_) return s;

        s.rain_intensity = current_env_->rain_intensity;
        s.wet_reflection = current_env_->wet_reflection;
        s.valley_fog_altitude = current_env_->valley_fog_altitude;
        s.valley_fog_density = current_env_->valley_fog_density;
        s.dust_intensity = current_env_->dust_intensity;
        s.smog_intensity = current_env_->smog_intensity;
        s.heat_shimmer = current_env_->heat_shimmer;
        s.volcanic_ash = current_env_->volcanic_ash;
        s.lava_glow = current_env_->lava_glow;
        s.is_interior = current_env_->is_interior;

        // Sealed maps retain local dampness/vent mist, never outdoor weather.
        // Identity also protects these maps from older exterior-style packs.
        if (sealed_mission(current_env_->id) || current_env_->is_interior) {
            s.is_interior = true;
            s.rain_intensity = s.dust_intensity = s.smog_intensity = 0;
            s.heat_shimmer = s.volcanic_ash = s.lava_glow = 0;
            return s;
        }

        // Lightning simulation for stormy missions
        if (current_env_->has_lightning) {
            // Periodic flash cycle roughly every 7.3 seconds
            double cycle = std::fmod(time_sec, 7.3);
            if (cycle < 0.18) {
                // Main strike flash + rapid micro-flicker
                float progress = float(cycle / 0.18);
                float flicker = (std::sin(progress * 35.0f) * 0.5f + 0.5f);
                float envelope = std::exp(-progress * 4.0f);
                s.lightning_flash = envelope * (1.2f + 1.3f * flicker);
            } else if (cycle > 0.28 && cycle < 0.38) {
                // Secondary smaller strike echo
                float progress = float((cycle - 0.28) / 0.10);
                s.lightning_flash = std::exp(-progress * 5.0f) * 0.75f;
            }
        }

        return s;
    }

private:
    CampaignManager() = default;
    bool campaign_active_{false},pending_world_{false};
    std::uint64_t generation_{}, reader_epoch_{};
    std::string active_mission_id_{};
    const MissionEnvironment* current_env_{nullptr};
};

} // namespace mw34::campaign
