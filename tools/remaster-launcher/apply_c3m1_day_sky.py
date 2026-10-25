"""Select an authored clear sky for C3M1 without reusing its storm-cloud artwork."""
from pathlib import Path
import argparse,struct,subprocess

OLD_SKY='''            vec3 base=operation(draw.mode.y).rgb*sun.skyTint.rgb*sun.skyGrade.x*mix(sun.skyGrade.y,1.0,pow(side,1.5));
            if(sun.detail.x>2.5)base*=cloudRelief(uv,v);'''
NEW_SKY='''            vec3 base;
            if(sun.skyTint.w>1.5){
                // Mission-authored clear daylight. Direction-space colour is
                // continuous across dome triangles and does not retain the
                // legacy storm texture or its cloud-normal contrast.
                float height=pow(clamp(v.y,0.0,1.0),0.45);
                base=mix(vec3(0.58,0.74,0.91),vec3(0.18,0.43,0.72),height);
                base*=sun.skyTint.rgb*sun.skyGrade.x*mix(sun.skyGrade.y,1.0,pow(side,1.5));
            }else{
                vec3 legacy=operation(draw.mode.y).rgb*sun.skyTint.rgb*sun.skyGrade.x*mix(sun.skyGrade.y,1.0,pow(side,1.5));
                if(sun.detail.x>2.5)legacy*=cloudRelief(uv,v);
                base=legacy;
            }'''


def apply(host: Path):
    path=host/'sun_lighting.hpp';source=path.read_text(encoding='utf-8')
    if 'bool clear_day_sky{};' not in source:
        replacements=[
            ('    bool sky_shading{};',
             '    bool sky_shading{};\n    bool clear_day_sky{}; // Authored sky source, independent of weather uniforms.'),
            ('    s.sky_tint = env.sky_tint;',
             '    s.clear_day_sky = env.id && std::strcmp(env.id,"c3m1")==0;\n    s.sky_tint = env.sky_tint;'),
            ('u.sky_tint={s.sky_tint[0],s.sky_tint[1],s.sky_tint[2],1};',
             'u.sky_tint={s.sky_tint[0],s.sky_tint[1],s.sky_tint[2],s.clear_day_sky?2.f:1.f};')]
        for old,new in replacements:
            if source.count(old)!=1:raise ValueError('Sky settings/upload anchor changed: '+old)
            source=source.replace(old,new,1)
    elif 's.clear_day_sky = env.id && std::strcmp(env.id,"c3m1")==0;' not in source or 's.clear_day_sky?2.f:1.f' not in source:
        raise ValueError('Partial clear-day sky settings')
    path.write_text(source,encoding='utf-8',newline='\n')
    path=host/'sun_scene.frag';source=path.read_text(encoding='utf-8')
    if NEW_SKY not in source:
        if source.count(OLD_SKY)!=1:raise ValueError('Original sky colour/relief route changed')
        source=source.replace(OLD_SKY,NEW_SKY,1)
    path.write_text(source,encoding='utf-8',newline='\n')


def compile_fragments(host: Path,compiler: Path,output: Path):
    output.mkdir(exist_ok=False)
    # Compile from this exact composed host, retaining status-preview and other
    # shader repairs that may not yet be folded into the common source snapshot.
    for stem,effect in [('sun_scene',False),('effect_scene',True)]:
        binary=output/(stem+'.frag.spv')
        subprocess.run([str(compiler),'-V','--target-env','vulkan1.0',
                        *(['-DMW34_EFFECT_LIGHTING=1'] if effect else []),'-S','frag',
                        str(host/'sun_scene.frag'),'-o',str(binary)],check=True)
        data=binary.read_bytes();words=struct.unpack('<'+'I'*(len(data)//4),data)
        header='// Compiled from authored sun_scene.frag.\ninline constexpr std::uint32_t '+stem+'_frag_spv[]={\n'
        header+='\n'.join(' '+','.join(f'0x{x:08x}u' for x in words[i:i+8])+',' for i in range(0,len(words),8))+'\n};\n'
        (host/(stem+'_frag.h')).write_text(header,encoding='utf-8',newline='\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host',type=Path);parser.add_argument('--compiler',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args();host=args.host.resolve(strict=True);apply(host)
    if args.compiler or args.output:
        if not args.compiler or not args.output:parser.error('Supply both compiler and output')
        compile_fragments(host,args.compiler.resolve(strict=True),args.output)
