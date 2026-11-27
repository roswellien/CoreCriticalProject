// The Media Foundation HD movie decoder (#559, mech3/hd_movie_mf.cpp) on a
// clip this check makes itself: 2 s of 320x240 H.264 at 24 frames a
// second, its top half white and bottom half black with the bottom right
// quarter red, and a 440 Hz AAC tone.
// Nothing is committed or downloaded; the clip is written to the temp
// folder and deleted. Returns 77 (CTest's skip) when this Windows can't
// encode H.264/AAC, so a missing encoder is reported as "not run".
#ifndef NOMINMAX
#define NOMINMAX  // std::min, not windows.h's macro
#endif
#include <windows.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <wrl/client.h>

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <set>
#include <string>
#include <vector>

#include "mech3/hd_movie.h"

namespace {

using Microsoft::WRL::ComPtr;

constexpr int kSkipped = 77;
constexpr UINT32 kWidth = 320, kHeight = 240, kFps = 24, kFrames = 48;
// Microsoft's AAC encoder takes only 44.1 or 48 kHz, so the made clip can't
// be 22050 Hz; that rate is checked on the real pack (the #559 runs).
constexpr UINT32 kAudioRate = 44100;
constexpr LONGLONG kFrameTime = 10'000'000 / kFps;  // 100 ns units

int failures = 0;
void expect(bool condition, const char* what) {
  if (condition) return;
  std::printf("  FAILED: %s\n", what);
  ++failures;
}

ComPtr<IMFMediaType> media_type(const GUID& major, const GUID& subtype) {
  ComPtr<IMFMediaType> type;
  MFCreateMediaType(&type);
  type->SetGUID(MF_MT_MAJOR_TYPE, major);
  type->SetGUID(MF_MT_SUBTYPE, subtype);
  return type;
}

ComPtr<IMFSample> sample_of(const std::vector<uint8_t>& bytes, LONGLONG time, LONGLONG duration) {
  ComPtr<IMFMediaBuffer> buffer;
  MFCreateMemoryBuffer(static_cast<DWORD>(bytes.size()), &buffer);
  BYTE* data = nullptr;
  buffer->Lock(&data, nullptr, nullptr);
  std::memcpy(data, bytes.data(), bytes.size());
  buffer->Unlock();
  buffer->SetCurrentLength(static_cast<DWORD>(bytes.size()));
  ComPtr<IMFSample> sample;
  MFCreateSample(&sample);
  sample->AddBuffer(buffer.Get());
  sample->SetSampleTime(time);
  sample->SetSampleDuration(duration);
  return sample;
}

// Writes the clip; false (with why) when this Windows can't encode it.
bool make_clip(const std::wstring& path, std::string* why) {
  ComPtr<IMFSinkWriter> writer;
  if (FAILED(MFCreateSinkWriterFromURL(path.c_str(), nullptr, nullptr, &writer)))
    return *why = "no MP4 sink writer", false;
  auto h264 = media_type(MFMediaType_Video, MFVideoFormat_H264);
  h264->SetUINT32(MF_MT_AVG_BITRATE, 800000);
  h264->SetUINT32(MF_MT_INTERLACE_MODE, MFVideoInterlace_Progressive);
  MFSetAttributeSize(h264.Get(), MF_MT_FRAME_SIZE, kWidth, kHeight);
  MFSetAttributeRatio(h264.Get(), MF_MT_FRAME_RATE, kFps, 1);
  MFSetAttributeRatio(h264.Get(), MF_MT_PIXEL_ASPECT_RATIO, 1, 1);
  DWORD video = 0, audio = 0;
  if (FAILED(writer->AddStream(h264.Get(), &video))) return *why = "no H.264 encoder", false;
  // NV12 in: the H.264 encoder's own input, so no converter is assumed.
  auto nv12 = media_type(MFMediaType_Video, MFVideoFormat_NV12);
  nv12->SetUINT32(MF_MT_INTERLACE_MODE, MFVideoInterlace_Progressive);
  MFSetAttributeSize(nv12.Get(), MF_MT_FRAME_SIZE, kWidth, kHeight);
  MFSetAttributeRatio(nv12.Get(), MF_MT_FRAME_RATE, kFps, 1);
  MFSetAttributeRatio(nv12.Get(), MF_MT_PIXEL_ASPECT_RATIO, 1, 1);
  if (FAILED(writer->SetInputMediaType(video, nv12.Get(), nullptr))) return *why = "no NV12 input to H.264", false;
  auto aac = media_type(MFMediaType_Audio, MFAudioFormat_AAC);
  aac->SetUINT32(MF_MT_AUDIO_BITS_PER_SAMPLE, 16);
  aac->SetUINT32(MF_MT_AUDIO_SAMPLES_PER_SECOND, kAudioRate);
  aac->SetUINT32(MF_MT_AUDIO_NUM_CHANNELS, 1);
  aac->SetUINT32(MF_MT_AUDIO_AVG_BYTES_PER_SECOND, 12000);
  if (FAILED(writer->AddStream(aac.Get(), &audio))) return *why = "no AAC encoder", false;
  auto pcm = media_type(MFMediaType_Audio, MFAudioFormat_PCM);
  pcm->SetUINT32(MF_MT_AUDIO_BITS_PER_SAMPLE, 16);
  pcm->SetUINT32(MF_MT_AUDIO_SAMPLES_PER_SECOND, kAudioRate);
  pcm->SetUINT32(MF_MT_AUDIO_NUM_CHANNELS, 1);
  pcm->SetUINT32(MF_MT_AUDIO_BLOCK_ALIGNMENT, 2);
  pcm->SetUINT32(MF_MT_AUDIO_AVG_BYTES_PER_SECOND, kAudioRate * 2);
  if (FAILED(writer->SetInputMediaType(audio, pcm.Get(), nullptr))) return *why = "no PCM input to AAC", false;
  if (FAILED(writer->BeginWriting())) return *why = "the sink writer would not start", false;

  // NV12: Y rows (white 235 above the middle, black 16 below), then chroma
  // at half size as U, V pairs: grey (128) except the bottom right quarter,
  // which is red (U 90, V 240), so red and blue can't be swapped unseen.
  std::vector<uint8_t> picture(kWidth * kHeight * 3 / 2, 128);
  for (UINT32 y = 0; y < kHeight; ++y)
    std::memset(&picture[y * kWidth], y < kHeight / 2 ? 235 : 16, kWidth);
  uint8_t* chroma = &picture[kWidth * kHeight];
  for (UINT32 chroma_row = kHeight / 4; chroma_row < kHeight / 2; ++chroma_row) {
    for (UINT32 pair = kWidth / 4; pair < kWidth / 2; ++pair) {
      chroma[chroma_row * kWidth + pair * 2 + 0] = 90;   // U
      chroma[chroma_row * kWidth + pair * 2 + 1] = 240;  // V
    }
  }
  for (UINT32 f = 0; f < kFrames; ++f)
    writer->WriteSample(video, sample_of(picture, f * kFrameTime, kFrameTime).Get());
  constexpr UINT32 kChunk = kAudioRate / 10;  // 0.1 s
  std::vector<uint8_t> tone(kChunk * 2);
  for (UINT32 chunk = 0; chunk < 20; ++chunk) {
    for (UINT32 i = 0; i < kChunk; ++i) {
      const double t = static_cast<double>(chunk * kChunk + i) / kAudioRate;
      const auto value = static_cast<int16_t>(8000 * std::sin(2 * 3.14159265358979 * 440 * t));
      std::memcpy(&tone[i * 2], &value, 2);
    }
    writer->WriteSample(audio, sample_of(tone, chunk * 1'000'000LL, 1'000'000LL).Get());
  }
  if (FAILED(writer->Finalize())) return *why = "the sink writer would not finish", false;
  return true;
}

// Opens the clip through the game's factory and checks what it gives.
void check_clip(const std::string& path) {
  auto source = mech3::default_hd_movie_factory()();
  mech3::HdMovieInfo info;
  std::string reason;
  expect(source->open(path, &info, &reason), "the made clip opens");
  if (!reason.empty()) std::printf("  reason: %s\n", reason.c_str());
  expect(info.width == static_cast<int>(kWidth) && info.height == static_cast<int>(kHeight), "its size");
  expect(std::fabs(info.seconds - 2.0) < 0.15, "about 2 s long");
  expect(info.audio_rate == static_cast<int>(kAudioRate) && info.channels == 1, "44100 Hz mono");

  std::set<uint64_t> serials;
  double last_pts = -1;
  bool rising = true, top_white = true, bottom_black = true, alpha_set = true, red_first = true;
  // Ask for each frame's time in turn, as the game would, waiting up to
  // 0.5 s each for the worker to have decoded that far.
  for (UINT32 step = 0; step < kFrames; ++step) {
    const double seconds = step / static_cast<double>(kFps) + 0.001;
    mech3::HdFrame frame;
    bool got_new = false;
    for (int wait = 0; wait < 100 && !got_new; ++wait) {
      got_new = source->frame_at(seconds, &frame) && !serials.count(frame.serial);
      if (!got_new) Sleep(5);
    }
    if (!got_new) continue;
    serials.insert(frame.serial);
    rising = rising && frame.pts > last_pts;
    last_pts = frame.pts;
    const uint8_t* top = frame.rgba->data() + 10 * frame.pitch + 4 * 10;
    const uint8_t* bottom = frame.rgba->data() + (kHeight - 10) * frame.pitch + 4 * 10;
    const uint8_t* red = frame.rgba->data() + (kHeight * 7 / 8) * frame.pitch + 4 * (kWidth * 7 / 8);
    top_white = top_white && top[1] > 200;  // green
    bottom_black = bottom_black && bottom[1] < 50;
    alpha_set = alpha_set && top[3] == 255;
    red_first = red_first && red[0] > 120 && red[2] < 60;  // R, G, B, A
    if (serials.size() == 1) std::printf("  red quarter: %u %u %u %u\n", red[0], red[1], red[2], red[3]);
  }
  std::printf("  %zu pictures decoded, last at %.3f s\n", serials.size(), last_pts);
  expect(serials.size() >= 40 && serials.size() <= kFrames + 2, "about 48 distinct pictures");
  expect(rising, "pictures in rising time");
  expect(top_white && bottom_black, "the top row first (not upside down)");
  expect(alpha_set, "opaque pixels");
  expect(red_first, "red in the first byte (RGBA, not BGRA)");

  std::vector<int16_t> sound(kAudioRate);
  size_t total = 0;
  for (size_t got; (got = source->read_pcm(sound.data(), sound.size())) > 0;) total += got;
  std::printf("  %zu sound frames\n", total);
  expect(total > kAudioRate * 2 * 9 / 10 && total < kAudioRate * 2 * 11 / 10, "about 2 s of sound");
  std::string failure;
  expect(!source->failed(&failure), "no decoding failure");
  source.reset();
  auto again = mech3::default_hd_movie_factory()();
  expect(again->open(path, &info, &reason), "it opens again after the first is closed");
}

// The temp folder can hold non-ASCII characters (an accented user name), so
// the path is converted properly rather than one character at a time.
std::string utf8_of(const std::wstring& wide) {
  const int length = WideCharToMultiByte(CP_UTF8, 0, wide.c_str(), -1, nullptr, 0, nullptr, nullptr);
  if (length <= 1) return std::string();
  std::string narrow(static_cast<size_t>(length), '\0');
  WideCharToMultiByte(CP_UTF8, 0, wide.c_str(), -1, &narrow[0], length, nullptr, nullptr);
  narrow.resize(static_cast<size_t>(length - 1));  // drop the terminator the call counts
  return narrow;
}

}  // namespace

int main() {
  wchar_t temp[MAX_PATH];
  GetTempPathW(MAX_PATH, temp);
  const std::wstring wide = std::wstring(temp) + L"mw3hd-" + std::to_wstring(GetCurrentProcessId()) + L".mp4";
  const std::string path = utf8_of(wide);  // the decoder takes UTF-8 paths
  CoInitializeEx(nullptr, COINIT_MULTITHREADED);
  MFStartup(MF_VERSION, MFSTARTUP_LITE);
  std::string why;
  const bool made = make_clip(wide, &why);
  MFShutdown();
  if (!made) {
    std::printf("mw3hd_movie_checks: not run: %s\n", why.c_str());
    DeleteFileW(wide.c_str());
    CoUninitialize();
    return kSkipped;
  }
  check_clip(path);
  DeleteFileW(wide.c_str());
  CoUninitialize();
  std::printf("mw3hd_movie_checks: %s\n", failures ? "FAILED" : "passed");
  return failures ? 1 : 0;
}
