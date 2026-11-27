// Ours (#559): HD movies decoded by Windows' Media Foundation (hd_movie.h,
// docs/fmv.md section 9). Two Source Readers on one local file: the sound,
// read on the game's thread as the movie player asks for it (an AAC second
// costs a few milliseconds), and the pictures, decoded and converted to
// 32-bit RGB on a thread of their own into a queue of at most three frames.
// Media Foundation ignores the MP4's edit lists, so the sound's is read from
// the file here and applied (mp4_sound_edit).
// Built on Windows only (CMakeLists.txt sets MW3_HD_MOVIE_MF); nothing here
// is downloaded or bundled: the decoders are Windows' own, and a Windows N
// edition without the Media Feature Pack is told so and plays the original.
#include "mech3/hd_movie.h"

#ifndef NOMINMAX
#define NOMINMAX  // std::min, not windows.h's macro
#endif
#include <windows.h>
#include <mfapi.h>
#include <mferror.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <wrl/client.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <thread>

namespace mech3 {

namespace {

using Microsoft::WRL::ComPtr;

std::string hresult_text(const char* what, HRESULT hr) {
  char text[96];
  std::snprintf(text, sizeof text, "%s failed (0x%08lx)", what, static_cast<unsigned long>(hr));
  return text;
}

// True when Windows has a decoder for `subtype` in `category` (a Windows N
// edition without the Media Feature Pack has neither H.264 nor AAC).
bool decoder_installed(const GUID& category, const GUID& major, const GUID& subtype) {
  MFT_REGISTER_TYPE_INFO input{major, subtype};
  IMFActivate** found = nullptr;
  UINT32 count = 0;
  const UINT32 flags = MFT_ENUM_FLAG_SYNCMFT | MFT_ENUM_FLAG_ASYNCMFT | MFT_ENUM_FLAG_HARDWARE |
                       MFT_ENUM_FLAG_SORTANDFILTER;
  if (FAILED(MFTEnumEx(category, flags, &input, nullptr, &found, &count))) return false;
  for (UINT32 i = 0; i < count; ++i) found[i]->Release();
  CoTaskMemFree(found);
  return count > 0;
}

// The option's path (UTF-8) as a wide path for the Windows calls; empty for
// bad UTF-8. Only local files: a URL scheme is refused, so the resolver
// never reaches the network.
std::wstring local_file_path(const std::string& path, std::string* reason) {
  if (path.find("://") != std::string::npos) return *reason = "it is not a local file", std::wstring();
  const int length = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, path.c_str(), -1, nullptr, 0);
  if (length <= 1) return *reason = "its path is not valid UTF-8", std::wstring();
  std::wstring wide(static_cast<size_t>(length), L'\0');
  MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, path.c_str(), -1, &wide[0], length);
  wide.resize(static_cast<size_t>(length - 1));
  const DWORD attributes = GetFileAttributesW(wide.c_str());
  if (attributes == INVALID_FILE_ATTRIBUTES || (attributes & FILE_ATTRIBUTE_DIRECTORY))
    return *reason = "the file is not there", std::wstring();
  return wide;
}

// The sound's edit list (hd_movie.h), read straight from the file: Media
// Foundation's timestamps don't carry it. Zeros if it can't be read.
Mp4SoundEdit read_sound_edit(const std::wstring& path) {
  const HANDLE file = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
                                  FILE_ATTRIBUTE_NORMAL, nullptr);
  if (file == INVALID_HANDLE_VALUE) return {};
  LARGE_INTEGER size{};
  Mp4SoundEdit edit;
  if (GetFileSizeEx(file, &size)) {
    const auto read_at = [file](uint64_t offset, void* out, size_t bytes) {
      OVERLAPPED where{};
      where.Offset = static_cast<DWORD>(offset);
      where.OffsetHigh = static_cast<DWORD>(offset >> 32);
      DWORD got = 0;
      return ReadFile(file, out, static_cast<DWORD>(bytes), &got, &where) && got == bytes;
    };
    edit = mp4_sound_edit(read_at, static_cast<uint64_t>(size.QuadPart));
  }
  CloseHandle(file);
  return edit;
}

constexpr DWORD kFirstAudio = static_cast<DWORD>(MF_SOURCE_READER_FIRST_AUDIO_STREAM);
constexpr DWORD kFirstVideo = static_cast<DWORD>(MF_SOURCE_READER_FIRST_VIDEO_STREAM);

class MfHdMovieSource : public HdMovieSource {
 public:
  ~MfHdMovieSource() override {
    queue_.stop();  // wakes the worker if it waits for space
    stopping_ = true;
    if (worker_.joinable()) worker_.join();
    video_.Reset();
    audio_.Reset();
    if (mf_started_) MFShutdown();
    if (com_owned_) CoUninitialize();
  }

  bool open(const std::string& path, HdMovieInfo* info, std::string* reason) override {
    // The game's thread may already have COM in another mode; Media
    // Foundation's objects are free-threaded, so that is fine too.
    const HRESULT com = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    if (com == S_OK || com == S_FALSE) com_owned_ = true;
    else if (com != RPC_E_CHANGED_MODE) return *reason = hresult_text("CoInitializeEx", com), false;
    HRESULT hr = MFStartup(MF_VERSION, MFSTARTUP_LITE);
    if (FAILED(hr)) return *reason = hresult_text("MFStartup", hr), false;
    mf_started_ = true;
    if (!decoder_installed(MFT_CATEGORY_VIDEO_DECODER, MFMediaType_Video, MFVideoFormat_H264) ||
        !decoder_installed(MFT_CATEGORY_AUDIO_DECODER, MFMediaType_Audio, MFAudioFormat_AAC))
      return *reason = "no H.264/AAC decoder (Windows N needs the Media Feature Pack)", false;
    const std::wstring wide = local_file_path(path, reason);
    if (wide.empty()) return false;
    if (!open_audio(wide, info, reason)) return false;
    if (!open_video(wide, info, reason)) return false;
    // The pack's AAC starts with 1024 priming samples (46 ms at 22050 Hz);
    // played, they put the sound behind the picture (#569's review). Its
    // last AAC frame is padded too (923 samples in INTRO), played after
    // the clip's end.
    const Mp4SoundEdit edit = read_sound_edit(wide);
    skip_sound_frames_ = static_cast<size_t>(std::llround(edit.start * info->audio_rate));
    if (edit.length > 0) sound_frames_left_ = static_cast<size_t>(std::llround(edit.length * info->audio_rate));
    PROPVARIANT duration;
    PropVariantInit(&duration);
    hr = audio_->GetPresentationAttribute(static_cast<DWORD>(MF_SOURCE_READER_MEDIASOURCE), MF_PD_DURATION,
                                          &duration);
    if (FAILED(hr) || duration.vt != VT_UI8) {
      PropVariantClear(&duration);
      return *reason = hresult_text("reading its length", hr), false;
    }
    info->seconds = static_cast<double>(duration.uhVal.QuadPart) / 1e7;  // 100 ns units
    PropVariantClear(&duration);
    return true;
  }

  size_t read_pcm(int16_t* out, size_t frames) override {
    const size_t channels = static_cast<size_t>(channels_ > 0 ? channels_ : 1);
    size_t given = 0;
    while (given < frames) {
      if (sound_frames_left_ == 0) break;  // the edit list's end: only padding is left
      if (leftover_at_ < leftover_.size()) {
        const size_t available = (leftover_.size() - leftover_at_) / channels;
        const size_t take = std::min({available, frames - given, sound_frames_left_});
        sound_frames_left_ -= take;
        std::memcpy(out + given * channels, &leftover_[leftover_at_], take * channels * sizeof(int16_t));
        leftover_at_ += take * channels;
        given += take;
        continue;
      }
      if (sound_ended_ || !next_audio_sample()) break;
    }
    return given;
  }

  bool frame_at(double seconds, HdFrame* out) override {
    if (!worker_started_ && video_) {
      worker_started_ = true;  // not at open: validate() at the script's load decodes nothing
      worker_ = std::thread([this] { decode_pictures(); });
    }
    return queue_.pick(seconds, out);
  }

  bool failed(std::string* reason) override {
    std::lock_guard<std::mutex> lock(failure_mutex_);
    if (failure_.empty()) return false;
    *reason = failure_;
    return true;
  }

 private:
  bool open_audio(const std::wstring& path, HdMovieInfo* info, std::string* reason) {
    HRESULT hr = MFCreateSourceReaderFromURL(path.c_str(), nullptr, &audio_);
    if (FAILED(hr)) return *reason = hresult_text("opening it", hr), false;
    audio_->SetStreamSelection(static_cast<DWORD>(MF_SOURCE_READER_ALL_STREAMS), FALSE);
    if (FAILED(audio_->SetStreamSelection(kFirstAudio, TRUE))) {
      info->channels = 0;  // HdMovieStandIn refuses a clip with no sound
      sound_ended_ = true;
      return true;
    }
    UINT32 file_rate = 0;
    ComPtr<IMFMediaType> native;
    if (SUCCEEDED(audio_->GetNativeMediaType(kFirstAudio, 0, &native)))
      file_rate = MFGetAttributeUINT32(native.Get(), MF_MT_AUDIO_SAMPLES_PER_SECOND, 0);
    // The file's own rate asked for first; without it Windows' AAC decoder
    // gives a 22050 Hz AAC-LC stream at 44100 (it allows for HE-AAC's hidden
    // second layer), which is then halved here (next_audio_sample).
    hr = E_FAIL;
    for (const bool ask_file_rate : {true, false}) {
      if (ask_file_rate && !file_rate) continue;
      ComPtr<IMFMediaType> pcm;
      MFCreateMediaType(&pcm);
      pcm->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Audio);
      pcm->SetGUID(MF_MT_SUBTYPE, MFAudioFormat_PCM);
      pcm->SetUINT32(MF_MT_AUDIO_BITS_PER_SAMPLE, 16);
      if (ask_file_rate) pcm->SetUINT32(MF_MT_AUDIO_SAMPLES_PER_SECOND, file_rate);
      hr = audio_->SetCurrentMediaType(kFirstAudio, nullptr, pcm.Get());
      if (SUCCEEDED(hr)) break;
    }
    if (FAILED(hr)) return *reason = hresult_text("decoding its sound", hr), false;
    ComPtr<IMFMediaType> actual;
    hr = audio_->GetCurrentMediaType(kFirstAudio, &actual);
    if (FAILED(hr)) return *reason = hresult_text("reading its sound format", hr), false;
    channels_ = static_cast<int>(MFGetAttributeUINT32(actual.Get(), MF_MT_AUDIO_NUM_CHANNELS, 0));
    const UINT32 decoded_rate = MFGetAttributeUINT32(actual.Get(), MF_MT_AUDIO_SAMPLES_PER_SECOND, 0);
    halve_rate_ = file_rate && decoded_rate == 2 * file_rate;
    info->channels = channels_;
    info->audio_rate = static_cast<int>(halve_rate_ ? file_rate : decoded_rate);
    return true;
  }

  bool open_video(const std::wstring& path, HdMovieInfo* info, std::string* reason) {
    ComPtr<IMFAttributes> attributes;
    MFCreateAttributes(&attributes, 1);
    // The reader's own YUV -> RGB32 conversion (software). Measured in the
    // #559 runs; NV12 and a shader are the follow-up if it is too slow.
    attributes->SetUINT32(MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING, TRUE);
    // Without MF_LOW_LATENCY the H.264 decoder holds about 95 MB more (seen
    // on INTRO), over #559's budget. With it, the pictures still come in
    // order with the right durations, but the timestamps are wrong for
    // B-frames (the second picture is stamped 0, the first 0.083 s), so
    // decode_pictures times them by their durations instead.
    attributes->SetUINT32(MF_LOW_LATENCY, TRUE);
    HRESULT hr = MFCreateSourceReaderFromURL(path.c_str(), attributes.Get(), &video_);
    if (FAILED(hr)) return *reason = hresult_text("opening its picture", hr), false;
    video_->SetStreamSelection(static_cast<DWORD>(MF_SOURCE_READER_ALL_STREAMS), FALSE);
    if (FAILED(video_->SetStreamSelection(kFirstVideo, TRUE))) return *reason = "it has no picture", false;
    ComPtr<IMFMediaType> rgb;
    MFCreateMediaType(&rgb);
    rgb->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video);
    rgb->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_RGB32);
    hr = video_->SetCurrentMediaType(kFirstVideo, nullptr, rgb.Get());
    if (FAILED(hr)) return *reason = hresult_text("decoding its picture", hr), false;
    if (!read_picture_format()) return *reason = "its picture format could not be read", false;
    info->width = width_, info->height = height_;
    return true;
  }

  // The picture's size and row step from the reader's current type. A
  // negative step is a bottom-up picture (MF's rule for RGB without a
  // MF_MT_DEFAULT_STRIDE).
  bool read_picture_format() {
    ComPtr<IMFMediaType> actual;
    if (FAILED(video_->GetCurrentMediaType(kFirstVideo, &actual))) return false;
    UINT32 width = 0, height = 0;
    if (FAILED(MFGetAttributeSize(actual.Get(), MF_MT_FRAME_SIZE, &width, &height))) return false;
    UINT32 stride = 0;
    LONG default_stride = 0;
    if (SUCCEEDED(actual->GetUINT32(MF_MT_DEFAULT_STRIDE, &stride))) default_stride = static_cast<LONG>(stride);
    else if (FAILED(MFGetStrideForBitmapInfoHeader(MFVideoFormat_RGB32.Data1, width, &default_stride))) return false;
    width_ = static_cast<int>(width), height_ = static_cast<int>(height), default_stride_ = default_stride;
    UINT32 rate_numerator = 0, rate_denominator = 0;
    if (SUCCEEDED(MFGetAttributeRatio(actual.Get(), MF_MT_FRAME_RATE, &rate_numerator, &rate_denominator)) &&
        rate_numerator > 0)
      frame_duration_ = static_cast<LONGLONG>(10000000.0 * rate_denominator / rate_numerator);
    return width_ > 0 && height_ > 0;
  }

  // One more decoded sound sample into `leftover_`; false at the end or on
  // an error (the rest of the movie is then silent).
  bool next_audio_sample() {
    DWORD flags = 0;
    LONGLONG timestamp = 0;
    ComPtr<IMFSample> sample;
    const HRESULT hr = audio_->ReadSample(kFirstAudio, 0, nullptr, &flags, &timestamp, &sample);
    if (FAILED(hr) || (flags & MF_SOURCE_READERF_ERROR)) {
      record_failure(hresult_text("reading its sound", hr));
      return sound_ended_ = true, false;
    }
    if (flags & MF_SOURCE_READERF_ENDOFSTREAM) return sound_ended_ = true, false;
    leftover_.clear();
    leftover_at_ = 0;
    if (!sample) return true;
    ComPtr<IMFMediaBuffer> buffer;
    if (FAILED(sample->ConvertToContiguousBuffer(&buffer))) return true;
    BYTE* data = nullptr;
    DWORD length = 0;
    if (FAILED(buffer->Lock(&data, nullptr, &length))) return true;
    leftover_.resize(length / sizeof(int16_t));
    std::memcpy(leftover_.data(), data, leftover_.size() * sizeof(int16_t));
    buffer->Unlock();
    if (halve_rate_) halve(&leftover_);
    if (skip_sound_frames_ > 0) {  // the encoder's priming, never heard
      const size_t channels = static_cast<size_t>(channels_ > 0 ? channels_ : 1);
      const size_t skipped = std::min(skip_sound_frames_, leftover_.size() / channels);
      leftover_at_ = skipped * channels;
      skip_sound_frames_ -= skipped;
    }
    return true;
  }

  // The decoder's doubled rate back to the file's: each pair of sample frames
  // averaged into one (a frame left over waits for the next sample). An
  // AAC-LC stream at 22050 Hz holds nothing above 11 kHz, so the doubling
  // added no sound there; averaging dulls only its top octave slightly.
  void halve(std::vector<int16_t>* samples) {
    const size_t channels = static_cast<size_t>(channels_ > 0 ? channels_ : 1);
    std::vector<int16_t> joined(halve_carry_);
    joined.insert(joined.end(), samples->begin(), samples->end());
    const size_t frames = joined.size() / channels;
    const size_t pairs = frames / 2;
    samples->resize(pairs * channels);
    for (size_t pair = 0; pair < pairs; ++pair)
      for (size_t c = 0; c < channels; ++c) {
        const int first = joined[(2 * pair) * channels + c], second = joined[(2 * pair + 1) * channels + c];
        (*samples)[pair * channels + c] = static_cast<int16_t>((first + second) / 2);
      }
    halve_carry_.assign(joined.begin() + static_cast<std::ptrdiff_t>(2 * pairs * channels), joined.end());
  }

  // The worker: every picture, decoded in order, copied top row first with
  // its alpha set, into the queue (which waits while it is full).
  void decode_pictures() {
    const HRESULT com = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    uint64_t serial = 0;
    while (!stopping_) {
      DWORD flags = 0;
      LONGLONG timestamp = 0;
      ComPtr<IMFSample> sample;
      const HRESULT hr = video_->ReadSample(kFirstVideo, 0, nullptr, &flags, &timestamp, &sample);
      if (FAILED(hr) || (flags & MF_SOURCE_READERF_ERROR)) {
        record_failure(hresult_text("reading its picture", hr));
        break;
      }
      if (flags & MF_SOURCE_READERF_ENDOFSTREAM) break;
      if (flags & MF_SOURCE_READERF_CURRENTMEDIATYPECHANGED) {
        const int old_width = width_, old_height = height_;
        if (!read_picture_format() || width_ != old_width || height_ != old_height) {
          record_failure("its picture changed size part way through");
          break;
        }
      }
      if (!sample) continue;
      // The picture's time: the durations of those before it, from 0 (see
      // open_video), counted even for a picture that can't be copied.
      // Media Foundation's own stamps also leave out the MP4 edit list,
      // which for these clips is the same B-frame delay.
      LONGLONG duration = 0;
      if (FAILED(sample->GetSampleDuration(&duration)) || duration <= 0) duration = frame_duration_;
      const LONGLONG picture_time = picture_clock_;
      picture_clock_ += duration;
      HdFrame frame;
      if (!copy_picture(sample.Get(), &frame)) continue;
      frame.pts = static_cast<double>(picture_time) / 1e7;
      frame.serial = ++serial;
      if (!queue_.push(std::move(frame))) break;  // stopped
    }
    if (com == S_OK || com == S_FALSE) CoUninitialize();
  }

  bool copy_picture(IMFSample* sample, HdFrame* frame) {
    ComPtr<IMFMediaBuffer> buffer;
    if (FAILED(sample->ConvertToContiguousBuffer(&buffer))) return false;
    const size_t row_bytes = static_cast<size_t>(width_) * 4;
    auto pixels = std::make_shared<std::vector<uint8_t>>(row_bytes * height_);
    ComPtr<IMF2DBuffer> two_d;
    BYTE* first_row = nullptr;
    LONG pitch = 0;
    bool locked_2d = false;
    BYTE* data = nullptr;
    if (SUCCEEDED(buffer.As(&two_d)) && SUCCEEDED(two_d->Lock2D(&first_row, &pitch))) {
      locked_2d = true;  // the buffer's own top row and step
    } else {
      DWORD length = 0;
      if (FAILED(buffer->Lock(&data, nullptr, &length))) return false;
      const size_t needed = static_cast<size_t>(std::abs(default_stride_)) * height_;
      if (length < needed) {
        buffer->Unlock();
        return false;
      }
      pitch = default_stride_;
      first_row = default_stride_ < 0 ? data + static_cast<size_t>(-default_stride_) * (height_ - 1) : data;
    }
    for (int y = 0; y < height_; ++y) {
      const BYTE* source_row = first_row + static_cast<ptrdiff_t>(pitch) * y;
      uint8_t* row = pixels->data() + row_bytes * y;
      std::memcpy(row, source_row, row_bytes);
      for (size_t x = 3; x < row_bytes; x += 4) row[x] = 0xff;  // RGB32's fourth byte is undefined
    }
    if (locked_2d) two_d->Unlock2D();
    else buffer->Unlock();
    frame->bgra = std::move(pixels);
    frame->width = width_, frame->height = height_, frame->pitch = static_cast<int>(row_bytes);
    return true;
  }

  void record_failure(const std::string& reason) {
    std::lock_guard<std::mutex> lock(failure_mutex_);
    if (failure_.empty()) failure_ = reason;
  }

  bool com_owned_ = false, mf_started_ = false;
  ComPtr<IMFSourceReader> audio_, video_;
  int channels_ = 0;
  bool sound_ended_ = false;
  bool halve_rate_ = false;           // the decoder gives twice the file's rate
  std::vector<int16_t> halve_carry_;  // a sample frame waiting for its pair
  std::vector<int16_t> leftover_;  // decoded sound not yet handed out
  size_t leftover_at_ = 0;
  size_t skip_sound_frames_ = 0;  // priming sample frames still to drop
  // Sample frames still to hand out before the edit list's end; no limit
  // without one.
  size_t sound_frames_left_ = std::numeric_limits<size_t>::max();
  LONGLONG picture_clock_ = 0;    // the next picture's time, 100 ns units (worker only)
  LONGLONG frame_duration_ = 0;   // from the frame rate, for a picture without a duration
  int width_ = 0, height_ = 0;
  LONG default_stride_ = 0;
  HdFrameQueue queue_;
  std::thread worker_;
  bool worker_started_ = false;
  std::atomic<bool> stopping_{false};
  std::mutex failure_mutex_;
  std::string failure_;
};

}  // namespace

HdMovieFactory default_hd_movie_factory() {
  return [] { return std::make_unique<MfHdMovieSource>(); };
}

}  // namespace mech3
