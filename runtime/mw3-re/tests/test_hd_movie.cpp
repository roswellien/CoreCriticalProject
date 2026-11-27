// The HD movie stand-in (#559, mech3/hd_movie.h, docs/fmv.md section 9):
// the AVI streams the movie player is given for a mapped movie, its sound
// served in order, the frame queue, and one log line for each reason a
// clip can't stand in, and the MP4 edit lists read for the decoder. A
// fake decoder and MP4s built in memory, so no media is needed.
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <initializer_list>
#include <memory>
#include <string>
#include <thread>
#include <utility>
#include <vector>

#include "check.h"
#include "gamez/zfmv/fmv_script.h"
#include "gamez/zfmv/fmv_stream.h"
#include "gamez/zsound/zsnd.h"
#include "mech3/app_engine.h"
#include "mech3/hd_movie.h"
#include "platform/silent_sound.h"

namespace {

using mech3::HdFrame;
using mech3::HdFrameQueue;
using mech3::HdMovieInfo;
using mech3::HdMovieSource;
using mech3::HdMovieStandIn;

// A decoder whose sound is a counting ramp (sample n of channel c is
// n * channels + c) and whose pictures are whatever the test sets.
struct FakeSource : HdMovieSource {
  HdMovieInfo info;
  bool opens = true;
  int64_t sound_frames = 0;  // how much sound the file has
  int64_t next_sound = 0;
  bool decode_failed = false;
  int* destroyed = nullptr;
  std::vector<HdFrame> frames;
  ~FakeSource() override {
    if (destroyed) ++*destroyed;
  }
  bool open(const std::string&, HdMovieInfo* out, std::string* reason) override {
    if (!opens) return *reason = "the fake refused", false;
    *out = info;
    return true;
  }
  size_t read_pcm(int16_t* out, size_t count) override {
    size_t given = 0;
    for (; given < count && next_sound < sound_frames; ++given, ++next_sound)
      for (int c = 0; c < info.channels; ++c)
        out[given * info.channels + c] = static_cast<int16_t>(next_sound * info.channels + c);
    return given;
  }
  bool frame_at(double seconds, HdFrame* out) override {
    bool found = false;
    for (const HdFrame& f : frames)
      if (f.pts <= seconds) *out = f, found = true;
    return found;
  }
  bool failed(std::string* reason) override {
    if (decode_failed) *reason = "the fake broke";
    return decode_failed;
  }
};

// INTRO's HD clip as the pack has it: 182.5 s, 1280x960, 22050 Hz stereo.
HdMovieInfo intro_clip() {
  HdMovieInfo info;
  info.seconds = 182.5, info.width = 1280, info.height = 960, info.audio_rate = 22050, info.channels = 2;
  return info;
}

struct Built {
  std::unique_ptr<HdMovieStandIn> stand_in;
  FakeSource* source = nullptr;  // owned by the stand-in once started
  std::vector<std::string> log;
};

// A stand-in for `name` over one fake; `adjust` changes the fake first.
template <class Adjust>
void build(Built& b, const std::string& name, Adjust adjust, int* destroyed = nullptr) {
  auto fake = std::make_unique<FakeSource>();
  fake->info = intro_clip();
  fake->sound_frames = 22050 * 3;
  fake->destroyed = destroyed;
  adjust(*fake);
  b.source = fake.get();
  auto handed = std::make_shared<std::unique_ptr<FakeSource>>(std::move(fake));
  mech3::HdMovieFactory factory = [handed]() -> std::unique_ptr<HdMovieSource> { return std::move(*handed); };
  b.stand_in = std::make_unique<HdMovieStandIn>(name, "intro.mp4", factory,
                                                [&b](const std::string& line) { b.log.push_back(line); });
}

uint32_t read32(const std::vector<uint8_t>& bytes, size_t at) {
  uint32_t value = 0;
  std::memcpy(&value, &bytes[at], 4);
  return value;
}
uint16_t read16(const std::vector<uint8_t>& bytes, size_t at) {
  uint16_t value = 0;
  std::memcpy(&value, &bytes[at], 2);
  return value;
}

}  // namespace

TEST(hd_movie_names_and_the_shape_table) {
  EXPECT(mech3::hd_movie_name("./video\\INTRO.AVI") == "intro");
  EXPECT(mech3::hd_movie_name("video/c1m1.avi") == "c1m1");
  int frames = 0, width = 0, height = 0;
  EXPECT(mech3::hd_movie_table("intro", &frames, &width, &height));
  EXPECT(frames == 2737 && width == 640 && height == 480);
  EXPECT(!mech3::hd_movie_table("intr", &frames, &width, &height));  // a prefix is not a name
  EXPECT(!mech3::hd_movie_table("nosuchmovie", &frames, &width, &height));
}

TEST(hd_movie_stand_in_streams_are_the_originals_shape) {
  Built b;
  build(b, "intro", [](FakeSource&) {});
  EXPECT(b.stand_in->start());
  EXPECT(b.log.size() == 1 && b.log[0] == "mw3: hd movie intro: intro.mp4 (1280x960, 182.5 s)");
  const std::vector<uint8_t>& video = b.stand_in->video_format();
  EXPECT(video.size() == 40 && read32(video, 4) == 640 && read32(video, 8) == 480 && read16(video, 14) == 16);
  EXPECT(b.stand_in->video_info().length == 2737);
  EXPECT(b.stand_in->video_info().rate == 15 && b.stand_in->video_info().scale == 1);
  const std::vector<uint8_t>& audio = b.stand_in->audio_format();
  EXPECT(audio.size() == 18 && read16(audio, 0) == 1 && read16(audio, 2) == 2 && read32(audio, 4) == 22050);
  EXPECT(read16(audio, 12) == 4 && read16(audio, 14) == 16);
  EXPECT(b.stand_in->audio_info().sample_size == 4);
  EXPECT(b.stand_in->audio_info().suggested_buffer == 22050 * 4);  // one second a half
  EXPECT(b.stand_in->audio_info().length == 22050u * 1825 / 10);
}

TEST(hd_movie_stand_in_serves_sound_in_order_then_silence) {
  Built b;
  build(b, "intro", [](FakeSource& f) { f.sound_frames = 1000; });
  EXPECT(b.stand_in->start());
  std::vector<int16_t> buffer(2 * 600, 7);
  b.stand_in->read_audio(0, 600, buffer.data(), static_cast<int32_t>(buffer.size() * 2));
  EXPECT(buffer[0] == 0 && buffer[1] == 1 && buffer[2 * 599 + 1] == 2 * 599 + 1);
  // The next read goes on from 600; past the file's 1000 frames it is silent.
  std::fill(buffer.begin(), buffer.end(), int16_t{7});
  b.stand_in->read_audio(600, 600, buffer.data(), static_cast<int32_t>(buffer.size() * 2));
  EXPECT(buffer[0] == 2 * 600 && buffer[2 * 399 + 1] == 2 * 999 + 1);
  EXPECT(buffer[2 * 400] == 0 && buffer[2 * 599 + 1] == 0);
  // A read further on skips ahead to its start.
  Built skip;
  build(skip, "intro", [](FakeSource& f) { f.sound_frames = 1000; });
  EXPECT(skip.stand_in->start());
  skip.stand_in->read_audio(100, 10, buffer.data(), static_cast<int32_t>(buffer.size() * 2));
  EXPECT(buffer[0] == 2 * 100);
}

TEST(hd_movie_frame_queue_picks_by_time_and_stops) {
  HdFrameQueue queue;
  for (int i = 0; i < 3; ++i) {
    HdFrame f;
    f.pts = i / 24.0, f.serial = static_cast<uint64_t>(i + 1);
    EXPECT(queue.push(f));
  }
  HdFrame picked;
  EXPECT(!queue.pick(-0.01, &picked));
  EXPECT(queue.pick(1.5 / 24.0, &picked) && picked.serial == 2);  // the newest due; 1 dropped
  EXPECT(queue.pick(10.0, &picked) && picked.serial == 3);
  EXPECT(!queue.pick(10.0, &picked));
  // A full queue's push waits until stop() wakes it, then refuses.
  HdFrameQueue full;
  for (size_t i = 0; i < HdFrameQueue::kCapacity; ++i) EXPECT(full.push(HdFrame{}));
  bool refused = false;
  std::thread pusher([&] { refused = !full.push(HdFrame{}); });
  full.stop();
  pusher.join();
  EXPECT(refused);
}

TEST(hd_movie_stand_in_holds_the_last_picture_and_logs_a_failure_once) {
  Built b;
  build(b, "intro", [](FakeSource& f) {
    HdFrame first;
    first.serial = 1, first.pts = 0;
    f.frames.push_back(first);
  });
  HdFrame shown;
  EXPECT(b.stand_in->start());
  EXPECT(b.stand_in->frame_at(5.0, &shown) && shown.serial == 1);
  b.source->frames.clear();
  b.source->decode_failed = true;
  EXPECT(b.stand_in->frame_at(6.0, &shown) && shown.serial == 1);
  EXPECT(b.stand_in->frame_at(7.0, &shown) && shown.serial == 1);
  EXPECT(b.log.size() == 2 && b.log[1].find("decoding stopped (the fake broke)") != std::string::npos);
}

TEST(hd_movie_each_unusable_clip_plays_the_original_with_one_line) {
  struct Case {
    const char* name;
    void (*adjust)(FakeSource&);
    const char* reason;
  };
  const Case cases[] = {
      {"intro", [](FakeSource& f) { f.opens = false; }, "(the fake refused)"},
      {"nosuchmovie", [](FakeSource&) {}, "(the original's length is not known)"},
      {"intro", [](FakeSource& f) { f.info.seconds = 184.0; }, "(its length is 184.0 s, the original's 182.5 s)"},
      {"intro", [](FakeSource& f) { f.info.audio_rate = 44100; }, "(audio is 44100 Hz, not 22050)"},
      {"intro", [](FakeSource& f) { f.info.channels = 6; }, "(6 sound channels)"},
      {"intro", [](FakeSource& f) { f.info.channels = 0; }, "(it has no sound)"},
  };
  for (const Case& c : cases) {
    Built b;
    int destroyed = 0;
    build(b, c.name, c.adjust, &destroyed);
    EXPECT(!b.stand_in->start());
    EXPECT(b.log.size() == 1);
    EXPECT(b.log.size() == 1 && b.log[0].find(c.reason) != std::string::npos &&
           b.log[0].find("; playing the original") != std::string::npos);
    EXPECT(destroyed == 1);  // a refused source is closed at once
    std::string reason;
    EXPECT(!HdMovieStandIn::validate(c.name, "x.mp4", [c]() -> std::unique_ptr<HdMovieSource> {
      auto fake = std::make_unique<FakeSource>();
      fake->info = intro_clip();
      c.adjust(*fake);
      return fake;
    }, &reason));
    EXPECT(!reason.empty());
  }
}

TEST(hd_movie_stand_in_closes_its_source_once) {
  int destroyed = 0;
  {
    Built b;
    build(b, "intro", [](FakeSource&) {}, &destroyed);
    EXPECT(b.stand_in->start());
    EXPECT(destroyed == 0);
  }
  EXPECT(destroyed == 1);
}

namespace {

// MP4 boxes built in memory: a big-endian size, the type, the contents.
using Bytes = std::vector<uint8_t>;

void append_big(Bytes& bytes, uint64_t value, int size) {
  for (int shift = (size - 1) * 8; shift >= 0; shift -= 8) bytes.push_back(static_cast<uint8_t>(value >> shift));
}

Bytes mp4_box(const char* type, const Bytes& contents) {
  Bytes box;
  append_big(box, contents.size() + 8, 4);
  box.insert(box.end(), type, type + 4);
  box.insert(box.end(), contents.begin(), contents.end());
  return box;
}

Bytes joined(std::initializer_list<Bytes> parts) {
  Bytes all;
  for (const Bytes& part : parts) all.insert(all.end(), part.begin(), part.end());
  return all;
}

Bytes mdhd(uint32_t timescale) {
  Bytes contents(4 + 8);  // version 0, flags, created, modified
  append_big(contents, timescale, 4);
  append_big(contents, 0, 4 + 4);  // duration, language and pre_defined
  return mp4_box("mdhd", contents);
}

Bytes hdlr(const char* handler) {
  Bytes contents(8);  // version, flags, pre_defined
  contents.insert(contents.end(), handler, handler + 4);
  contents.resize(contents.size() + 13);  // reserved and an empty name
  return mp4_box("hdlr", contents);
}

// An 'elst' whose entries are (duration, media time) pairs.
Bytes elst(bool version1, std::initializer_list<std::pair<uint64_t, int64_t>> entries) {
  Bytes contents{static_cast<uint8_t>(version1 ? 1 : 0), 0, 0, 0};
  append_big(contents, entries.size(), 4);
  for (const auto& entry : entries) {
    append_big(contents, entry.first, version1 ? 8 : 4);
    append_big(contents, static_cast<uint64_t>(entry.second), version1 ? 8 : 4);
    append_big(contents, 0x00010000, 4);  // rate 1.0
  }
  return mp4_box("elst", contents);
}

Bytes trak(const char* handler, uint32_t timescale, const Bytes& edits) {
  const Bytes media = mp4_box("mdia", joined({mdhd(timescale), hdlr(handler)}));
  if (edits.empty()) return mp4_box("trak", media);
  return mp4_box("trak", joined({mp4_box("edts", edits), media}));
}

// The movie header: its timescale counts the edit lists' durations.
// Version 0 has 4 bytes each of created and modified before it, version 1
// has 8 and 8; the rest (duration, rate, matrix, ...) is left zero.
Bytes mvhd(uint32_t timescale, bool version1 = false) {
  Bytes contents{static_cast<uint8_t>(version1 ? 1 : 0), 0, 0, 0};
  contents.resize(version1 ? 20 : 12);
  append_big(contents, timescale, 4);
  contents.resize(version1 ? 108 : 96);
  return mp4_box("mvhd", contents);
}

mech3::Mp4SoundEdit sound_edit_of(const Bytes& file) {
  const auto read_at = [&file](uint64_t offset, void* out, size_t bytes) {
    if (offset > file.size() || file.size() - offset < bytes) return false;
    std::memcpy(out, file.data() + offset, bytes);
    return true;
  };
  return mech3::mp4_sound_edit(read_at, file.size());
}

bool close_to(double value, double expected) { return std::fabs(value - expected) < 1e-9; }

}  // namespace

// The pack's own layout (ffmpeg's): the movie box ahead of the media at a
// 1000 timescale, the video's edit two 24 fps frames in at 12288 (its
// B-frame delay, not wanted here), the sound's 1024 priming samples in at
// 22050 and 182.467 s long, so INTRO's last AAC frame's 923 padding
// samples (4,024,320 decoded) are left out: ffmpeg's 4,023,397.
TEST(hd_movie_mp4_edit_list_gives_the_sounds_priming_and_length) {
  const Bytes moov = mp4_box("moov", joined({mvhd(1000), trak("vide", 12288, elst(false, {{182500, 1024}})),
                                             trak("soun", 22050, elst(false, {{182467, 1024}}))}));
  const Bytes file = joined({mp4_box("ftyp", Bytes(24)), moov, mp4_box("mdat", Bytes(64))});
  const mech3::Mp4SoundEdit edit = sound_edit_of(file);
  EXPECT(close_to(edit.start, 1024.0 / 22050.0));
  EXPECT(close_to(edit.length, 182.467));
  EXPECT(std::llround(edit.length * 22050) == 4023397);
}

// An empty edit (media time -1) delays a track instead of trimming it, so
// the next entry is the edit; version 1 entries and headers are 64-bit; the
// movie box may come after the media and its header after the tracks. A
// sound track with no edit list keeps everything, and without the movie's
// timescale the length is unknown (0) while the start is still read.
TEST(hd_movie_mp4_edit_list_skips_empty_edits_and_reads_version_1) {
  const Bytes moov =
      mp4_box("moov", joined({trak("vide", 90000, elst(false, {{9000, 3003}})),
                              trak("soun", 48000, elst(true, {{500, -1}, {9000, 2112}})), mvhd(600, true)}));
  const mech3::Mp4SoundEdit edit = sound_edit_of(joined({mp4_box("mdat", Bytes(32)), moov}));
  EXPECT(close_to(edit.start, 2112.0 / 48000.0));
  EXPECT(close_to(edit.length, 9000.0 / 600.0));
  const mech3::Mp4SoundEdit no_edit = sound_edit_of(mp4_box("moov", joined({mvhd(1000), trak("soun", 48000, Bytes())})));
  EXPECT(no_edit.start == 0.0 && no_edit.length == 0.0);
  const mech3::Mp4SoundEdit no_header = sound_edit_of(mp4_box("moov", trak("soun", 22050, elst(false, {{100, 1024}}))));
  EXPECT(close_to(no_header.start, 1024.0 / 22050.0) && no_header.length == 0.0);
}

// A box that claims more than the file holds, or nothing like an MP4,
// gives zeros rather than reading past the end.
TEST(hd_movie_mp4_edit_list_of_a_broken_file_is_zero) {
  Bytes moov = mp4_box("moov", joined({mvhd(1000), trak("soun", 22050, elst(false, {{100, 1024}}))}));
  moov[3] = 0xff;  // the movie box's size now runs past the file
  const auto zero = [](const mech3::Mp4SoundEdit& edit) { return edit.start == 0.0 && edit.length == 0.0; };
  EXPECT(zero(sound_edit_of(moov)));
  EXPECT(zero(sound_edit_of(Bytes{'n', 'o', 't', ' ', 'm', 'p', '4', '!', '!'})));
  EXPECT(zero(sound_edit_of(Bytes())));
}

namespace {

// The movie host's side (GameFmvHost, app_fmv.cpp): a screen that records
// the HD frames it is given, and a clock the silent sound's cursor follows.
struct HdScreen : platform::Screen2D {
  struct Shown {
    uint64_t serial = 0;
    int width = 0, height = 0, src_top = 0, src_bottom = 0;
  };
  std::vector<Shown> shown;
  int released = 0;
  void present_16(const uint16_t*, int, int, int, bool) override {}
  bool present_frame_rgba(const uint8_t*, int width, int height, int, uint64_t serial, int src_top,
                          int src_bottom) override {
    shown.push_back({serial, width, height, src_top, src_bottom});
    return true;
  }
  void release_frame_rgba() override { ++released; }
};

struct StepClock : platform::Clock {
  uint32_t ms = 0;
  uint32_t ticks_ms() override { return ms; }
};

HdFrame fake_picture(double pts, uint64_t serial) {
  HdFrame frame;
  frame.width = 1280, frame.height = 960, frame.pitch = 1280 * 4;
  frame.bgra = std::make_shared<std::vector<uint8_t>>(static_cast<size_t>(frame.pitch) * frame.height,
                                                       uint8_t{0x80});
  frame.pts = pts, frame.serial = serial;
  return frame;
}

}  // namespace

// The whole path a mapped movie takes in the program, with a fake decoder:
// the script's file check finds it without the original AVI, the ported
// player (zfmv::Stream) opens the stand-in through the host and plays it on
// the silent sound's clocked cursor, the engine shows the decoded picture
// due for that sound in the movie's shape, and the player's release ends it.
TEST(hd_movie_host_plays_a_mapped_movie_through_the_player) {
  StepClock clock;
  HdScreen screen;
  platform::SilentSoundOutput sound;
  sound.clock = &clock;
  mech3::Platform p;
  p.clock = &clock, p.movie_clock = &clock, p.screen = &screen, p.sound = &sound;
  p.hd_movies["intro"] = "intro.mp4";
  int sources_made = 0;
  p.hd_movie_factory = [&sources_made]() -> std::unique_ptr<HdMovieSource> {
    auto fake = std::make_unique<FakeSource>();
    fake->info = intro_clip();
    fake->sound_frames = 22050 * 4;
    fake->frames = {fake_picture(0.0, 1), fake_picture(1.0, 2)};
    ++sources_made;
    return fake;
  };
  {
    mech3::GameEngine engine(p, "mech3.exe -nofmv");
    engine.quiet = true;
    zsnd::state() = zsnd::State{};  // as a new process: zSound not yet initialised
    EXPECT(engine.sound_init(0) == 1);
    // The device as zsnd::load opens it before reading sounds.zrd, which
    // this test has no need of.
    EXPECT(zsnd::open_device() == 1);
    zsnd::state().open = 1;
    zfmv::Host& host = zfmv::host();
    EXPECT(host.file_stat("./video\\INTRO.AVI") == 0);    // no original here: found as the HD clip
    EXPECT(host.file_stat("./video\\CAMPAIGN.AVI") == -1);  // not mapped, and no original
    {
      zfmv::Stream stream("./video\\INTRO.AVI", true);
      EXPECT(stream.video_ok && stream.audio_ok);
      EXPECT(stream.length == 2737 && stream.fps == 15);  // the original's frames, from the shape table
      EXPECT(engine.hd_movie_active_);
      EXPECT(sources_made == 2);  // checked at the file check, then the one that plays

      // A PLAYAVI pass as the script makes it (fmv_script.cpp): the frame
      // for the sound, then its image asked for to draw.
      const auto script_pass = [&] {
        stream.frame(-1);
        host.stream_image(&stream);
      };
      script_pass();  // the sound starts; the stand-in's frame 0 decoded
      bool all_black = true;
      for (uint16_t pixel : stream.pixels) all_black = all_black && pixel == 0;
      EXPECT(all_black);  // the 16-bit picture is never shown, the HD one is
      EXPECT(engine.present_hd_movie(true));
      EXPECT(screen.shown.size() == 1 && screen.shown[0].serial == 1);
      // Between the script's flips the same picture counts as shown (the
      // 16-bit buffer stays hidden) but isn't drawn again.
      EXPECT(engine.present_hd_movie(false));
      EXPECT(screen.shown.size() == 1);

      // The script's passes, one each 1/15 s (the player refills the half of
      // its sound buffer the cursor has left), each flip showing the picture
      // due: the first until 1 s of sound has played, then the second.
      double second_seen_at = -1;
      for (uint32_t ms = 66; ms <= 1500; ms += 66) {
        clock.ms = ms;
        script_pass();
        EXPECT(engine.present_hd_movie(true));
        if (second_seen_at < 0 && screen.shown.back().serial == 2) second_seen_at = stream.sound_seconds();
      }
      EXPECT(second_seen_at >= 1.0 && second_seen_at < 1.0 + 0.067);
      const HdScreen::Shown& last = screen.shown.back();
      EXPECT(last.serial == 2 && last.width == 1280 && last.height == 960);
      // INTRO's rows 79..400 of the original's 480 as rows of the 960-row clip.
      EXPECT(last.src_top == 158 && last.src_bottom == 801);
      EXPECT(screen.released == 0);
    }
    EXPECT(!engine.hd_movie_active_);  // the player's streams released: the movie is over
    EXPECT(screen.released == 1);
    EXPECT(!engine.present_hd_movie(true));
    engine.sound_shutdown();
  }
  zsnd::hooks() = zsnd::Hooks{};  // the silent output goes with this test
}
