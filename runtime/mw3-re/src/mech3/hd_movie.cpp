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
  const std::string key = movie_shape_key(avi_path ? avi_path : "", 0, 0, 0);  // "name/0/0x0"
  return key.substr(0, key.find('/'));
}

bool hd_movie_table(const std::string& name, int* frames, int* width, int* height) {
  for (const std::string& line : movie_shape_table()) {
    // "intro/2737/640x480 0:79-400": the key's name, frames and size.
    const std::string key = line.substr(0, line.find(' '));
    const size_t first_slash = key.find('/');
    const size_t second_slash = key.find('/', first_slash + 1);
    if (first_slash == std::string::npos || second_slash == std::string::npos) continue;
    if (key.compare(0, first_slash, name) != 0 || first_slash != name.size()) continue;
    int table_width = 0, table_height = 0;
    const int table_frames = std::atoi(key.c_str() + first_slash + 1);
    if (std::sscanf(key.c_str() + second_slash + 1, "%dx%d", &table_width, &table_height) != 2) return false;
    *frames = table_frames, *width = table_width, *height = table_height;
    return table_frames > 0 && table_width > 0 && table_height > 0;
  }
  return false;
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
