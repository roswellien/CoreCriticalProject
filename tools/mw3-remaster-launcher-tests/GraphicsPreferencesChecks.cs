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
            if(settings.Current.InitialSetupCompleted || settings.Current.DynamicLighting || settings.Current.Shadows || settings.Current.Headlights)
                throw new Exception("Fresh setup must start with stock lighting and remain incomplete");
            settings.Current.ActivePacks.Add("test.keep-pack");
            settings.Save();
            if(new SettingsManager(root,root).Current.InitialSetupCompleted)
                throw new Exception("Saving/cancelling defaults completed first-run setup");
            var choice=new GraphicsPreferences(2560,1440,"windowed","4",8,2400,0,true,true,true);
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
            // Legacy installations keep their choices and do not reopen first-run setup.
            File.WriteAllText(settings.SettingsPath,"{\"Width\":3440,\"Height\":1440,\"WindowMode\":\"windowed\",\"AntiAliasing\":\"2\",\"ActivePacks\":[\"test.existing\"]}");
            loaded=new SettingsManager(root,root).Current;
            if(!loaded.InitialSetupCompleted || loaded.Width!=3440 || loaded.AntiAliasing!="2" ||
               !loaded.ActivePacks.Contains("test.existing") || loaded.DynamicLighting || loaded.Shadows || loaded.Headlights)
                throw new Exception("Existing launcher settings were reset by setup migration");
            Console.WriteLine("First-run graphics validation, persistence, cancellation marker and legacy preference preservation passed.");
        }
        finally{if(Directory.Exists(root))Directory.Delete(root,true);}
    }
}
