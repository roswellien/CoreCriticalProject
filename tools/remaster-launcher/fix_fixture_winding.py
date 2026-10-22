"""Correct physical fixture offsets for reversed original draw submissions.

The source-polygon path already uses original corner order. Only the fallback
that consumes submitted TL/GPU geometry needs its winding restored. Without
this correction a positive emitter offset goes into the mounting wall, which
then occludes the lamp in its own shadow map.
"""

from pathlib import Path
import argparse


def correct(text: str) -> str:
    boundary = "  const auto source=fixture_source(draw,*surface);"
    if text.count(boundary) != 1:
        raise ValueError("Expected one submitted-geometry fixture fallback")
    original, fallback = text.split(boundary)
    if "Restore source winding" in fallback:
        raise ValueError("Fixture winding correction already applied")
    polygon = "  if(fixture->emission_regions.empty())manager.observe_polygon(*fixture,fix_pts,host.frames,source);"
    regions = "   manager.observe_regions(*fixture,triangles,host.frames,source);"
    if fallback.count(polygon) != 1 or fallback.count(regions) != 1:
        raise ValueError("Unsupported fixture fallback layout")
    fallback = fallback.replace(
        polygon,
        "  // Restore source winding: original TL/GPU submissions reverse the\n"
        "  // polygon corners. A positive offset must point out of the wall.\n"
        "  std::reverse(fix_pts.begin(),fix_pts.end());\n" + polygon,
    ).replace(
        regions,
        "   for(size_t at=0;at+2<triangles.size();at+=3)std::swap(triangles[at+1],triangles[at+2]);\n"
        + regions,
    )
    return original + boundary + fallback


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=Path)
    args = parser.parse_args()
    args.stage.write_text(correct(args.stage.read_text(encoding="utf-8")), encoding="utf-8")
