// Read-only bounded reference export from the persisted seeded MW3 database.
// @category MW34.Recomp
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import com.google.gson.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
public class MW34FieldReferences extends GhidraScript {
 private Map<String,Object> map(Object... kv){Map<String,Object> r=new LinkedHashMap<>();for(int i=0;i<kv.length;i+=2)r.put((String)kv[i],kv[i+1]);return r;}
 private Address addr(long v){return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v);}
 private String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte x:b)s.append(String.format("%02x",x&255));return s.toString();}
 public void run()throws Exception{
  String[] a=getScriptArgs();if(a.length!=1)throw new IllegalArgumentException("output");
  if(!currentProgram.getExecutableSHA256().equalsIgnoreCase("95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf"))throw new IllegalStateException("Target SHA");
  long start=System.nanoTime();List<Object> refs=new ArrayList<>();Set<Long> functions=new TreeSet<>();
  for(long dest=0x6099e8L;dest<0x6099f8L;dest++){
   ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(addr(dest));
   while(it.hasNext()){
    Reference ref=it.next();Address source=ref.getFromAddress();Instruction ins=currentProgram.getListing().getInstructionContaining(source);Function f=currentProgram.getFunctionManager().getFunctionContaining(source);if(f!=null)functions.add(f.getEntryPoint().getOffset());
    refs.add(map("to",dest,"from",source.getOffset(),"reference_type",ref.getReferenceType().toString(),"operand_index",ref.getOperandIndex(),"instruction",ins==null?null:ins.toString(),"bytes_hex",ins==null?null:hex(ins.getBytes()),"function",f==null?null:f.getEntryPoint().getOffset()));
   }
  }
  // Explicit construction/cleanup table entries must remain present even when analysis missed a helper boundary.
  for(long entry:new long[]{0x49d5c0L,0x49d600L,0x49d5d0L,0x49d610L}){Function f=currentProgram.getFunctionManager().getFunctionAt(addr(entry));if(f!=null)functions.add(entry);}
  DecompInterface d=new DecompInterface();d.toggleCCode(true);d.toggleSyntaxTree(true);if(!d.openProgram(currentProgram))throw new IllegalStateException("decompiler");List<Object> exports=new ArrayList<>();
  try{for(long entry:functions){Function f=currentProgram.getFunctionManager().getFunctionAt(addr(entry));List<Object> rows=new ArrayList<>();InstructionIterator ii=currentProgram.getListing().getInstructions(f.getBody(),true);while(ii.hasNext()){Instruction i=ii.next();List<Object> target=new ArrayList<>();for(Reference ref:i.getReferencesFrom())target.add(map("to",ref.getToAddress().getOffset(),"type",ref.getReferenceType().toString()));rows.add(map("pc",i.getAddress().getOffset(),"bytes_hex",hex(i.getBytes()),"text",i.toString(),"references",target));}DecompileResults dr=d.decompileFunction(f,15,monitor);exports.add(map("entry",entry,"name",f.getName(),"signature",f.getSignature().toString(),"instructions",rows,"pseudocode",dr.decompileCompleted()?dr.getDecompiledFunction().getC():null,"error",dr.getErrorMessage()));}}finally{d.dispose();}
  Map<String,Object> result=map("target_sha256",currentProgram.getExecutableSHA256(),"image_base",currentProgram.getImageBase().getOffset(),"field_begin",0x6099e8L,"field_end",0x6099f8L,"references",refs,"exports",exports,"script_seconds",(System.nanoTime()-start)/1e9,"static_only",true,"read_only",true,"whole_program_liveness_proven",false);
  Files.writeString(Path.of(a[0]),new GsonBuilder().setPrettyPrinting().create().toJson(result)+"\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);println("MW34_FIELD_REFERENCES_COMPLETE "+a[0]);
 }
}
