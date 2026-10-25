"""Compose the audited campaign sky/interior policy after the C3M1 sky repair."""
from pathlib import Path
import argparse
import shutil

from apply_c3m1_day_sky import NEW_SKY, compile_fragments

SKY = '''            vec3 base;
            if(sun.skyTint.w>5.5){
                // An opaque particulate canopy, not water-bearing storm clouds.
                float height=pow(clamp(v.y,0.0,1.0),0.45);
                base=mix(haze, sun.skyTint.rgb*sun.skyGrade.x*0.55, height);
            }else if(sun.skyTint.w>1.5){
                float height=pow(clamp(v.y,0.0,1.0),0.45);
                if(sun.skyTint.w>3.5)
                    base=mix(vec3(0.12,0.16,0.26),vec3(0.015,0.025,0.055),height);
                else if(sun.skyTint.w>2.5)
                    base=mix(vec3(0.36,0.42,0.60),vec3(0.13,0.18,0.33),height);
                else
                    base=mix(vec3(0.58,0.74,0.91),vec3(0.18,0.43,0.72),height);
                base*=sun.skyTint.rgb*sun.skyGrade.x*mix(sun.skyGrade.y,1.0,pow(side,1.5));
            }else{
                vec3 legacy=operation(draw.mode.y).rgb*sun.skyTint.rgb*sun.skyGrade.x*mix(sun.skyGrade.y,1.0,pow(side,1.5));
                if(sun.detail.x>2.5)legacy*=cloudRelief(uv,v);
                base=legacy;
            }'''


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('Campaign policy anchor changed: ' + old[:90])
    return source.replace(old, new, 1)


def apply(host):
    maintained = Path(__file__).with_name('native-overrides')
    target = host / 'campaign_environment_policy.hpp'
    if target.resolve() != (maintained / target.name).resolve():
        shutil.copy2(maintained / target.name, target)
    path = host / 'campaign_lighting.hpp'
    source = path.read_text(encoding='utf-8')
    if '#include "campaign_environment_policy.hpp"' not in source:
        source = replace_once(source, '#include "mission_environment_pack.hpp"',
                              '#include "mission_environment_pack.hpp"\n#include "campaign_environment_policy.hpp"')
        source = replace_once(source, '        // Lightning simulation for stormy missions',
            '''        // Sealed maps retain local dampness/vent mist, never outdoor weather.
        // Identity also protects these maps from older exterior-style packs.
        if (sealed_mission(current_env_->id) || current_env_->is_interior) {
            s.is_interior = true;
            s.rain_intensity = s.dust_intensity = s.smog_intensity = 0;
            s.heat_shimmer = s.volcanic_ash = s.lava_glow = 0;
            return s;
        }

        // Lightning simulation for stormy missions''')
    path.write_text(source, encoding='utf-8', newline='\n')
    path = host / 'sun_lighting.hpp'
    source = path.read_text(encoding='utf-8')
    if 'campaign::SkySource sky_source' not in source:
        source = replace_once(source,
            'inline void apply_campaign_environment(Settings& s, const campaign::MissionEnvironment& env, double time_sec) {',
            '''inline void apply_campaign_environment(Settings& s, const campaign::MissionEnvironment& env, double time_sec) {
    const bool interior = campaign::sealed_mission(env.id) || env.is_interior;''')
        source = replace_once(source, 'const float minimum=env.is_interior?.04f:.085f;',
                              'const float minimum=interior?.04f:.085f;')
        source = replace_once(source, 'if (weather.lightning_flash > 0.01f)',
                              'if (!interior && weather.lightning_flash > 0.01f)')
        source = replace_once(source,
            '    bool clear_day_sky{}; // Authored sky source, independent of weather uniforms.',
            '    campaign::SkySource sky_source{campaign::SkySource::OriginalClouds};')
        source = replace_once(source, '    s.clear_day_sky = env.id && std::strcmp(env.id,"c3m1")==0;',
            '    s.sky_source = campaign::mission_sky_source(env.id, interior);')
        source = replace_once(source,
            'u.sky_tint={s.sky_tint[0],s.sky_tint[1],s.sky_tint[2],s.clear_day_sky?2.f:1.f};',
            'u.sky_tint={s.sky_tint[0],s.sky_tint[1],s.sky_tint[2],float(s.sky_source)};')
        source = replace_once(source, '    if (env.is_interior) {\n        s.night_world_gain = 0.0f;\n    }',
            '''    if (interior) {
        s.strength = s.glow_strength = s.sky_brightness = 0;
        s.color = s.sky_tint = s.glow_color = {0,0,0};
        s.shadows = false;
        s.night_world_gain = 0;
        s.rain_wetness = weather.wet_reflection; // Local damp surfaces may remain.
        s.dust_intensity = s.heat_shimmer = s.lava_glow = 0;
    }''')
    path.write_text(source, encoding='utf-8', newline='\n')
    path = host / 'sun_scene.frag'
    source = path.read_text(encoding='utf-8')
    if SKY not in source:
        source = replace_once(source, NEW_SKY, SKY)
        source = replace_once(source,
            '        vec3 v=skyRay();float side=skySide(v);vec3 haze=hazeColor(v),c=haze;',
            '''        // Sealed maps have no natural sky. This also avoids evaluating
        // the valid interior horizon interval [0,0] through smoothstep.
        if(sun.skyTint.w>4.5&&sun.skyTint.w<5.5){
            result=vec4(0.0,0.0,0.0,operation(draw.mode.z).a);return;
        }
        vec3 v=skyRay();float side=skySide(v);vec3 haze=hazeColor(v),c=haze;''')
    path.write_text(source, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    parser.add_argument('--compiler', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if bool(args.compiler) != bool(args.output):
        parser.error('Supply both compiler and output')
    host = args.host.resolve(strict=True)
    apply(host)
    if args.compiler:
        compile_fragments(host, args.compiler.resolve(strict=True), args.output)
