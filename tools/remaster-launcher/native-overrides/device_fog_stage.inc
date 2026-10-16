// Optional repair of the original fog cache lifetime across main-device creation.
// Original 57A900 creates the device into 809370 at return57AA9E, then calls
// 57BB70(1). That setter suppresses the call when cached8093B0 already equals1.
// A replacement device starts with FOGENABLE=0. Reconcile the cache with that
// real state and let original initialization decide whether to enable fog.
static bool device_fog_rebind_enabled(){
 static const bool enabled=[]{
  const char*value=std::getenv("MW34_DEVICE_FOG_REBIND");
  if(!value||!std::strcmp(value,"0"))return false;
  if(!std::strcmp(value,"1"))return true;
  throw std::runtime_error("MW34_DEVICE_FOG_REBIND must be 0 or 1");
 }();return enabled;
}
void device_fog_created(unsigned output,unsigned actual){
 if(!device_fog_rebind_enabled()||output!=0x809370||load(state.gpr.rsp.dword)!=0x57aa9e)return;
 const unsigned cached=load(0x8093b0);
 if(cached>1||actual>1)deny("Unknown original/device fog-enable state at main-device creation",cached);
 store(0x8093b0,actual);
 if(const char*path=std::getenv("MW34_FOG_TRACE")){if(FILE*f=std::fopen(path,"a")){
  std::fprintf(f,"cache-sync frame %u old %u actual %u\n",host.frames,cached,actual);std::fclose(f);
 }}
}
