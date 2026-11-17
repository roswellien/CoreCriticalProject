using MW3RemasterLauncher.Core;
using System.IO;
using System.Text.Json;

static class GraphicsPreferencesChecks
{
    public static void Run()
    {
        var root=Path.Combine(Path.GetTempPath(),"MW3GraphicsSetup-"+Guid.NewGuid().ToString("N"));
        try
        {
            var settings=new SettingsManager(root,root);
            if(settings.Current.InitialSetupCompleted || settings.Current.DynamicLighting || settings.Current.Shadows || settings.Current.Headlights ||
               !settings.Current.WaterDetail || !settings.Current.CloudDetail || settings.Current.DrawDistance != 800)
                throw new Exception("Fresh setup must start with stock lighting and remain incomplete");
            settings.Current.ActivePacks.Add("test.keep-pack");
            settings.Save();
            if(new SettingsManager(root,root).Current.InitialSetupCompleted)
                throw new Exception("Saving/cancelling defaults completed first-run setup");
            var choice=new GraphicsPreferences(2560,1440,"windowed","4",8,1600,true,true,true,false,true);
            choice.ApplyTo(settings.Current);
            settings.Current.InitialSetupCompleted=true;
            settings.Save();
            var loaded=new SettingsManager(root,root).Current;
            if(GraphicsPreferences.From(loaded)!=choice || !loaded.InitialSetupCompleted || loaded.Fullscreen ||
               !loaded.ActivePacks.SequenceEqual(new[]{"test.keep-pack"}))
                throw new Exception("Setup graphics did not persist independently of pack selection");
            var headlightStore=new HeadlightBindings(root);
            if(headlightStore.Load()!=new HeadlightBinding())throw new Exception("Headlights must start unbound");
            var headlightBinding=new HeadlightBinding {Key=0x223,Button=3};
            headlightStore.Save(headlightBinding);
            if(headlightStore.Load()!=headlightBinding)throw new Exception("Headlight binding persistence");
            (choice with {DynamicLighting=false}).ApplyTo(loaded);
            if(!loaded.Headlights)throw new Exception("Lighting off lost headlight preference");
            if(loaded.WaterDetail || !loaded.CloudDetail)throw new Exception("Surface detail choices did not persist");
            foreach(var invalid in new[]{new HeadlightBinding{Key=0x43},new HeadlightBinding{Button=26},new HeadlightBinding{Version=2}})
            {
                try{headlightStore.Save(invalid);throw new Exception("Invalid headlight binding accepted");}
                catch(InvalidDataException){}
                if(headlightStore.Load()!=headlightBinding)throw new Exception("Invalid write replaced binding");
            }
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
}
