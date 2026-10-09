// Static-only pilot. Program database annotations never modify the supplied PE.
// @category MW34.Recomp
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;
import com.google.gson.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

public class MW34GhidraPilot extends GhidraScript {
    private final Gson gson = new GsonBuilder().setPrettyPrinting().create();
    private static String hex(byte[] b) {
        StringBuilder s = new StringBuilder();
        for (byte x : b) s.append(String.format("%02x", x & 255));
        return s.toString();
    }
    private static String sha(byte[] b) throws Exception {
        return hex(MessageDigest.getInstance("SHA-256").digest(b));
    }
    private static Map<String,Object> map(Object... x) {
        Map<String,Object> r = new LinkedHashMap<>();
        for(int i=0;i<x.length;i+=2) r.put((String)x[i],x[i+1]);
        return r;
    }
    private Address address(long x) { return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(x); }
    private Map<String,Object> export(long entry, DecompInterface decompiler) throws Exception {
        long begin = System.nanoTime();
        Address a = address(entry);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        if(f==null) return map("entry",entry,"present",false,"containing_function",String.valueOf(currentProgram.getFunctionManager().getFunctionContaining(a)));
        List<Object> ranges = new ArrayList<>(), instructions = new ArrayList<>(), calls = new ArrayList<>();
        AddressRangeIterator ri = f.getBody().getAddressRanges();
        while(ri.hasNext()) {
            AddressRange ar=ri.next();
            byte[] bytes=new byte[(int)ar.getLength()];
            currentProgram.getMemory().getBytes(ar.getMinAddress(),bytes);
            ranges.add(map("start",ar.getMinAddress().getOffset(),"end_inclusive",ar.getMaxAddress().getOffset(),"length",bytes.length,"bytes_hex",hex(bytes),"sha256",sha(bytes)));
        }
        InstructionIterator ii=currentProgram.getListing().getInstructions(f.getBody(),true);
        while(ii.hasNext()) {
            Instruction ins=ii.next();
            instructions.add(map("address",ins.getAddress().getOffset(),"length",ins.getLength(),"bytes_hex",hex(ins.getBytes()),"text",ins.toString(),"flow_type",ins.getFlowType().toString()));
            if(ins.getFlowType().isCall()) {
                List<Object> refs=new ArrayList<>();
                for(Reference ref:ins.getReferencesFrom()) {
                    Address dest=ref.getToAddress();
                    Function called=currentProgram.getFunctionManager().getFunctionAt(dest);
                    refs.add(map("address",dest.getOffset(),"space",dest.getAddressSpace().getName(),"type",ref.getReferenceType().toString(),"operand",ref.getOperandIndex(),"function",called==null?null:called.getName()));
                }
                calls.add(map("site",ins.getAddress().getOffset(),"instruction",ins.toString(),"references",refs));
            }
        }
        long decompStart=System.nanoTime();
        DecompileResults result=decompiler.decompileFunction(f,60,monitor);
        String pseudo=result.decompileCompleted()?result.getDecompiledFunction().getC():null;
        return map("entry",entry,"present",true,"name",f.getName(),"signature",f.getSignature().toString(),"calling_convention",f.getCallingConventionName(),"body_ranges",ranges,"instruction_count",instructions.size(),"instructions",instructions,"calls",calls,"decompile_completed",result.decompileCompleted(),"decompile_error",result.getErrorMessage(),"pseudocode",pseudo,"decompile_seconds",(System.nanoTime()-decompStart)/1e9,"export_seconds",(System.nanoTime()-begin)/1e9);
    }
    @Override public void run() throws Exception {
        long scriptStart=System.nanoTime();
        String[] args=getScriptArgs();
        if(args.length<4) throw new IllegalArgumentException("output mode originalPE sha256 [inventory inventorysha]");
        Path output=Path.of(args[0]);
        Path original=Path.of(args[2]);
        String targetSha=sha(Files.readAllBytes(original));
        if(!targetSha.equals(args[3])) throw new IllegalStateException("original target hash mismatch");
        if(!targetSha.equalsIgnoreCase(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Ghidra imported target hash mismatch");
        Map<String,Object> root=map("target",original.toAbsolutePath().toString(),"target_sha256",targetSha,"imported_sha256",currentProgram.getExecutableSHA256(),"program_name",currentProgram.getName(),"image_base",currentProgram.getImageBase().getOffset(),"language",currentProgram.getLanguageID().toString(),"compiler_spec",currentProgram.getCompilerSpec().getCompilerSpecID().toString(),"mode",args[1],"native_executed",false,"initializer_credit",false,"function_count_before",currentProgram.getFunctionManager().getFunctionCount());
        long[] selected;
        if(args[1].equals("game")) {
            byte[] inventoryRaw=Files.readAllBytes(Path.of(args[4]));
            if(!sha(inventoryRaw).equals(args[5])) throw new IllegalStateException("inventory receipt hash mismatch");
            JsonObject inventory=JsonParser.parseString(new String(inventoryRaw,StandardCharsets.UTF_8)).getAsJsonObject();
            if(!targetSha.equals(inventory.get("game_sha256").getAsString())) throw new IllegalStateException("inventory target mismatch");
            long tableStart=inventory.get("table_start").getAsLong();
            int slots=inventory.get("slots").getAsInt();
            if(slots!=145) throw new IllegalStateException("unexpected table size");
            byte[] table=new byte[slots*4];
            currentProgram.getMemory().getBytes(address(tableStart),table);
            if(!hex(table).equals(inventory.get("table_bytes_hex").getAsString()) || !sha(table).equals(inventory.get("table_sha256").getAsString())) throw new IllegalStateException("actual Ghidra table bytes differ");
            Map<Long,Long> expected=new LinkedHashMap<>();
            for(JsonElement el:inventory.getAsJsonArray("roots")) {
                JsonObject r=el.getAsJsonObject();
                expected.put(r.get("slot").getAsLong(),r.get("entry").getAsLong());
            }
            if(expected.size()!=144) throw new IllegalStateException("expected root count differs");
            long seedStart=System.nanoTime();
            List<Object> seeds=new ArrayList<>();
            int found=0,created=0,conflicts=0;
            for(int i=0;i<slots;i++) {
                int k=i*4;
                long entry=(table[k]&255L)|((table[k+1]&255L)<<8)|((table[k+2]&255L)<<16)|((table[k+3]&255L)<<24);
                if(entry==0) { if(i!=0) throw new IllegalStateException("unexpected zero"); continue; }
                long slot=tableStart+k;
                if(!Long.valueOf(entry).equals(expected.get(slot))) throw new IllegalStateException("table root mismatch");
                Address a=address(entry);
                Function at=currentProgram.getFunctionManager().getFunctionAt(a);
                Function containing=currentProgram.getFunctionManager().getFunctionContaining(a);
                MemoryBlock block=currentProgram.getMemory().getBlock(a);
                String status;
                if(at!=null) { status="existing_exact"; found++; }
                else if(containing!=null || block==null || !block.isExecute()) { status="refused_conflict_or_nonexec"; conflicts++; }
                else {
                    if(currentProgram.getListing().getInstructionAt(a)==null) disassemble(a);
                    if(currentProgram.getListing().getInstructionAt(a)==null) { status="refused_no_instruction"; conflicts++; }
                    else {
                        Function made=createFunction(a,String.format("mw34_initializer_%08x",entry));
                        if(made==null || !made.getEntryPoint().equals(a)) { status="refused_create_failed"; conflicts++; }
                        else {status="created_missing_exact"; created++;}
                    }
                }
                seeds.add(map("slot",slot,"entry",entry,"status",status,"prior_containing",containing==null?null:containing.getEntryPoint().getOffset()));
            }
            root.put("table",map("inventory_sha256",args[5],"start",tableStart,"slots",slots,"nonzero_entries",expected.size(),"bytes_hex",hex(table),"sha256",sha(table),"existing_exact",found,"created",created,"conflicts",conflicts,"seed_seconds",(System.nanoTime()-seedStart)/1e9,"seeds",seeds));
            // First three physical roots, a callback-registration root, its wrapper,
            // and the numeric initializer/helper whose floating-point effects matter.
            selected=new long[]{0x40ffe0L,0x410030L,0x410080L,0x410210L,0x5ac110L,0x51af50L,0x51b020L};
        } else if(args[1].equals("provider")) selected=new long[]{0x78004a36L,0x7800151dL};
        else throw new IllegalArgumentException("unknown mode");
        DecompInterface d=new DecompInterface();
        d.toggleCCode(true);d.toggleSyntaxTree(true);
        if(!d.openProgram(currentProgram)) throw new IllegalStateException("decompiler open failed");
        List<Object> exports=new ArrayList<>();
        long exportsStart=System.nanoTime();
        try { for(long entry:selected) exports.add(export(entry,d)); } finally { d.dispose(); }
        root.put("exports",exports);
        root.put("exports_seconds",(System.nanoTime()-exportsStart)/1e9);
        root.put("function_count_after",currentProgram.getFunctionManager().getFunctionCount());
        root.put("script_seconds",(System.nanoTime()-scriptStart)/1e9);
        Files.writeString(output,gson.toJson(root)+"\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        println("MW34_PILOT_COMPLETE "+output+" script_seconds="+root.get("script_seconds"));
    }
}
