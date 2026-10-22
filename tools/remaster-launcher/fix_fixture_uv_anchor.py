"""Keep an emission island anchored to its authored UV center through camera clipping.

Updates only the UV fixture placement expression in an existing private host.
Does not build, launch, or publish it.
"""
from pathlib import Path
import argparse

OLD = 'if(area<=best||area<1e-10f)continue;best=area;position={};for(const auto&p:poly)for(unsigned j=0;j<3;++j)position[j]+=p.p[j]/float(poly.size());'
NEW = '''// The visible fragment centroid changes at the screen edge. Recover
                // the authored island center through the triangle's affine UV mapping
                // instead, including when that center is just outside the clipped
                // triangle. Otherwise one physical lamp drifts/duplicates in retention.
                if(area<=best||area<1e-10f)continue;
                const double bu=double(b.u)-a.u,bv=double(b.v)-a.v,cu=double(c.u)-a.u,cv=double(c.v)-a.v;
                const double determinant=bu*cv-bv*cu;
                if(!std::isfinite(determinant)||std::abs(determinant)<1e-12)continue;
                const double du=(double(rect[0])+rect[2])*.5-a.u,dv=(double(rect[1])+rect[3])*.5-a.v;
                const double wb=(du*cv-dv*cu)/determinant,wc=(bu*dv-bv*du)/determinant;
                Point anchor{};bool valid=true;
                for(unsigned j=0;j<3;++j){const double value=a.p[j]+wb*(double(b.p[j])-a.p[j])+wc*(double(c.p[j])-a.p[j]);
                    if(!std::isfinite(value)||std::abs(value)>1000000)valid=false;anchor[j]=float(value);}
                if(!valid)continue;best=area;position=anchor;'''

def apply(path):
    source=path.read_text()
    if NEW in source:
        return
    if source.count(OLD)!=1:
        raise SystemExit(f'Expected one UV fixture placement expression in {path}')
    path.write_text(source.replace(OLD,NEW))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host',type=Path)
    args=parser.parse_args()
    apply(args.host/'fixture_lighting.hpp')
