using System.Buffers.Binary;
using System.IO;
using System.Text;
using MW3RemasterLauncher.Core;

static class SteamShortcutChecks
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "CC Steam checks " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        string Text(SteamShortcuts.Field row, string key) => Encoding.UTF8.GetString(row.Children!.Single(f => f.Name.Equals(key, StringComparison.OrdinalIgnoreCase)).Value);
        void SetText(SteamShortcuts.Field row, string key, string value) => row.Children!.Single(f => f.Name.Equals(key, StringComparison.OrdinalIgnoreCase)).Value = Encoding.UTF8.GetBytes(value);
        List<SteamShortcuts.Field> Rows(byte[] bytes) => SteamShortcuts.Parse(bytes)[0].Children!;
        void Reject(Action action)
        {
            try { action(); } catch (InvalidDataException) { return; }
            throw new Exception("Malformed Steam shortcut data was accepted.");
        }
        try
        {
            var app = Path.Combine(root, "App with spaces"); Directory.CreateDirectory(app);
            var exe = Path.Combine(app, "Core Critical Launcher.exe"); File.WriteAllBytes(exe, []);
            var initial = SteamShortcuts.Upsert(null, exe, exe);
            if (Rows(initial.Bytes).Count != 1 || !initial.Changed || !Text(Rows(initial.Bytes)[0], "Exe").Equals('"' + exe + '"'))
                throw new Exception("Fresh Steam shortcut target was not quoted correctly.");
            if (SteamShortcuts.Upsert(initial.Bytes, exe, exe).Changed) throw new Exception("Repeated Steam integration was not idempotent.");
            var legacy = SteamShortcuts.Parse(initial.Bytes);
            var owned = legacy[0].Children![0];
            SetText(owned, "AppName", "MechWarrior 3 Remastered");
            SetText(owned, "Exe", '"' + Path.Combine(app, "MW3RemasterLauncher.exe") + '"');
            SetText(owned, "LaunchOptions", "--authored-user-option");
            var stableId = owned.Children!.Single(f => f.Name == "appid").Value.ToArray();
            owned.Children.Add(new(7, "AuthoredUnknownUint64", new byte[] { 1,2,3,4,5,6,7,8 }));
            var other = Rows(SteamShortcuts.Upsert(null, Path.Combine(root, "other.exe"), "other.ico").Bytes)[0];
            SetText(other, "AppName", "Authored other game");
            SetText(other, "LaunchOptions", "--note Core Critical Launcher"); // A substring is not an installed launcher.
            var otherBody = SteamShortcuts.Serialize(new() { new(0, "shortcuts", [], new() { other }) });
            legacy[0].Children!.Insert(0, other); // Reproduce the old writer's two index-0 records.
            var before = SteamShortcuts.Serialize(legacy);
            var fixedEntry = SteamShortcuts.Upsert(before, exe, exe);
            var rows = Rows(fixedEntry.Bytes);
            if (rows.Count != 2 || rows[0].Name != "0" || rows[1].Name != "1" ||
                !SteamShortcuts.Serialize(new() { new(0,"shortcuts",[],new(){rows[0]}) }).SequenceEqual(otherBody))
                throw new Exception("Unrelated Steam shortcut fields were changed or indexes collided.");
            if (Text(rows[1], "AppName") != "Core Critical Launcher" || Text(rows[1], "Exe") != '"' + exe + '"' ||
                Text(rows[1], "LaunchOptions") != "--authored-user-option" ||
                !rows[1].Children!.Single(f => f.Name == "appid").Value.SequenceEqual(stableId) ||
                !rows[1].Children!.Single(f => f.Name == "AuthoredUnknownUint64").Value.SequenceEqual(new byte[]{1,2,3,4,5,6,7,8}))
                throw new Exception("Legacy target repair lost its stable ID, options or unknown fields.");
            if (SteamShortcuts.Upsert(fixedEntry.Bytes, exe, exe).Changed) throw new Exception("Repaired shortcut changed on repeat.");
            var duplicate = Rows(initial.Bytes)[0]; legacy[0].Children!.Add(duplicate);
            if (Rows(SteamShortcuts.Upsert(SteamShortcuts.Serialize(legacy), exe, exe).Bytes).Count != 2)
                throw new Exception("Duplicate owned launcher entries were retained.");
            Reject(() => SteamShortcuts.Parse(initial.Bytes[..^1]));
            Reject(() => SteamShortcuts.Parse(initial.Bytes.Concat(new byte[]{8}).ToArray()));
            Reject(() => SteamShortcuts.Parse(new byte[SteamShortcuts.MaximumBytes + 1]));
            var invalid = initial.Bytes.ToArray();invalid[0]=9;Reject(() => SteamShortcuts.Parse(invalid));

            var steam = Path.Combine(root,"Steam");var profile=Path.Combine(steam,"userdata","42");var config=Path.Combine(profile,"config");Directory.CreateDirectory(config);
            Directory.CreateDirectory(Path.Combine(steam,"userdata","0","config"));
            if (SteamHelper.SelectProfile(steam)!=profile) throw new Exception("Steam profile 0 was selected.");
            var second=Path.Combine(steam,"userdata","43");Directory.CreateDirectory(Path.Combine(second,"config"));
            if (SteamHelper.SelectProfile(steam,43)!=second) throw new Exception("Active Steam profile was ignored.");
            Directory.CreateDirectory(Path.Combine(steam,"config"));
            File.WriteAllText(Path.Combine(steam,"config","loginusers.vdf"),"\"users\" { \"76561197960265770\" { \"MostRecent\" \"1\" \"PersonaName\" \"Authored \\\"name\\\"\" } \"76561197960265771\" { \"MostRecent\" \"0\" } }");
            if (SteamHelper.SelectProfile(steam)!=profile) throw new Exception("Most recent Steam profile was not selected.");
            var file=Path.Combine(config,"shortcuts.vdf");File.WriteAllBytes(file,before);
            var art=Path.Combine(root,"Artwork");Directory.CreateDirectory(art);File.WriteAllBytes(Path.Combine(art,"hero-art.png"),[1,2,3]);File.WriteAllBytes(Path.Combine(art,"brand-mark.png"),[4,5,6]);
            var result=SteamHelper.InstallForProfile(profile,exe,art);
            if(!result.Changed || result.Backup==null || !File.ReadAllBytes(result.Backup).SequenceEqual(before) || Rows(File.ReadAllBytes(file)).Count!=2)
                throw new Exception("Atomic shortcut update or exact backup failed.");
            var hero=Path.Combine(config,"grid",result.AppId+"_hero.png");File.WriteAllBytes(hero,[7,8,9]);
            if(SteamHelper.InstallForProfile(profile,exe,art).Changed || !File.ReadAllBytes(hero).SequenceEqual(new byte[]{7,8,9}))
                throw new Exception("Repeat integration changed the shortcut or custom artwork.");
            File.WriteAllBytes(file,[0,1,2]);Reject(()=>SteamHelper.InstallForProfile(profile,exe,art));
            if(!File.ReadAllBytes(file).SequenceEqual(new byte[]{0,1,2}))throw new Exception("Malformed Steam file was overwritten.");
            if(File.Exists(Path.Combine(second,"config","shortcuts.vdf")))throw new Exception("An unselected Steam profile was changed.");
        }
        finally {Directory.Delete(root,true);}
        Console.WriteLine("Steam shortcut checks passed: binary structure, index repair, stable-ID target migration, unrelated fields/options, duplicates, exact backup, repeat safety, custom artwork, profile selection and malformed-file preservation.");
    }
}
