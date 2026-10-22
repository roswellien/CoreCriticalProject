#pragma once
// Local red-book-audio replacement. The original game still chooses tracks and sends
// MCI commands. Only the CD device is supplied here; movie MCI devices are unrelated.
// Prepared PCM is immutable. All WaveOut calls and PCM gain arithmetic run on one
// native worker, outside the guest's x87 environment. No host mixer levels are changed.
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#include <mmsystem.h>

#include <algorithm>
#include <array>
#include <condition_variable>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <filesystem>
#include <fstream>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace mw34::audio {
// Native replacement for the game's CD-audio device, not a general MCI driver.
// Construction owns loading and worker startup; send() marshals native parameters
// into requests, and the worker exclusively owns playback and notification state.
class LocalCdAudio {
    using U64 = std::uint64_t;
    static constexpr unsigned sample_rate = 44100, channels = 2, bytes_per_sample_frame = 4,
                              samples_per_cd_frame = 588;
    static constexpr unsigned sample_frames_per_buffer = 441, output_buffer_count = 4;
    struct Track {
        // start/frames are stereo PCM sample frames, not interleaved sample counts
        // or CD sectors. One CD frame is samples_per_cd_frame (588) PCM frames.
        unsigned number{};
        U64 start{}, frames{};
    };
    struct OutputSlot {
        WAVEHDR header{};
        std::array<std::int16_t, sample_frames_per_buffer * channels> pcm{};
        U64 end{}, nonzero{};
        bool prepared{}, queued{};
    };
    struct Output {
        HWAVEOUT wave{};
        HANDLE event{};
        std::array<OutputSlot, output_buffer_count> slots{};
        ~Output() {
            if (event)
                ::CloseHandle(event);
        }
    };
    struct Request {
        enum Kind { Command, GetVolume, SetVolume, Shutdown } kind = Command;
        UINT dev{}, msg{};
        DWORD flags{}, value{}, from{}, to{}, item{}, track{}, format{};
        DWORD_PTR callback{};
        MCIERROR result{};
        DWORD_PTR answer{};
        bool done{};
        std::mutex mutex;
        std::condition_variable ready;
    };
    using RequestPtr = std::shared_ptr<Request>;
    std::vector<std::int16_t> pcm_;
    std::array<Track, 2> tracks_{};
    U64 total_{};
    bool enabled_{};
    HANDLE control_{};
    std::thread worker_;
    std::mutex queue_mutex_;
    std::deque<RequestPtr> queue_;
    FILE *log_{};
    // Worker-owned state. Public methods communicate exclusively through requests.
    std::unique_ptr<Output> output_;
    bool opened_{};
    DWORD mode_ = MCI_MODE_STOP, time_format_ = MCI_FORMAT_MSF, volume_ = 0xffffffffU;
    U64 cursor_{}, play_base_{}, play_end_{}, submitted_{}, completed_{};
    DWORD_PTR pending_notify_{};
    RequestPtr wait_play_;
    MCIERROR fault_{};
    U64 queued_nonzero_{}, played_nonzero_{};
    unsigned audits_{};

    static std::uint16_t u16(const std::vector<unsigned char> &b, std::size_t at) {
        if (at > b.size() || b.size() - at < 2)
            throw std::runtime_error("Local CD: truncated u16");
        return std::uint16_t(b[at]) | std::uint16_t(b[at + 1]) << 8;
    }
    static std::uint32_t u32(const std::vector<unsigned char> &b, std::size_t at) {
        if (at > b.size() || b.size() - at < 4)
            throw std::runtime_error("Local CD: truncated u32");
        return std::uint32_t(u16(b, at)) | std::uint32_t(u16(b, at + 2)) << 16;
    }
    static U64 u64(const std::vector<unsigned char> &b, std::size_t at) {
        return U64(u32(b, at)) | U64(u32(b, at + 4)) << 32;
    }
    static std::vector<unsigned char> file_bytes(const std::filesystem::path &p,
                                                 std::size_t limit) {
        std::ifstream f(p, std::ios::binary | std::ios::ate);
        if (!f)
            throw std::runtime_error("Local CD: cannot open prepared music file");
        const auto end = f.tellg();
        if (end < 0 || U64(end) > limit)
            throw std::runtime_error("Local CD: music file outside size limit");
        std::vector<unsigned char> b(static_cast<std::size_t>(end));
        f.seekg(0);
        if (!b.empty() && !f.read(reinterpret_cast<char *>(b.data()), std::streamsize(b.size())))
            throw std::runtime_error("Local CD: incomplete file read");
        return b;
    }
    static std::filesystem::path utf8_path(const std::string &s) {
        if (s.empty() || s.find('\0') != std::string::npos)
            throw std::runtime_error("Local CD: empty or embedded-NUL path");
        const int n = ::MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, s.data(), int(s.size()),
                                            nullptr, 0);
        if (!n)
            throw std::runtime_error("Local CD: invalid UTF-8 path");
        std::wstring w(std::size_t(n), L'\0');
        if (::MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, s.data(), int(s.size()), w.data(),
                                  n) != n)
            throw std::runtime_error("Local CD: UTF-8 path conversion failed");
        return std::filesystem::path(w);
    }
    static std::filesystem::path environment_path(const char *name) {
        const char *p = std::getenv(name);
        return p && *p ? utf8_path(p) : std::filesystem::path{};
    }
    void load(const std::filesystem::path &manifest) {
        // MW3CD1 contains exactly the two audio tracks, numbered 2 and 3.
        // Track 1 is the original disc's data track and has no PCM payload here.
        const auto b = file_bytes(manifest, 2 * 1024 * 1024);
        const unsigned char magic[8] = {'M', 'W', '3', 'C', 'D', '1', 0, 0};
        if (b.size() < 16 || std::memcmp(b.data(), magic, 8) || u32(b, 8) != 1 || u32(b, 12) != 2)
            throw std::runtime_error("Local CD: unsupported music manifest");
        std::size_t at = 16;
        for (unsigned i = 0; i < 2; ++i) {
            if (at > b.size() || b.size() - at < 28)
                throw std::runtime_error("Local CD: truncated track record");
            const auto track = u32(b, at), sr = u32(b, at + 4), ch = u32(b, at + 8),
                       bits = u32(b, at + 12);
            const U64 frames = u64(b, at + 16);
            const auto len = u32(b, at + 24);
            at += 28;
            if (track != i + 2 || sr != sample_rate || ch != channels || bits != 16 || !frames ||
                frames > 0x7fffffffULL / bytes_per_sample_frame || !len || len > 32768 ||
                len > b.size() - at)
                throw std::runtime_error("Local CD: invalid track metadata");
            const auto path =
                utf8_path(std::string(reinterpret_cast<const char *>(b.data() + at), len));
            at += len;
            if (!path.is_absolute())
                throw std::runtime_error("Local CD: prepared WAV path must be absolute");
            const auto wav = file_bytes(path, 0x7fffffffU);
            // Preparation emits a canonical 44-byte PCM WAV header. Arbitrary
            // RIFF chunk ordering, compressed WAV and extra chunks are rejected.
            if (wav.size() != 44 + frames * bytes_per_sample_frame ||
                std::memcmp(wav.data(), "RIFF", 4) || u32(wav, 4) != wav.size() - 8 ||
                std::memcmp(wav.data() + 8, "WAVEfmt ", 8) || u32(wav, 16) != 16 ||
                u16(wav, 20) != WAVE_FORMAT_PCM || u16(wav, 22) != channels ||
                u32(wav, 24) != sample_rate ||
                u32(wav, 28) != sample_rate * bytes_per_sample_frame ||
                u16(wav, 32) != bytes_per_sample_frame || u16(wav, 34) != 16 ||
                std::memcmp(wav.data() + 36, "data", 4) ||
                u32(wav, 40) != frames * bytes_per_sample_frame)
                throw std::runtime_error("Local CD: WAV does not match canonical PCM manifest");
            tracks_[i] = {track, total_, frames};
            const std::size_t start = pcm_.size();
            pcm_.resize(start + std::size_t(frames) * channels);
            std::memcpy(pcm_.data() + start, wav.data() + 44,
                        std::size_t(frames) * bytes_per_sample_frame);
            total_ += frames;
        }
        if (at != b.size())
            throw std::runtime_error("Local CD: trailing manifest data");
        enabled_ = true;
    }
    void trace(const char *what, unsigned a = 0, U64 b = 0) {
        if (log_) {
            std::fprintf(log_, "%llu %s %u %llu\n", ::GetTickCount64(), what, a,
                         static_cast<unsigned long long>(b));
            std::fflush(log_);
        }
    }
    void audit(const char *reason) {
        if (log_ && audits_++ < 128) {
            std::fprintf(
                log_,
                "%llu audio-state %s mode=%lu gain=%08lx base=%llu cursor=%llu submitted=%llu "
                "completed=%llu queued_nonzero_frames=%llu completed_nonzero_frames=%llu\n",
                ::GetTickCount64(), reason, mode_, volume_,
                static_cast<unsigned long long>(play_base_),
                static_cast<unsigned long long>(cursor_),
                static_cast<unsigned long long>(submitted_),
                static_cast<unsigned long long>(completed_),
                static_cast<unsigned long long>(queued_nonzero_),
                static_cast<unsigned long long>(played_nonzero_));
            std::fflush(log_);
        }
    }
    MCIERROR hardware(const char *where, MMRESULT r) {
        if (!r)
            return 0;
        trace(where, r);
        std::fprintf(stderr, "Local CD audio: %s failed (%u)\n", where, r);
        return MCIERR_HARDWARE;
    }
    void complete(const RequestPtr &r, MCIERROR result, DWORD_PTR answer = 0) {
        std::lock_guard lock(r->mutex);
        r->result = result;
        r->answer = answer;
        r->done = true;
        r->ready.notify_one();
    }
    MCIERROR invoke(const RequestPtr &r) {
        // Callers wait for request completion, not necessarily playback completion.
        // MCI_WAIT play requests remain pending until the worker drains or aborts
        // their selected range. The shared request outlives this queue transfer.
        if (!enabled_)
            return MCIERR_DEVICE_NOT_INSTALLED;
        {
            std::lock_guard lock(queue_mutex_);
            queue_.push_back(r);
            if (!::SetEvent(control_)) {
                queue_.pop_back();
                return MCIERR_HARDWARE;
            }
        }
        std::unique_lock lock(r->mutex);
        r->ready.wait(lock, [&] { return r->done; });
        return r->result;
    }
    static bool flags_allowed(DWORD actual, DWORD allowed) {
        return (actual & ~allowed) == 0 &&
               ((actual & (MCI_WAIT | MCI_NOTIFY)) != (MCI_WAIT | MCI_NOTIFY));
    }
    static bool callback_valid(const Request &r) {
        return !(r.flags & MCI_NOTIFY) ||
               (r.callback && ::IsWindow(reinterpret_cast<HWND>(r.callback)));
    }
    void notify(DWORD_PTR callback, unsigned reason) {
        if (!callback)
            return;
        trace("notify", reason, callback);
        if (!::PostMessageA(reinterpret_cast<HWND>(callback), MM_MCINOTIFY, reason, device_id)) {
            trace("notify-post-failed", ::GetLastError());
            std::fprintf(stderr, "Local CD audio: MM_MCINOTIFY delivery failed\n");
            fault_ = MCIERR_NO_WINDOW;
        }
    }
    void cancel_pending(unsigned reason) {
        const auto cb = pending_notify_;
        pending_notify_ = 0;
        notify(cb, reason);
    }
    void finish_wait(MCIERROR error) {
        if (wait_play_) {
            const auto r = std::move(wait_play_);
            complete(r, error);
        }
    }
    void install_notification(const Request &r, bool prevents_old, bool async) {
        // Changing the play range aborts its notification; a new notification
        // on the same range supersedes the old one. Ordinary synchronous commands
        // report success immediately instead of waiting for WaveOut completion.
        if (pending_notify_ && (prevents_old || (r.flags & MCI_NOTIFY)))
            cancel_pending(prevents_old ? MCI_NOTIFY_ABORTED : MCI_NOTIFY_SUPERSEDED);
        if (r.flags & MCI_NOTIFY) {
            if (async)
                pending_notify_ = r.callback;
            else
                notify(r.callback, MCI_NOTIFY_SUCCESSFUL);
        }
    }
    void failed_play(MCIERROR error) {
        fault_ = error;
        mode_ = MCI_MODE_STOP;
        cancel_pending(MCI_NOTIFY_FAILURE);
        finish_wait(error);
    }
    void reap() {
        // Submitted buffers still belong to the device until WHDR_DONE. Advance
        // completed_ only from returned buffers and finish a range only after
        // every queued buffer drains, including its final partial buffer.
        if (!output_)
            return;
        bool queued = false;
        for (auto &s : output_->slots) {
            if (s.queued && (s.header.dwFlags & WHDR_DONE)) {
                completed_ = std::max(completed_, s.end);
                played_nonzero_ += s.nonzero;
                s.queued = false;
            }
            queued |= s.queued;
        }
        if (mode_ == MCI_MODE_PLAY && submitted_ == play_end_ && !queued) {
            cursor_ = play_end_;
            mode_ = MCI_MODE_STOP;
            trace("play-complete", device_id, cursor_);
            audit("complete");
            cancel_pending(MCI_NOTIFY_SUCCESSFUL);
            finish_wait(0);
        }
    }
    MCIERROR position() {
        reap();
        if (!output_ || mode_ == MCI_MODE_STOP)
            return 0;
        MMTIME t{};
        t.wType = TIME_SAMPLES;
        const auto e =
            hardware("waveOutGetPosition", ::waveOutGetPosition(output_->wave, &t, sizeof t));
        if (e)
            return e;
        U64 offset{};
        if (t.wType == TIME_SAMPLES)
            offset = t.u.sample;
        else if (t.wType == TIME_BYTES)
            offset = t.u.cb / bytes_per_sample_frame;
        else if (t.wType == TIME_MS)
            offset = U64(t.u.ms) * sample_rate / 1000;
        else {
            trace("unsupported-position-format", t.wType);
            return MCIERR_HARDWARE;
        }
        // WaveOut position is relative to its last reset, while cursor_ uses the
        // concatenated track timeline. Bound it by completed data and play end.
        cursor_ = std::min(play_end_, std::max(completed_, play_base_ + offset));
        return 0;
    }
    MCIERROR reset() {
        if (!output_)
            return 0;
        const auto e = hardware("waveOutReset", ::waveOutReset(output_->wave));
        if (e)
            return e;
        for (auto &s : output_->slots)
            s.queued = false;
        submitted_ = completed_ = cursor_;
        return 0;
    }
    MCIERROR close_output() {
        // Driver ownership ends in order: reset pending playback, unprepare each
        // header, close the device, then release buffers and the callback event.
        if (!output_) {
            opened_ = false;
            return 0;
        }
        const auto e = reset();
        if (e)
            return e;
        for (auto &s : output_->slots)
            if (s.prepared) {
                const auto r =
                    hardware("waveOutUnprepareHeader",
                             ::waveOutUnprepareHeader(output_->wave, &s.header, sizeof s.header));
                if (r)
                    return r;
                s.prepared = false;
            }
        const auto r = hardware("waveOutClose", ::waveOutClose(output_->wave));
        if (r)
            return r;
        output_->wave = nullptr;
        output_.reset();
        opened_ = false;
        mode_ = MCI_MODE_STOP;
        return 0;
    }
    MCIERROR open_output() {
        if (opened_)
            return MCIERR_DEVICE_OPEN;
        if (output_)
            return MCIERR_HARDWARE;
        output_ = std::make_unique<Output>();
        output_->event = ::CreateEventW(nullptr, FALSE, FALSE, nullptr);
        if (!output_->event) {
            output_.reset();
            return MCIERR_OUT_OF_MEMORY;
        }
        WAVEFORMATEX fmt{WAVE_FORMAT_PCM,
                         channels,
                         sample_rate,
                         sample_rate * bytes_per_sample_frame,
                         bytes_per_sample_frame,
                         16,
                         0};
        const auto r =
            ::waveOutOpen(&output_->wave, WAVE_MAPPER, &fmt,
                          reinterpret_cast<DWORD_PTR>(output_->event), 0, CALLBACK_EVENT);
        if (r) {
            hardware("waveOutOpen", r);
            output_.reset();
            return MCIERR_HARDWARE;
        }
        for (auto &s : output_->slots) {
            s.header.lpData = reinterpret_cast<LPSTR>(s.pcm.data());
            s.header.dwBufferLength = sizeof(s.pcm);
            const auto e =
                hardware("waveOutPrepareHeader",
                         ::waveOutPrepareHeader(output_->wave, &s.header, sizeof s.header));
            if (e) {
                close_output();
                return e;
            }
            s.prepared = true;
        }
        opened_ = true;
        cursor_ = play_base_ = submitted_ = completed_ = 0;
        play_end_ = total_;
        mode_ = MCI_MODE_STOP;
        time_format_ = MCI_FORMAT_MSF;
        fault_ = 0;
        trace("open", device_id, total_);
        return 0;
    }
    MCIERROR fill() {
        // Reuse only returned slots. Apply this service's stereo gain while
        // copying immutable source PCM; a volume change affects future fills,
        // never another application's mixer or already queued samples.
        reap();
        if (!output_ || mode_ != MCI_MODE_PLAY)
            return 0;
        for (auto &s : output_->slots)
            if (!s.queued && submitted_ < play_end_) {
                const unsigned n =
                    unsigned(std::min<U64>(sample_frames_per_buffer, play_end_ - submitted_));
                const unsigned left = volume_ & 65535, right = volume_ >> 16;
                U64 nonzero{};
                for (unsigned i = 0; i < n; ++i) {
                    const auto from = std::size_t(submitted_ + i) * channels;
                    s.pcm[i * 2] =
                        std::int16_t(std::int32_t(pcm_[from]) * std::int32_t(left) / 65535);
                    s.pcm[i * 2 + 1] =
                        std::int16_t(std::int32_t(pcm_[from + 1]) * std::int32_t(right) / 65535);
                    if (s.pcm[i * 2] || s.pcm[i * 2 + 1])
                        ++nonzero;
                }
                s.header.dwBufferLength = n * bytes_per_sample_frame;
                s.end = submitted_ + n;
                const auto e = hardware("waveOutWrite",
                                        ::waveOutWrite(output_->wave, &s.header, sizeof s.header));
                if (e)
                    return e;
                s.queued = true;
                s.nonzero = nonzero;
                queued_nonzero_ += nonzero;
                submitted_ = s.end;
            }
        return 0;
    }
    const Track &track_at(U64 sample) const {
        return sample < tracks_[1].start ? tracks_[0] : tracks_[1];
    }
    bool decode_position(DWORD v, bool endpoint, U64 &sample) const {
        // MCI addresses use 75 CD frames per second; playback counts stereo PCM
        // frames at 44.1 kHz. Track 4 at zero is accepted only as an end sentinel
        // after audio track 3, not as another playable track.
        if (time_format_ == MCI_FORMAT_TMSF) {
            const auto t = MCI_TMSF_TRACK(v), m = MCI_TMSF_MINUTE(v), s = MCI_TMSF_SECOND(v),
                       f = MCI_TMSF_FRAME(v);
            if (s >= 60 || f >= 75)
                return false;
            if (t == 4 && endpoint && !m && !s && !f) {
                sample = total_;
                return true;
            }
            if (t < 2 || t > 3)
                return false;
            const auto &tr = tracks_[t - 2];
            const U64 offset = (U64(m) * 60 * 75 + U64(s) * 75 + f) * samples_per_cd_frame;
            if (offset > tr.frames)
                return false;
            sample = tr.start + offset;
            return sample <= total_;
        }
        if (time_format_ == MCI_FORMAT_MSF) {
            const auto m = MCI_MSF_MINUTE(v), s = MCI_MSF_SECOND(v), f = MCI_MSF_FRAME(v);
            if ((v >> 24) || s >= 60 || f >= 75)
                return false;
            sample = (U64(m) * 60 * 75 + U64(s) * 75 + f) * samples_per_cd_frame;
            return sample <= total_;
        }
        return false;
    }
    static DWORD msf(U64 samples) {
        const U64 f = samples / samples_per_cd_frame;
        return MCI_MAKE_MSF(f / (60 * 75), (f / 75) % 60, f % 75);
    }
    DWORD position_value(U64 sample) const {
        sample = std::min(sample, total_);
        if (time_format_ != MCI_FORMAT_TMSF)
            return msf(sample);
        const auto &tr = track_at(sample);
        const U64 f = (sample - tr.start) / samples_per_cd_frame;
        return MCI_MAKE_TMSF(tr.number, f / (60 * 75), (f / 75) % 60, f % 75);
    }
    MCIERROR status(const Request &r, DWORD_PTR &answer) {
        if (!(r.flags & MCI_STATUS_ITEM))
            return MCIERR_MISSING_PARAMETER;
        if ((r.flags & MCI_TRACK) && (r.track < 1 || r.track > 3))
            return MCIERR_OUTOFRANGE;
        if ((r.flags & MCI_STATUS_START) && r.item != MCI_STATUS_POSITION)
            return MCIERR_FLAGS_NOT_COMPATIBLE;
        if ((r.flags & MCI_TRACK) && r.item != MCI_STATUS_POSITION && r.item != MCI_STATUS_LENGTH &&
            r.item != MCI_CDA_STATUS_TYPE_TRACK)
            return MCIERR_FLAGS_NOT_COMPATIBLE;
        switch (r.item) {
        case MCI_STATUS_MEDIA_PRESENT:
        case MCI_STATUS_READY:
            answer = TRUE;
            break;
        case MCI_STATUS_NUMBER_OF_TRACKS:
            answer = 3;
            break;
        case MCI_STATUS_TIME_FORMAT:
            answer = time_format_;
            break;
        case MCI_STATUS_MODE:
            answer = mode_;
            break;
        case MCI_STATUS_CURRENT_TRACK:
            answer = track_at(cursor_).number;
            break;
        case MCI_CDA_STATUS_TYPE_TRACK:
            if (!(r.flags & MCI_TRACK))
                return MCIERR_MISSING_PARAMETER;
            answer = r.track == 1 ? MCI_CDA_TRACK_OTHER : MCI_CDA_TRACK_AUDIO;
            break;
        case MCI_STATUS_LENGTH:
            if (r.flags & MCI_TRACK) {
                if (r.track == 1)
                    return MCIERR_NONAPPLICABLE_FUNCTION;
                answer = msf(tracks_[r.track - 2].frames);
            } else
                answer = msf(total_);
            break;
        case MCI_STATUS_POSITION:
            if (r.flags & MCI_TRACK) {
                if (r.track == 1)
                    return MCIERR_NONAPPLICABLE_FUNCTION;
                answer = position_value(tracks_[r.track - 2].start);
            } else if (r.flags & MCI_STATUS_START)
                answer = position_value(0);
            else
                answer = position_value(cursor_);
            break;
        default:
            return MCIERR_UNSUPPORTED_FUNCTION;
        }
        return 0;
    }
    MCIERROR command(const RequestPtr &q, bool &deferred, DWORD_PTR &answer) {
        auto &r = *q;
        trace("command", r.msg, r.flags);
        if (r.msg == MCI_OPEN) {
            const auto e = open_output();
            if (!e) {
                answer = device_id;
                install_notification(r, false, false);
            }
            return e;
        }
        if (r.dev != device_id || !opened_)
            return MCIERR_INVALID_DEVICE_ID;
        if (fault_ && r.msg != MCI_STOP && r.msg != MCI_CLOSE)
            return fault_;
        if (const auto e = position(); e && r.msg != MCI_CLOSE) {
            (void)reset();
            failed_play(e);
            return e;
        }
        switch (r.msg) {
        case MCI_STATUS: {
            const auto e = status(r, answer);
            if (!e) {
                install_notification(r, false, false);
                audit("status");
            }
            return e;
        }
        case MCI_SET:
            if (!(r.flags & MCI_SET_TIME_FORMAT))
                return MCIERR_UNSUPPORTED_FUNCTION;
            if (r.format != MCI_FORMAT_TMSF && r.format != MCI_FORMAT_MSF)
                return MCIERR_BAD_TIME_FORMAT;
            time_format_ = r.format;
            install_notification(r, false, false);
            return 0;
        case MCI_PLAY: {
            U64 from = cursor_, to = total_;
            if ((r.flags & MCI_FROM) && !decode_position(r.from, false, from))
                return MCIERR_OUTOFRANGE;
            if ((r.flags & MCI_TO) && !decode_position(r.to, true, to))
                return MCIERR_OUTOFRANGE;
            if (from >= to || from >= total_)
                return MCIERR_OUTOFRANGE;
            if (wait_play_)
                return MCIERR_DEVICE_LOCKED;
            // A play command without a new start can keep the queued range.
            // Replacing the range instead resets WaveOut and restarts counters.
            const bool keep = (mode_ == MCI_MODE_PLAY || mode_ == MCI_MODE_PAUSE) &&
                              !(r.flags & MCI_FROM) && to == play_end_;
            const bool prevents = pending_notify_ && ((r.flags & MCI_FROM) || to != play_end_);
            if (keep) {
                if (mode_ == MCI_MODE_PAUSE) {
                    const auto e = hardware("waveOutRestart", ::waveOutRestart(output_->wave));
                    if (e)
                        return e;
                    mode_ = MCI_MODE_PLAY;
                }
            } else {
                const auto e = reset();
                if (e)
                    return e;
                cursor_ = play_base_ = submitted_ = completed_ = from;
                play_end_ = to;
                queued_nonzero_ = played_nonzero_ = 0;
                mode_ = MCI_MODE_PLAY;
                const auto f = fill();
                if (f) {
                    (void)reset();
                    cancel_pending(MCI_NOTIFY_ABORTED);
                    failed_play(f);
                    return f;
                }
            }
            install_notification(r, prevents, true);
            trace("play", position_value(from), to);
            if (r.flags & MCI_WAIT) {
                wait_play_ = q;
                deferred = true;
            }
            return 0;
        }
        case MCI_PAUSE:
            if (mode_ != MCI_MODE_PLAY && mode_ != MCI_MODE_PAUSE)
                return MCIERR_NONAPPLICABLE_FUNCTION;
            if (mode_ == MCI_MODE_PLAY) {
                const auto e = hardware("waveOutPause", ::waveOutPause(output_->wave));
                if (e)
                    return e;
                mode_ = MCI_MODE_PAUSE;
            }
            install_notification(r, false, false);
            trace("pause", position_value(cursor_));
            return 0;
        case MCI_RESUME:
            if (mode_ != MCI_MODE_PAUSE)
                return MCIERR_NONAPPLICABLE_FUNCTION;
            {
                const auto e = hardware("waveOutRestart", ::waveOutRestart(output_->wave));
                if (e)
                    return e;
                mode_ = MCI_MODE_PLAY;
                install_notification(r, false, true);
                return 0;
            }
        case MCI_SEEK: {
            U64 to{};
            if (r.flags & MCI_SEEK_TO_END)
                to = total_;
            else if (r.flags & MCI_SEEK_TO_START)
                to = 0;
            else if (!decode_position(r.to, false, to))
                return MCIERR_OUTOFRANGE;
            const auto e = reset();
            if (e)
                return e;
            mode_ = MCI_MODE_STOP;
            cursor_ = submitted_ = completed_ = to;
            finish_wait(MCIERR_DEVICE_NOT_READY);
            install_notification(r, true, false);
            trace("seek", position_value(cursor_));
            return 0;
        }
        case MCI_STOP: {
            audit("stop");
            const auto e = reset();
            if (e)
                return e;
            mode_ = MCI_MODE_STOP;
            fault_ = 0;
            finish_wait(MCIERR_DEVICE_NOT_READY);
            install_notification(r, true, false);
            trace("stop", position_value(cursor_));
            return 0;
        }
        case MCI_CLOSE: {
            const auto e = close_output();
            if (e)
                return e;
            finish_wait(MCIERR_DEVICE_NOT_READY);
            install_notification(r, true, false);
            fault_ = 0;
            trace("close", device_id);
            return 0;
        }
        default:
            return MCIERR_UNRECOGNIZED_COMMAND;
        }
    }
    void worker() {
        // The manual-reset control event and queue share one mutex: draining
        // and resetting under that lock prevents losing a concurrent submission.
        // Device events wake the same thread to reclaim and refill PCM slots.
        bool exit = false;
        while (!exit) {
            HANDLE events[2] = {control_, output_ ? output_->event : nullptr};
            const auto w = ::WaitForMultipleObjects(output_ ? 2U : 1U, events, FALSE, INFINITE);
            if (w == WAIT_FAILED) {
                fault_ = MCIERR_HARDWARE;
                trace("worker-wait-failed", ::GetLastError());
                std::fprintf(stderr, "Local CD audio: worker wait failed\n");
            }
            std::deque<RequestPtr> ready;
            {
                std::lock_guard lock(queue_mutex_);
                ready.swap(queue_);
                ::ResetEvent(control_);
            }
            for (const auto &r : ready) {
                MCIERROR result{};
                DWORD_PTR answer{};
                bool deferred = false;
                try {
                    if (r->kind == Request::Shutdown) {
                        if (opened_)
                            (void)position();
                        result = close_output();
                        cancel_pending(MCI_NOTIFY_ABORTED);
                        finish_wait(MCIERR_DEVICE_NOT_READY);
                        exit = true;
                    } else if (r->kind == Request::GetVolume)
                        answer = volume_;
                    else if (r->kind == Request::SetVolume) {
                        volume_ = r->value;
                        trace("volume", volume_);
                    } else
                        result = command(r, deferred, answer);
                } catch (const std::bad_alloc &) {
                    result = MCIERR_OUT_OF_MEMORY;
                } catch (...) {
                    result = MCIERR_INTERNAL;
                    std::fprintf(stderr, "Local CD audio: unexpected worker exception\n");
                }
                if (!deferred)
                    complete(r, result, answer);
            }
            if (!exit && opened_ && mode_ == MCI_MODE_PLAY) {
                const auto e = fill();
                if (e) {
                    (void)reset();
                    failed_play(e);
                }
            }
        }
        // A pathological driver failure must not free memory still owned by its DMA queue.
        // Keep that one session alive until process teardown and make the failure visible.
        if (output_) {
            std::fprintf(stderr,
                         "Local CD audio: failed driver cleanup; retaining its live buffers\n");
            (void)output_.release();
        }
    }

  public:
    static constexpr UINT device_id = 0x4d34;
    // An empty manifest leaves the service disabled. A supplied manifest is loaded
    // and validated before creating the worker; missing/bad data throws visibly.
    LocalCdAudio() : LocalCdAudio(environment_path("MW34_MUSIC_PACK")) {}
    explicit LocalCdAudio(const std::filesystem::path &manifest) {
        if (manifest.empty())
            return;
        load(manifest);
        const auto logpath = environment_path("MW34_MUSIC_LOG");
        if (!logpath.empty()) {
            log_ = ::_wfopen(logpath.c_str(), L"ab");
            if (!log_)
                throw std::runtime_error("Local CD: cannot open requested music log");
        }
        control_ = ::CreateEventW(nullptr, TRUE, FALSE, nullptr);
        if (!control_) {
            if (log_)
                std::fclose(log_);
            throw std::runtime_error("Local CD: cannot create worker event");
        }
        try {
            worker_ = std::thread([this] { worker(); });
        } catch (...) {
            ::CloseHandle(control_);
            if (log_)
                std::fclose(log_);
            throw;
        }
    }
    // Callers stop submitting requests before destruction. Shutdown runs on the
    // worker and is joined before host event/log resources are released.
    ~LocalCdAudio() {
        if (worker_.joinable()) {
            auto r = std::make_shared<Request>();
            r->kind = Request::Shutdown;
            (void)invoke(r);
            worker_.join();
        }
        if (control_)
            ::CloseHandle(control_);
        if (log_)
            std::fclose(log_);
    }
    LocalCdAudio(const LocalCdAudio &) = delete;
    LocalCdAudio &operator=(const LocalCdAudio &) = delete;
    bool enabled() const noexcept { return enabled_; }
    bool owns(UINT dev) const noexcept { return enabled_ && dev == device_id; }
    UINT aux_id() const noexcept { return 0; }
    MMRESULT aux_caps(AUXCAPSA &caps) const {
        if (!enabled_)
            return MMSYSERR_BADDEVICEID;
        caps = {};
        caps.vDriverVersion = 0x100;
        std::strcpy(caps.szPname, "MW3 local CD audio");
        caps.wTechnology = AUXCAPS_CDAUDIO;
        caps.dwSupport = AUXCAPS_VOLUME | AUXCAPS_LRVOLUME;
        return MMSYSERR_NOERROR;
    }
    MMRESULT aux_get_volume(DWORD &volume) {
        auto r = std::make_shared<Request>();
        r->kind = Request::GetVolume;
        const auto e = invoke(r);
        if (e)
            return MMSYSERR_ERROR;
        volume = DWORD(r->answer);
        return MMSYSERR_NOERROR;
    }
    MMRESULT aux_set_volume(DWORD volume) {
        auto r = std::make_shared<Request>();
        r->kind = Request::SetVolume;
        r->value = volume;
        return invoke(r) ? MMSYSERR_ERROR : MMSYSERR_NOERROR;
    }
    // params points to the caller's native MCI parameter structure, not guest
    // memory. The guest-facing adapter must marshal and validate it first. This
    // method copies supported request fields before handing work to the worker.
    MCIERROR send(UINT dev, UINT msg, DWORD flags, DWORD_PTR params) {
        if (!enabled_)
            return MCIERR_DEVICE_NOT_INSTALLED;
        auto r = std::make_shared<Request>();
        r->dev = dev;
        r->msg = msg;
        r->flags = flags;
        DWORD allowed = MCI_WAIT | MCI_NOTIFY;
        switch (msg) {
        case MCI_OPEN:
            allowed |= MCI_OPEN_TYPE | MCI_OPEN_TYPE_ID;
            break;
        case MCI_STATUS:
            allowed |= MCI_STATUS_ITEM | MCI_TRACK | MCI_STATUS_START;
            break;
        case MCI_SET:
            allowed |= MCI_SET_TIME_FORMAT;
            break;
        case MCI_PLAY:
            allowed |= MCI_FROM | MCI_TO;
            break;
        case MCI_SEEK:
            allowed |= MCI_TO | MCI_SEEK_TO_START | MCI_SEEK_TO_END;
            break;
        case MCI_STOP:
        case MCI_PAUSE:
        case MCI_RESUME:
        case MCI_CLOSE:
            break;
        default:
            return MCIERR_UNRECOGNIZED_COMMAND;
        }
        if (!flags_allowed(flags, allowed))
            return MCIERR_FLAGS_NOT_COMPATIBLE;
        if (!params && (msg == MCI_OPEN || msg == MCI_STATUS || msg == MCI_SET ||
                        (flags & (MCI_NOTIFY | MCI_FROM | MCI_TO))))
            return MCIERR_NULL_PARAMETER_BLOCK;
        if (params && (flags & MCI_NOTIFY))
            r->callback = reinterpret_cast<const MCI_GENERIC_PARMS *>(params)->dwCallback;
        if (!callback_valid(*r))
            return MCIERR_NO_WINDOW;
        if (msg == MCI_OPEN) {
            const auto *p = reinterpret_cast<const MCI_OPEN_PARMSA *>(params);
            if (!(flags & MCI_OPEN_TYPE))
                return MCIERR_DEVICE_TYPE_REQUIRED;
            if (flags & MCI_OPEN_TYPE_ID) {
                if (reinterpret_cast<std::uintptr_t>(p->lpstrDeviceType) != MCI_DEVTYPE_CD_AUDIO)
                    return MCIERR_INVALID_DEVICE_NAME;
            } else if (!p->lpstrDeviceType || ::_stricmp(p->lpstrDeviceType, "cdaudio"))
                return MCIERR_INVALID_DEVICE_NAME;
        } else if (msg == MCI_STATUS) {
            const auto *p = reinterpret_cast<const MCI_STATUS_PARMS *>(params);
            r->item = p->dwItem;
            if (flags & MCI_TRACK)
                r->track = p->dwTrack;
        } else if (msg == MCI_SET) {
            const auto *p = reinterpret_cast<const MCI_SET_PARMS *>(params);
            if (flags & MCI_SET_TIME_FORMAT)
                r->format = p->dwTimeFormat;
        } else if (msg == MCI_PLAY) {
            const auto *p = reinterpret_cast<const MCI_PLAY_PARMS *>(params);
            if (flags & MCI_FROM)
                r->from = p->dwFrom;
            if (flags & MCI_TO)
                r->to = p->dwTo;
        } else if (msg == MCI_SEEK) {
            const unsigned choices = ((flags & MCI_TO) ? 1U : 0U) +
                                     ((flags & MCI_SEEK_TO_START) ? 1U : 0U) +
                                     ((flags & MCI_SEEK_TO_END) ? 1U : 0U);
            if (!choices)
                return MCIERR_MISSING_PARAMETER;
            if (choices != 1)
                return MCIERR_FLAGS_NOT_COMPATIBLE;
            if (flags & MCI_TO)
                r->to = reinterpret_cast<const MCI_SEEK_PARMS *>(params)->dwTo;
        }
        const auto e = invoke(r);
        if (!e && msg == MCI_OPEN)
            reinterpret_cast<MCI_OPEN_PARMSA *>(params)->wDeviceID = device_id;
        if (!e && msg == MCI_STATUS)
            reinterpret_cast<MCI_STATUS_PARMS *>(params)->dwReturn = r->answer;
        return e;
    }
};
} // namespace mw34::audio
