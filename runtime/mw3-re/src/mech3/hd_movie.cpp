// Ours (#559): the HD movie stand-in (hd_movie.h, docs/fmv.md section 9).
#include "mech3/hd_movie.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "mech3/movie_shape.h"

namespace mech3 {

namespace {

constexpr uint32_t kVidsType = 0x73646976;  // 'vids'
constexpr uint32_t kAudsType = 0x73647561;  // 'auds'
// The original movies' sound: 22050 Hz 16-bit PCM (CinematicPack.cs, the
// importer's .wav). The player's frame count comes from this rate, so a
// clip at another rate would play at the wrong speed.
constexpr int kAudioRate = 22050;
constexpr double kOriginalFps = 15.0;
// The most a clip's length may differ from the original's frames / 15 and
// still stand in (the pack's clips are within 0.1 s; issue #559).
constexpr double kLengthTolerance = 1.0;
constexpr int kLargestPicture = 4096;

void put16(std::vector<uint8_t>& bytes, size_t at, uint16_t value) { std::memcpy(&bytes[at], &value, 2); }
void put32(std::vector<uint8_t>& bytes, size_t at, uint32_t value) { std::memcpy(&bytes[at], &value, 4); }

std::string seconds_text(double seconds) {
  char text[32];
  std::snprintf(text, sizeof text, "%.1f s", seconds);
  return text;
}

#ifndef MW3_HD_MOVIE_MF
// No decoder in this build: every HD movie plays its original.
class UnavailableHdMovieSource : public HdMovieSource {
 public:
  bool open(const std::string&, HdMovieInfo*, std::string* reason) override {
    *reason = "no HD movie decoder on this platform";
    return false;
  }
  size_t read_pcm(int16_t*, size_t) override { return 0; }
  bool frame_at(double, HdFrame*) override { return false; }
  bool failed(std::string*) override { return false; }
};
#endif

}  // namespace

#ifndef MW3_HD_MOVIE_MF
HdMovieFactory default_hd_movie_factory() {
  return [] { return std::make_unique<UnavailableHdMovieSource>(); };
}
#endif

bool HdFrameQueue::push(HdFrame frame) {
  std::unique_lock<std::mutex> lock(mutex_);
  space_.wait(lock, [this] { return stopped_ || frames_.size() < kCapacity; });
  if (stopped_) return false;
  frames_.push_back(std::move(frame));
  return true;
}

bool HdFrameQueue::pick(double seconds, HdFrame* out) {
  std::lock_guard<std::mutex> lock(mutex_);
  size_t newest_due = frames_.size();
  for (size_t i = 0; i < frames_.size(); ++i)
    if (frames_[i].pts <= seconds) newest_due = i;
  if (newest_due == frames_.size()) return false;
  *out = frames_[newest_due];
  frames_.erase(frames_.begin(), frames_.begin() + static_cast<std::ptrdiff_t>(newest_due) + 1);
  space_.notify_all();
  return true;
}

void HdFrameQueue::stop() {
  std::lock_guard<std::mutex> lock(mutex_);
  stopped_ = true;
  frames_.clear();
  space_.notify_all();
}

std::string hd_movie_name(const char* avi_path) {
  MovieShapeKeyParts parts;
  movie_shape_key_parts(movie_shape_key(avi_path ? avi_path : "", 0, 0, 0), &parts);
  return parts.name;
}

bool hd_movie_table(const std::string& name, int* frames, int* width, int* height) {
  for (const std::string& line : movie_shape_table()) {
    std::string key;
    std::vector<MovieShapeRun> runs;
    MovieShapeKeyParts parts;
    if (!movie_shape_parse(line, &key, &runs) || !movie_shape_key_parts(key, &parts)) continue;
    if (parts.name != name) continue;
    *frames = parts.frames, *width = parts.width, *height = parts.height;
    return parts.frames > 0 && parts.width > 0 && parts.height > 0;
  }
  return false;
}

namespace {

// MP4 numbers are big-endian.
uint32_t big32(const uint8_t* bytes) {
  return (uint32_t(bytes[0]) << 24) | (uint32_t(bytes[1]) << 16) | (uint32_t(bytes[2]) << 8) | bytes[3];
}
uint64_t big64(const uint8_t* bytes) { return (uint64_t(big32(bytes)) << 32) | big32(bytes + 4); }

// One box of an MP4: its four-letter type, where its contents start and
// where it ends.
struct Mp4Box {
  char type[5] = {};
  uint64_t body = 0, end = 0;
};

// The box at `at`, which must lie inside its parent (ending at `parent_end`).
bool read_mp4_box(const Mp4ReadAt& read_at, uint64_t at, uint64_t parent_end, Mp4Box* box) {
  uint8_t header[16];
  if (parent_end < at || parent_end - at < 8 || !read_at(at, header, 8)) return false;
  uint64_t size = big32(header);
  uint64_t header_size = 8;
  if (size == 1) {  // a 64-bit size follows the type
    if (parent_end - at < 16 || !read_at(at + 8, header + 8, 8)) return false;
    size = big64(header + 8);
    header_size = 16;
  } else if (size == 0) {  // runs to the end of its parent
    size = parent_end - at;
  }
  if (size < header_size || size > parent_end - at) return false;
  std::memcpy(box->type, header + 4, 4);
  box->body = at + header_size;
  box->end = at + size;
  return true;
}

// The first entry of an 'elst' that isn't an empty edit (media time -1,
// which delays the track instead of trimming it).
struct Mp4Edit {
  uint64_t duration = 0;  // how long it plays, in the movie's units ('mvhd')
  int64_t media_time = 0;  // where it starts, in the track's units ('mdhd')
};

// What one 'trak' says about which part of its media plays.
struct Mp4Track {
  char handler[5] = {};  // 'vide', 'soun', ...
  uint32_t timescale = 0;  // the media's units a second ('mdhd')
  Mp4Edit edit;  // zeros without an edit list
};

Mp4Edit read_edit(const Mp4ReadAt& read_at, const Mp4Box& elst) {
  uint8_t head[8];
  if (elst.end - elst.body < 8 || !read_at(elst.body, head, 8)) return {};
  const bool wide = head[0] == 1;  // version 1: 64-bit duration and media time
  const uint64_t entry_size = wide ? 20 : 12;
  const uint32_t entries = big32(head + 4);
  uint64_t at = elst.body + 8;
  for (uint32_t i = 0; i < entries && i < 16 && elst.end - at >= entry_size; ++i, at += entry_size) {
    uint8_t entry[20];
    if (!read_at(at, entry, static_cast<size_t>(entry_size))) return {};
    const int64_t media_time =
        wide ? static_cast<int64_t>(big64(entry + 8)) : static_cast<int64_t>(static_cast<int32_t>(big32(entry + 4)));
    if (media_time == -1) continue;
    Mp4Edit edit;
    edit.duration = wide ? big64(entry) : big32(entry);
    edit.media_time = media_time > 0 ? media_time : 0;
    return edit;
  }
  return {};
}

// The timescale at the same place in 'mdhd' and 'mvhd': version 0 has 4
// bytes each of created and modified before it, version 1 has 8 and 8.
uint32_t read_timescale(const Mp4ReadAt& read_at, const Mp4Box& box) {
  uint8_t head[24];
  if (box.end - box.body < 24 || !read_at(box.body, head, 24)) return 0;
  return big32(head + (head[0] == 1 ? 20 : 12));
}

// The children of a 'trak' that tell its handler, timescale and edit:
// 'edts'/'elst', 'mdia'/'mdhd' and 'mdia'/'hdlr'. `depth` stops a file whose
// boxes nest without end.
void read_track_boxes(const Mp4ReadAt& read_at, uint64_t at, uint64_t end, int depth, Mp4Track* track) {
  Mp4Box box;
  while (depth < 4 && read_mp4_box(read_at, at, end, &box)) {
    const std::string type = box.type;
    if (type == "edts" || type == "mdia") {
      read_track_boxes(read_at, box.body, box.end, depth + 1, track);
    } else if (type == "elst") {
      track->edit = read_edit(read_at, box);
    } else if (type == "mdhd") {
      track->timescale = read_timescale(read_at, box);
    } else if (type == "hdlr") {
      uint8_t head[12];  // version and flags, pre_defined, then the handler type
      if (box.end - box.body >= 12 && read_at(box.body, head, 12)) std::memcpy(track->handler, head + 8, 4);
    }
    at = box.end;
  }
}

}  // namespace

Mp4SoundEdit mp4_sound_edit(const Mp4ReadAt& read_at, uint64_t file_size) {
  Mp4Box top;
  for (uint64_t at = 0; read_mp4_box(read_at, at, file_size, &top); at = top.end) {
    if (std::string(top.type) != "moov") continue;
    // The movie's timescale counts the edit's duration; 'mvhd' normally
    // comes first, but nothing requires it, so the whole box is read.
    uint32_t movie_timescale = 0;
    Mp4Track sound;
    bool sound_found = false;
    Mp4Box child;
    for (uint64_t inner = top.body; read_mp4_box(read_at, inner, top.end, &child); inner = child.end) {
      const std::string type = child.type;
      if (type == "mvhd") {
        movie_timescale = read_timescale(read_at, child);
      } else if (type == "trak" && !sound_found) {
        Mp4Track track;
        read_track_boxes(read_at, child.body, child.end, 0, &track);
        sound_found = std::string(track.handler) == "soun";
        if (sound_found) sound = track;
      }
    }
    Mp4SoundEdit edit;
    if (!sound_found || sound.timescale == 0) return edit;
    edit.start = static_cast<double>(sound.edit.media_time) / sound.timescale;
    if (movie_timescale > 0) edit.length = static_cast<double>(sound.edit.duration) / movie_timescale;
    return edit;  // one movie box
  }
  return {};
}

HdMovieStandIn::HdMovieStandIn(std::string name, std::string path, HdMovieFactory factory, Log log)
    : name_(std::move(name)), path_(std::move(path)), factory_(std::move(factory)), log_(std::move(log)) {}

std::string HdMovieStandIn::unusable(const std::string& name, const HdMovieInfo& info) {
  int frames = 0, width = 0, height = 0;
  if (!hd_movie_table(name, &frames, &width, &height)) return "the original's length is not known";
  const double original_seconds = frames / kOriginalFps;
  if (std::fabs(info.seconds - original_seconds) > kLengthTolerance)
    return "its length is " + seconds_text(info.seconds) + ", the original's " + seconds_text(original_seconds);
  if (info.width <= 0 || info.height <= 0 || info.width > kLargestPicture || info.height > kLargestPicture)
    return "its picture is " + std::to_string(info.width) + "x" + std::to_string(info.height);
  if (info.channels != 1 && info.channels != 2)
    return info.channels == 0 ? std::string("it has no sound") : std::to_string(info.channels) + " sound channels";
  if (info.audio_rate != kAudioRate) return "audio is " + std::to_string(info.audio_rate) + " Hz, not 22050";
  return {};
}

bool HdMovieStandIn::validate(const std::string& name, const std::string& path, const HdMovieFactory& factory,
                              std::string* reason) {
  std::unique_ptr<HdMovieSource> source = factory ? factory() : nullptr;
  if (!source) return *reason = "no HD movie decoder", false;
  HdMovieInfo info;
  if (!source->open(path, &info, reason)) {
    if (reason->empty()) *reason = "it could not be opened";
    return false;
  }
  *reason = unusable(name, info);
  return reason->empty();
}

bool HdMovieStandIn::start() {
  std::string reason;
  source_ = factory_ ? factory_() : nullptr;
  if (!source_) {
    reason = "no HD movie decoder";
  } else {
    const bool opened = source_->open(path_, &info_, &reason);
    if (opened) reason = unusable(name_, info_);
    else if (reason.empty()) reason = "it could not be opened";
  }
  if (!reason.empty()) {
    source_.reset();
    if (log_) log_("mw3: hd movie " + name_ + " not used (" + reason + "); playing the original");
    return false;
  }
  hd_movie_table(name_, &table_frames_, &table_width_, &table_height_);
  build_formats();
  if (log_)
    log_("mw3: hd movie " + name_ + ": " + path_ + " (" + std::to_string(info_.width) + "x" +
         std::to_string(info_.height) + ", " + seconds_text(info_.seconds) + ")");
  return true;
}

// The stand-in's two streams as the player reads them (fmv_stream.cpp):
// - the picture: a BITMAPINFOHEADER of the original's size at 16 bits, its
//   frames at 15 a second, so the shape table's key ("intro/2737/640x480")
//   matches and the player's frame count and end are the original's;
// - the sound: WAVEFORMATEX PCM at 22050 Hz, 16-bit, the clip's channels,
//   one second a buffer half (what Video for Windows gives INTRO).
void HdMovieStandIn::build_formats() {
  video_format_.assign(40, 0);
  put32(video_format_, 0, 40);
  put32(video_format_, 4, static_cast<uint32_t>(table_width_));
  put32(video_format_, 8, static_cast<uint32_t>(table_height_));
  put16(video_format_, 12, 1);   // planes
  put16(video_format_, 14, 16);  // bits
  put32(video_format_, 20, static_cast<uint32_t>(table_width_ * table_height_ * 2));
  video_info_ = {};
  video_info_.type = kVidsType;
  video_info_.scale = 1;
  video_info_.rate = static_cast<uint32_t>(kOriginalFps);
  video_info_.length = static_cast<uint32_t>(table_frames_);
  video_info_.suggested_buffer = static_cast<uint32_t>(table_width_ * table_height_ * 2);

  const uint16_t block_align = static_cast<uint16_t>(2 * info_.channels);
  audio_format_.assign(18, 0);  // with cbSize 0
  put16(audio_format_, 0, 1);   // PCM
  put16(audio_format_, 2, static_cast<uint16_t>(info_.channels));
  put32(audio_format_, 4, kAudioRate);
  put32(audio_format_, 8, kAudioRate * block_align);
  put16(audio_format_, 12, block_align);
  put16(audio_format_, 14, 16);
  audio_info_ = {};
  audio_info_.type = kAudsType;
  audio_info_.scale = block_align;
  audio_info_.rate = kAudioRate * block_align;
  audio_info_.sample_size = block_align;
  audio_info_.suggested_buffer = kAudioRate * block_align;
  audio_info_.length = static_cast<uint32_t>(std::lround(info_.seconds * kAudioRate));
}

int32_t HdMovieStandIn::read_audio(int32_t start, int32_t samples, void* buffer, int32_t bytes) {
  if (!buffer || bytes <= 0) return 0;
  auto* out = static_cast<uint8_t*>(buffer);
  std::memset(out, 0, static_cast<size_t>(bytes));
  if (!source_ || info_.channels <= 0) return 0;
  const size_t channels = static_cast<size_t>(info_.channels);
  const size_t block = 2 * channels;
  // The player reads its sound in order; a read further on skips ahead.
  while (audio_position_ < start) {
    const size_t skip = static_cast<size_t>(std::min<int64_t>(start - audio_position_, kAudioRate));
    discard_.resize(skip * channels);
    const size_t got = source_->read_pcm(discard_.data(), skip);
    audio_position_ += static_cast<int64_t>(skip);
    if (got < skip) break;  // past the sound's end: silence from here
  }
  // An earlier start than the position is never asked (the source can't go
  // back); it is served the next samples in order.
  const size_t wanted = std::min(static_cast<size_t>(samples < 0 ? 0 : samples), static_cast<size_t>(bytes) / block);
  size_t filled = 0;
  while (filled < wanted) {
    const size_t got = source_->read_pcm(reinterpret_cast<int16_t*>(out + filled * block), wanted - filled);
    if (got == 0) break;  // the rest stays silent
    filled += got;
  }
  audio_position_ += static_cast<int64_t>(wanted);
  return 0;
}

bool HdMovieStandIn::frame_at(double seconds, HdFrame* out) {
  if (!source_) return false;
  std::string reason;
  if (!failure_logged_ && source_->failed(&reason)) {
    failure_logged_ = true;
    if (log_) log_("mw3: hd movie " + name_ + ": decoding stopped (" + reason + "); holding the last picture");
  }
  HdFrame picked;
  if (source_->frame_at(seconds, &picked)) last_ = std::move(picked);
  if (!last_.serial) return false;
  *out = last_;
  return true;
}

}  // namespace mech3
