// The HD movie stand-in (#559, mech3/hd_movie.h, docs/fmv.md section 9):
// the AVI streams the movie player is given for a mapped movie, its sound
// served in order, the frame queue, and one log line for each reason a
// clip can't stand in. A fake decoder, so no media is needed.
#include <cstdint>
#include <cstring>
#include <memory>
#include <string>
#include <thread>
#include <vector>

#include "check.h"
#include "mech3/hd_movie.h"

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
