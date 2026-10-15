// Local preparation tool. Decode user-provided audio with Windows Media
// Foundation into canonical PCM; the native game does not need this decoder.
#define NOMINMAX
#include <windows.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <wrl/client.h>
#include <array>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>

using Microsoft::WRL::ComPtr;
static void check(HRESULT result,const char* operation){
 if(FAILED(result)){char message[160]{};std::snprintf(message,sizeof(message),"%s failed (HRESULT %08lX)",operation,static_cast<unsigned long>(result));throw std::runtime_error(message);}}
static void word(std::ostream&out,std::uint16_t value){out.put(char(value));out.put(char(value>>8));}
static void dword(std::ostream&out,std::uint32_t value){word(out,std::uint16_t(value));word(out,std::uint16_t(value>>16));}
static void header(std::ostream&out,std::uint32_t bytes){
 out.seekp(0);out.write("RIFF",4);dword(out,bytes+36);out.write("WAVEfmt ",8);dword(out,16);
 word(out,WAVE_FORMAT_PCM);word(out,2);dword(out,44100);dword(out,176400);word(out,4);word(out,16);out.write("data",4);dword(out,bytes);}
static std::uint64_t decode(const std::filesystem::path&source,const std::filesystem::path&output){
 ComPtr<IMFSourceReader> reader;check(MFCreateSourceReaderFromURL(source.c_str(),nullptr,&reader),"Open source audio");
 ComPtr<IMFMediaType> format;check(MFCreateMediaType(&format),"Create PCM media type");
 check(format->SetGUID(MF_MT_MAJOR_TYPE,MFMediaType_Audio),"Set audio type");
 check(format->SetGUID(MF_MT_SUBTYPE,MFAudioFormat_PCM),"Set PCM subtype");
 check(format->SetUINT32(MF_MT_AUDIO_NUM_CHANNELS,2),"Set stereo");
 check(format->SetUINT32(MF_MT_AUDIO_SAMPLES_PER_SECOND,44100),"Set sample rate");
 check(format->SetUINT32(MF_MT_AUDIO_BITS_PER_SAMPLE,16),"Set sample depth");
 check(format->SetUINT32(MF_MT_AUDIO_BLOCK_ALIGNMENT,4),"Set sample alignment");
 check(format->SetUINT32(MF_MT_AUDIO_AVG_BYTES_PER_SECOND,176400),"Set byte rate");
 check(reader->SetCurrentMediaType(MF_SOURCE_READER_FIRST_AUDIO_STREAM,nullptr,format.Get()),"Select decoded PCM");
 std::ofstream out(output,std::ios::binary|std::ios::trunc);if(!out)throw std::runtime_error("Cannot create prepared WAV");header(out,0);
 std::uint64_t bytes{};bool finished{};
 while(!finished){
  DWORD stream{},flags{};LONGLONG timestamp{};ComPtr<IMFSample> sample;
  check(reader->ReadSample(MF_SOURCE_READER_FIRST_AUDIO_STREAM,0,&stream,&flags,&timestamp,&sample),"Read decoded audio");
  if(flags&MF_SOURCE_READERF_ERROR)throw std::runtime_error("Audio decoder reported a stream error");
  if(flags&MF_SOURCE_READERF_CURRENTMEDIATYPECHANGED)throw std::runtime_error("Audio format changed during decoding");
  finished=(flags&MF_SOURCE_READERF_ENDOFSTREAM)!=0;
  if(sample){ComPtr<IMFMediaBuffer> buffer;check(sample->ConvertToContiguousBuffer(&buffer),"Read PCM block");BYTE*data{};DWORD length{};
   check(buffer->Lock(&data,nullptr,&length),"Lock PCM block");
   if((length&3)||bytes+length>0xffffffdbULL){buffer->Unlock();throw std::runtime_error("Prepared PCM exceeds the supported WAV range");}
   out.write(reinterpret_cast<const char*>(data),length);bytes+=length;
   check(buffer->Unlock(),"Unlock PCM block");if(!out)throw std::runtime_error("Writing prepared PCM failed");
  }
 }
 if(!bytes)throw std::runtime_error("Audio source decoded to an empty stream");
 header(out,static_cast<std::uint32_t>(bytes));out.close();if(!out)throw std::runtime_error("Finishing prepared WAV failed");return bytes/4;
}
int wmain(int argc,wchar_t**argv){
 if(argc!=3){std::fprintf(stderr,"Usage: decode_music.exe source.flac output.wav\n");return 2;}
 const HRESULT com=CoInitializeEx(nullptr,COINIT_MULTITHREADED);if(FAILED(com)){std::fprintf(stderr,"COM initialization failed: %08lX\n",static_cast<unsigned long>(com));return 1;}
 const HRESULT media=MFStartup(MF_VERSION,MFSTARTUP_NOSOCKET);if(FAILED(media)){std::fprintf(stderr,"Media Foundation initialization failed: %08lX\n",static_cast<unsigned long>(media));CoUninitialize();return 1;}
 int result{};try{const auto frames=decode(argv[1],argv[2]);std::printf("Prepared %llu stereo PCM frames at 44100 Hz\n",static_cast<unsigned long long>(frames));}
 catch(const std::exception&error){std::fprintf(stderr,"Music preparation failed: %s\n",error.what());result=1;}
 MFShutdown();CoUninitialize();return result;
}
