#pragma once
// Ours (#559, docs/fmv.md section 9): an HD replacement for one of the
// game's movies, chosen with `mw3 --hd-movie NAME PATH`. The ported movie
// player (zfmv::Stream) still owns the movie: its script, skip keys, the CD
// pause and the end. It is handed a stand-in for the AVI: the original's
// frame count at 15 a second (from movie_shape_table.cpp) and the MP4's
// sound as 22050 Hz PCM. The MP4's pictures are drawn by the GPU at full
// size, timed by that sound (GameEngine::present_hd_movie). Anything wrong
// at the start plays the original movie and logs one line saying why.
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include "gamez/zfmv/fmv_stream.h"

namespace mech3 {

// What an opened HD movie holds.
struct HdMovieInfo {
  double seconds = 0;  // the longer of its picture and sound
  int width = 0, height = 0;
  int audio_rate = 0, channels = 0;  // 0 channels: no sound
};

// One decoded picture: 32-bit RGBA (the order the renderer's textures take,
// so the game's thread uploads it as it is), top row first, `pitch` bytes a
// row. The shared buffer keeps a picked frame alive while the decoder goes
// on: a buffer once handed out is never written again.
struct HdFrame {
  std::shared_ptr<const std::vector<uint8_t>> rgba;
  int width = 0, height = 0, pitch = 0;
  double pts = 0;       // seconds from the movie's start
  uint64_t serial = 0;  // different for every decoded frame; 0 none
};

// A frame and the rows of it to show (the movie's shape, movie_shape.h, in
// the clip's own rows); -1 for the whole frame.
struct HdPresentFrame {
  HdFrame frame;
  int src_top = -1, src_bottom = -1;
};

// A decoder for one HD movie file. Used from the game's thread only; a
// backend may decode pictures on a thread of its own.
class HdMovieSource {
 public:
  virtual ~HdMovieSource() = default;  // closes the file and stops any thread
  // False with `reason` (a short phrase for the log) when it cannot be played.
  virtual bool open(const std::string& path, HdMovieInfo* info, std::string* reason) = 0;
  // The next `frames` sample frames of 16-bit interleaved sound at the
  // file's rate; fewer at the end of the sound.
  virtual size_t read_pcm(int16_t* out, size_t frames) = 0;
  // The newest decoded picture at or before `seconds`; false when none yet.
  virtual bool frame_at(double seconds, HdFrame* out) = 0;
  // True with `reason` once decoding has failed part way through.
  virtual bool failed(std::string* reason) = 0;
};

using HdMovieFactory = std::function<std::unique_ptr<HdMovieSource>()>;
// Media Foundation on Windows (hd_movie_mf.cpp); elsewhere a source that
// always says no decoder is available.
HdMovieFactory default_hd_movie_factory();

// The decoded pictures waiting to be shown, at most `kCapacity` of them: a
// decoder thread pushes, the game's thread picks by time. Bounded so a fast
// decoder never holds more than a few 1280x960 frames (about 5 MB each);
// three is 125 ms ahead at 24 a second, kept low for #559's memory budget.
class HdFrameQueue {
 public:
  static constexpr size_t kCapacity = 3;
  // Waits while full; false once stopped (the frame is dropped).
  bool push(HdFrame frame);
  // The newest frame at or before `seconds`, the older ones dropped. False
  // when none is that early yet (the last picked stays the caller's).
  bool pick(double seconds, HdFrame* out);
  void stop();  // wakes every wait; push refuses from then on

 private:
  std::mutex mutex_;
  std::condition_variable space_;
  std::vector<HdFrame> frames_;  // in decode order (rising pts)
  bool stopped_ = false;
};

// The movie name the option and the shape table use for an AVI path:
// "./video\INTRO.AVI" -> "intro" (movie_shape_key's name part).
std::string hd_movie_name(const char* avi_path);
// The shape table's line for `name`: the original's frames and picture size.
bool hd_movie_table(const std::string& name, int* frames, int* width, int* height);

// Reads `bytes` at `offset` of a file; false past its end or on an error.
using Mp4ReadAt = std::function<bool(uint64_t offset, void* out, size_t bytes)>;
// What an MP4's first sound track's edit list (ISO 14496-12 'elst', the
// first entry that isn't an empty edit) keeps of the decoded sound. Media
// Foundation ignores edit lists, so its backend applies this itself.
struct Mp4SoundEdit {
  // Seconds skipped at the front: the AAC encoder's priming, 1024 samples
  // in the pack's clips. 0 with no edit list.
  double start = 0;
  // Seconds played from there; what follows is the encoder's padding of
  // the last AAC frame (923 samples in INTRO). 0 when unknown: play it all.
  double length = 0;
};
// The edit, or zeros for anything unreadable.
Mp4SoundEdit mp4_sound_edit(const Mp4ReadAt& read_at, uint64_t file_size);

// One play of a mapped movie: the HD source and the AVI stand-in the movie
// player reads (spec 3.4). Built at the AVI's open; destroyed with the
// player's streams.
class HdMovieStandIn {
 public:
  using Log = std::function<void(const std::string& line)>;
  HdMovieStandIn(std::string name, std::string path, HdMovieFactory factory, Log log);
  // Opens and checks the movie; logs exactly one line, used or not used.
  bool start();
  // The same checks without keeping the source (the script's load, long
  // before its play); no log line. False with `reason` when not playable.
  static bool validate(const std::string& name, const std::string& path, const HdMovieFactory& factory,
                       std::string* reason);

  // AVIStreamReadFormat / AVIStreamInfoA for the stand-in's two streams.
  const std::vector<uint8_t>& video_format() const { return video_format_; }
  const std::vector<uint8_t>& audio_format() const { return audio_format_; }
  const zfmv::AviStreamInfo& video_info() const { return video_info_; }
  const zfmv::AviStreamInfo& audio_info() const { return audio_info_; }
  // AVIStreamRead on the sound: `samples` sample frames from `start`;
  // silence past the movie's sound. The player reads in order.
  int32_t read_audio(int32_t start, int32_t samples, void* buffer, int32_t bytes);
  // The picture for `seconds` of sound played (the last one kept between
  // calls); false before the first is decoded. A failure part way through
  // is logged once and the last picture held.
  bool frame_at(double seconds, HdFrame* out);
  int clip_height() const { return info_.height; }
  int table_height() const { return table_height_; }
  const std::string& name() const { return name_; }

 private:
  // Why `info` from `name`'s file cannot stand in for the original, or "".
  static std::string unusable(const std::string& name, const HdMovieInfo& info);
  void build_formats();

  std::string name_, path_;
  HdMovieFactory factory_;
  Log log_;
  std::unique_ptr<HdMovieSource> source_;
  HdMovieInfo info_;
  int table_frames_ = 0, table_width_ = 0, table_height_ = 0;
  std::vector<uint8_t> video_format_, audio_format_;
  zfmv::AviStreamInfo video_info_, audio_info_;
  int64_t audio_position_ = 0;  // sample frames handed to the player so far
  std::vector<int16_t> discard_;  // for a read that skips ahead
  HdFrame last_;
  bool failure_logged_ = false;
};

}  // namespace mech3
