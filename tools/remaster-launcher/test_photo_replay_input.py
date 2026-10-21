"""Compile the actual input filters with a small device harness (no game media).

Run from a C++ build environment; --compiler accepts clang++ or cl-compatible clang-cl.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='clang++')
    parser.add_argument('--source', type=Path, default=Path(__file__).parent / 'native-overrides/photo_replay_stage.inc')
    args = parser.parse_args()
    stage = args.source.read_text()
    filters = stage[stage.index('void photo_replay_filter_device_state('):stage.index('void photo_replay_flush_di_keyboard(')]
    harness = r'''
#include <algorithm>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstring>
using DWORD = uint32_t;
struct DIMOUSESTATE { int32_t lX, lY, lZ; unsigned char buttons[4]; };
struct DIDEVICEOBJECTDATA_DX3 { DWORD dwOfs, dwData, dwTimeStamp, dwSequence; };
struct Harness {
    bool consume = false;
    struct { float accum_di_dx{}, accum_di_dy{}, accum_di_dz{};
        std::chrono::steady_clock::time_point suppress_escape_until{}; } photo_replay;
    bool photo_replay_consume_input() const { return consume; }
FILTERS
};
int main() {
    Harness h;
    unsigned char keys[256];
    for (unsigned char transition : {0x80, 0}) {
        std::memset(keys, transition, sizeof keys);
        h.photo_replay_filter_device_state(sizeof keys, keys);
        assert(keys[0x58] == transition); // F12 objectives, press AND release.
        assert(keys[0x1e] == transition); // Ordinary gameplay input.
        assert(keys[1] == transition);   // Escape outside overlay exit.
        assert(!keys[0x43] && !keys[0x44] && !keys[0x57]);
    }
    DIDEVICEOBJECTDATA_DX3 events[] = {
        {0x43,128,1,1}, {0x58,128,2,2}, {0x44,128,3,3},
        {0x1e,128,4,4}, {0x57,128,5,5}, {0x58,0,6,6}, {1,128,7,7}};
    DWORD count = 7;
    h.photo_replay_filter_device_data(events, count);
    assert(count == 4);
    assert(events[0].dwOfs == 0x58 && events[0].dwData == 128 && events[0].dwSequence == 2);
    assert(events[1].dwOfs == 0x1e);
    assert(events[2].dwOfs == 0x58 && events[2].dwData == 0 && events[2].dwSequence == 6);
    assert(events[3].dwOfs == 1);
    h.photo_replay.suppress_escape_until = std::chrono::steady_clock::now() + std::chrono::seconds(10);
    std::memset(keys, 128, sizeof keys);
    h.photo_replay_filter_device_state(sizeof keys, keys);
    assert(!keys[1] && keys[0x58] == 128);
    h.photo_replay_filter_device_data(events, count);
    assert(count == 3 && events[2].dwOfs == 0x58);
    h.consume = true;
    h.photo_replay_filter_device_state(sizeof keys, keys);
    assert(std::all_of(keys, keys + 256, [](auto k) { return k == 0; }));
    h.photo_replay_filter_device_data(events, count);
    assert(count == 0); // Photo/replay still owns input while active.
    DIMOUSESTATE mouse{3, -4, 1, {128,0,0,0}};
    h.photo_replay_filter_device_state(sizeof mouse, reinterpret_cast<unsigned char*>(&mouse));
    assert(h.photo_replay.accum_di_dx == 3 && h.photo_replay.accum_di_dy == -4);
    assert(mouse.lX == 0 && mouse.buttons[0] == 0);
}
'''.replace('FILTERS', filters)
    with tempfile.TemporaryDirectory(prefix='mw34-input-') as temp:
        folder = Path(temp)
        source = folder / 'input.cpp'
        source.write_text(harness)
        executable = folder / 'input.exe'
        if 'clang-cl' in Path(args.compiler).name:
            flags = ['/std:c++20', '/EHsc', str(source), '/Fe:' + str(executable)]
        else:
            flags = ['-std=c++20', str(source), '-o', str(executable)]
        subprocess.run([args.compiler, *flags], cwd=folder, check=True)
        subprocess.run([str(executable)], check=True)
    print('PASS: F12 press/release preserved in state and buffered input; capture hotkeys and overlay suppression retained.')


if __name__ == '__main__':
    main()
