"""Batch compatible captured triangles before repeated scene preparation work."""
import argparse
from pathlib import Path


def apply(host):
    path = host / 'd3d_provider.inc'
    source = path.read_text()
    anchor = 'dev->commands.push_back(std::move(c));return done(DD_OK,n=="DrawPrimitive"?6:8);'
    replacement = '''{
    static const bool early=[] {
     const char* value=std::getenv("MW34_EARLY_TRIANGLE_COMMANDS");
     if(!value||!*value||!std::strcmp(value,"0"))return false;
     if(!std::strcmp(value,"1"))return true;
     throw std::runtime_error("MW34_EARLY_TRIANGLE_COMMANDS must be 0 or 1");
    }();
    if(early)mw34::submission::append_triangle_command(dev->commands,std::move(c));
    else dev->commands.push_back(std::move(c));
   }return done(DD_OK,n=="DrawPrimitive"?6:8);'''
    if replacement not in source:
        if source.count(anchor) != 1:
            raise ValueError('Original capture and suppression route changed')
        source = source.replace(anchor, replacement, 1)
    header = host / 'mfc_stage.hpp'
    text = header.read_text()
    include = '#include "vk_scene.hpp"'
    new_include = include + '\n#include "early_triangle_commands.hpp"'
    if new_include not in text:
        if text.count(include) != 1:
            raise ValueError('Native command header include changed')
        text = text.replace(include, new_include, 1)
    helper = Path(__file__).parent / 'native-overrides/early_triangle_commands.hpp'
    data = helper.read_bytes()
    if path.read_text() != source:
        path.write_text(source)
    if header.read_text() != text:
        header.write_text(text)
    destination = host / helper.name
    if not destination.exists() or destination.read_bytes() != data:
        destination.write_bytes(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
