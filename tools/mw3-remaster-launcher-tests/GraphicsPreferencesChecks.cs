using MW3RemasterLauncher.Core;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;

static class GraphicsPreferencesChecks
{
    public static void Run()
    {
        var root=Path.Combine(Path.GetTempPath(),"MW3GraphicsSetup-"+Guid.NewGuid().ToString("N"));
        try
        {
            var settings=new SettingsManager(root,root);
            if(settings.Current.InitialSetupCompleted || settings.Current.DynamicLighting || settings.Current.Shadows || settings.Current.Headlights ||
               !settings.Current.WaterDetail || !settings.Current.CloudDetail || settings.Current.DrawDistance != 800 ||
               settings.Current.FlareStyle != "modern" || settings.Current.Vsync || !settings.Current.UpscaledCutscenes)
                throw new Exception("Fresh setup must start with stock lighting and remain incomplete");
            settings.Current.ActivePacks.Add("test.keep-pack");
            settings.Save();
            if(new SettingsManager(root,root).Current.InitialSetupCompleted)
                throw new Exception("Saving/cancelling defaults completed first-run setup");
            var choice=new GraphicsPreferences(2560,1440,"windowed","4",8,1600,true,true,true,false,true,"original", Vsync: true);
            choice.ApplyTo(settings.Current);
            settings.Current.InitialSetupCompleted=true;
            settings.Save();
            var loaded=new SettingsManager(root,root).Current;
            if(GraphicsPreferences.From(loaded)!=choice || !loaded.InitialSetupCompleted || loaded.Fullscreen ||
               !loaded.ActivePacks.SequenceEqual(new[]{"test.keep-pack"}))
                throw new Exception("Setup graphics did not persist independently of pack selection");
            (choice with { Vsync = false }).ApplyTo(settings.Current);
            settings.Save();
            if (new SettingsManager(root, root).Current.Vsync)
                throw new Exception("Turning VSync off did not persist.");
            (choice with { UpscaledCutscenes = false }).ApplyTo(settings.Current);
            settings.Save();
            if (new SettingsManager(root, root).Current.UpscaledCutscenes)
                throw new Exception("Turning Upscaled cutscenes off did not persist.");
            var headlightStore=new HeadlightBindings(root);
            if(headlightStore.Load()!=new HeadlightBinding())throw new Exception("Fresh headlight settings must default to L");
            var nativeSession=Path.Combine(root,"headlight-native");
            Directory.CreateDirectory(nativeSession);
            if(headlightStore.WriteNativeBinding(nativeSession,true)==null ||
               File.ReadAllText(Path.Combine(nativeSession,"mw3-headlights.txt"))!="CC_MW3_HEADLIGHTS_V1\n38 -1\n")
                throw new Exception("Default headlight binding native file format changed");
            var headlightPath=Path.Combine(root,"controls","mw3-headlights-v1.json");
            Directory.CreateDirectory(Path.GetDirectoryName(headlightPath)!);
            // JsonSerializer.Serialize's default options have written Key since 5ca34624,
            // including 0 for a clear; a missing Key means the binding was never set.
            File.WriteAllText(headlightPath,"{\"Version\":1,\"Button\":-1}");
            if (headlightStore.Load() != new HeadlightBinding())
                throw new Exception("A legacy headlight file must default to L with no mouse binding.");
            var clearedBinding=new HeadlightBinding {Key=0,Button=-1};
            headlightStore.Save(clearedBinding);
            if(!File.ReadAllText(headlightPath).Contains("\"Key\": 0") || headlightStore.Load()!=clearedBinding ||
               headlightStore.WriteNativeBinding(nativeSession,true)!=null)
                throw new Exception("An explicitly cleared headlight binding did not persist");
            var headlightBinding=new HeadlightBinding {Key=0x223,Button=3};
            headlightStore.Save(headlightBinding);
            if(headlightStore.Load()!=headlightBinding || headlightStore.WriteNativeBinding(nativeSession,true)==null ||
               File.ReadAllText(Path.Combine(nativeSession,"mw3-headlights.txt"))!="CC_MW3_HEADLIGHTS_V1\n547 3\n")
                throw new Exception("Saved headlight binding was changed or not written to the native file");
            (choice with {DynamicLighting=false}).ApplyTo(loaded);
            if(!loaded.Headlights)throw new Exception("Lighting off lost headlight preference");
            if(loaded.WaterDetail || !loaded.CloudDetail)throw new Exception("Surface detail choices did not persist");
            foreach(var invalid in new[]{new HeadlightBinding{Key=0x43},new HeadlightBinding{Button=26},new HeadlightBinding{Version=2}})
            {
                try{headlightStore.Save(invalid);throw new Exception("Invalid headlight binding accepted");}
                catch(InvalidDataException){}
                if(headlightStore.Load()!=headlightBinding)throw new Exception("Invalid write replaced binding");
            }
            CheckMouseHeadlights(headlightStore, headlightPath, nativeSession);
            var before=JsonSerializer.Serialize(loaded);
            try{(choice with{AnisotropicFiltering=3}).ApplyTo(loaded);throw new Exception("Unsupported AF accepted");}
            catch(InvalidOperationException){}
            if(JsonSerializer.Serialize(loaded)!=before)throw new Exception("Failed graphics validation partially changed settings");
            try
            {
                (choice with { DrawDistance = 1000 }).ApplyTo(loaded);
                throw new Exception("Unsupported scenery distance accepted");
            }
            catch(InvalidOperationException){}
            if(JsonSerializer.Serialize(loaded)!=before)throw new Exception("Failed scenery validation partially changed settings");
            try
            {
                (choice with { FlareStyle = "smooth" }).ApplyTo(loaded);
                throw new Exception("Unsupported lens flare style accepted");
            }
            catch(InvalidOperationException){}
            if(JsonSerializer.Serialize(loaded)!=before)throw new Exception("Failed flare validation partially changed settings");
            try
            {
                (choice with { FlareStyle = "future" }).Validate();
                throw new Exception("Unknown lens flare style accepted");
            }
            catch (InvalidOperationException) { }
            var expectedDistances = new[] { 800, 1200, 1600, 2400, 3200 };
            var acceptedDistances = new List<int>();
            for (var distance = 0; distance <= NativeGameRunner.MaxDrawDistance + 1; ++distance)
            {
                var graphicsAccepted = true;
                try { (choice with { DrawDistance = distance }).Validate(); }
                catch (InvalidOperationException) { graphicsAccepted = false; }
                var nativeAccepted = true;
                try
                {
                    var nativeDistance = NativeGameRunner.PreviewDrawDistance(distance,
                        out var reduced);
                    if (nativeDistance != distance || reduced)
                        throw new Exception("Native scenery selection was reduced");
                }
                catch (InvalidOperationException) { nativeAccepted = false; }
                if (graphicsAccepted != nativeAccepted)
                    throw new Exception("Graphics and native scenery validation disagree");
                if (graphicsAccepted) acceptedDistances.Add(distance);
            }
            if (!acceptedDistances.SequenceEqual(expectedDistances) ||
                NativeGameRunner.MaxDrawDistance != 3200)
                throw new Exception("Launcher scenery distances differ from the supported set");
            // Legacy installations keep their choices and do not reopen first-run setup.
            File.WriteAllText(settings.SettingsPath,"{\"Width\":3440,\"Height\":1440,\"WindowMode\":\"windowed\",\"AntiAliasing\":\"2\",\"DrawDistance\":3200,\"ActivePacks\":[\"test.existing\"]}");
            loaded=new SettingsManager(root,root).Current;
            if(!loaded.InitialSetupCompleted || loaded.Width!=3440 || loaded.AntiAliasing!="2" ||
               loaded.DrawDistance!=3200 || !loaded.ActivePacks.Contains("test.existing") ||
               loaded.DynamicLighting || loaded.Shadows || loaded.Headlights ||
               !loaded.WaterDetail || !loaded.CloudDetail)
                throw new Exception("Existing launcher settings were reset by setup migration");
            Console.WriteLine("First-run graphics validation, persistence, cancellation marker and legacy preference preservation passed.");
        }
        finally{if(Directory.Exists(root))Directory.Delete(root,true);}
    }
    private static void CheckMouseHeadlights(HeadlightBindings store, string jsonPath, string session)
    {
        var wirePath = Path.Combine(session, "mw3-headlights.txt");
        for (var mouse = 0; mouse <= 7; mouse++)
        {
            var binding = new HeadlightBinding { Key = 0, Button = -1, Mouse = mouse };
            store.Save(binding);
            using var json = JsonDocument.Parse(File.ReadAllText(jsonPath));
            if (json.RootElement.GetProperty("Version").GetInt32() != 1 || store.Load() != binding)
                throw new Exception("Headlight mouse binding was not saved as a JSON v1 profile.");
            if (mouse > 0 && (store.WriteNativeBinding(session, true) != wirePath ||
                File.ReadAllText(wirePath) != FormattableString.Invariant($"CC_MW3_HEADLIGHTS_V2\n0 -1 {mouse}\n")))
                throw new Exception("Mouse-only headlight binding lost its versioned wire row.");
            if (mouse == 0 && store.WriteNativeBinding(session, true) != null)
                throw new Exception("Unassigned headlight input wrote a binding.");
        }

        var launch = new JsonObject
        {
            ["native"] = new JsonObject
            {
                ["runtime_environment"] = new JsonObject { ["MW34_HEADLIGHT_BINDINGS"] = "original" }
            }
        };
        var original = launch.ToJsonString();
        var wire = File.ReadAllText(wirePath);
        try
        {
            store.PrepareLaunch(launch, session, true);
            throw new Exception("D7VK accepted an enabled headlight mouse binding.");
        }
        catch (InvalidDataException error) when (error.Message.Contains("D7VK")) { }
        if (launch.ToJsonString() != original || File.ReadAllText(wirePath) != wire)
            throw new Exception("D7VK rejection changed the headlight projection.");

        store.PrepareLaunch(launch, session, false);
        if (launch["native"]["runtime_environment"]["MW34_HEADLIGHT_BINDINGS"].GetValue<string>() != "" ||
            store.WriteNativeBinding(session, false) != null || File.ReadAllText(wirePath) != wire)
            throw new Exception("Disabled mouse headlights changed the wire file.");

        foreach (var invalid in new[]
        {
            new HeadlightBinding { Mouse = -1 }, new HeadlightBinding { Mouse = 8 }, new HeadlightBinding { Version = 2 }
        })
        {
            try { store.Save(invalid); throw new Exception("Invalid headlight binding was saved."); }
            catch (InvalidDataException) { }
            if (store.Load().Mouse != 7) throw new Exception("An invalid save replaced the mouse binding.");
            var valid = File.ReadAllText(jsonPath);
            File.WriteAllText(jsonPath, JsonSerializer.Serialize(invalid));
            try { store.Load(); throw new Exception("Invalid headlight JSON was loaded."); }
            catch (InvalidDataException) { }
            finally { File.WriteAllText(jsonPath, valid); }
        }
    }
}
