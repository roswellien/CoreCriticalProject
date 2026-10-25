using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.Json;

namespace MW3RemasterLauncher.Core
{
    /// <summary>One duplicate relative filename and the precedence claimed by active packs.</summary>
    public class PackConflict
    {
        public string RelativePath { get; set; } = string.Empty;
        public string WinningPackName { get; set; } = string.Empty;
        public string OverriddenPackName { get; set; } = string.Empty;
    }

    /// <summary>Maintain the launcher's discovered packs and user-selected priority order.</summary>
    /// <remarks>
    /// Collection order is precedence order; InspectConflicts reports the first claim.
    /// PackStorage validates and stages imported files. Publisher authentication and
    /// host compatibility are separate from archive integrity.
    /// </remarks>
    public class PackManager
    {
        private readonly string _modsRoot;
        public string GameId { get; }
        private readonly ObservableCollection<PackManifest> _packs = new();

        public ObservableCollection<PackManifest> Packs => _packs;
        public string ModsRoot => _modsRoot;
        public List<string> DiscoveryErrors { get; } = new();

        public PackManager(string basePath, string gameId = GameCatalog.Mw3)
        {
            GameId = GameCatalog.Get(gameId).Id;
            _modsRoot = Path.GetFullPath(Path.Combine(GameCatalog.PackBase(basePath, GameId), "mods"));
            PackStorage.EnsureNoLinks(_modsRoot);
            if (!Directory.Exists(_modsRoot))
            {
                Directory.CreateDirectory(_modsRoot);
            }
        }

        /// <summary>Rescan directories/archives, then restore the requested enabled order.</summary>
        /// <remarks>Null and an empty list both start stock; existing explicit choices persist.</remarks>
        public void RefreshPacks(List<string>? activeOrder = null)
        {
            _packs.Clear();
            DiscoveryErrors.Clear();
            if (!Directory.Exists(_modsRoot)) return;

            using var storageLock = PackStorage.Lock(_modsRoot);
            PackStorage.Recover(_modsRoot);
            // Loose archives require an explicit import. Startup never overwrites installed content.
            var discovered = new List<PackManifest>();

            // 1. Scan subdirectories under mods/
            foreach (var dir in Directory.GetDirectories(_modsRoot))
            {
                if (Path.GetFileName(dir).StartsWith('.')) continue;
                var manifestFile = Path.Combine(dir, "pack.json");
                if (File.Exists(manifestFile))
                {
                    try
                    {
                        var manifest = PackStorage.ReadManifest(manifestFile);
                        GameCatalog.RequirePackTarget(manifest.GameId, GameId);
                        if (!string.Equals(Path.GetFileName(dir), manifest.Id, StringComparison.Ordinal))
                            throw new InvalidDataException("Installed directory and pack ID disagree.");
                        if (manifest != null && !string.IsNullOrWhiteSpace(manifest.Id))
                        {
                            manifest.DirectoryPath = dir;
                            var preview = Path.Combine(dir, "preview.png");
                            if (File.Exists(preview))
                            {
                                manifest.PreviewImagePath = preview;
                            }
                            manifest.IsOfficial = false; // IDs are not authenticated publisher identities.
                            discovered.Add(manifest);
                        }
                    }
                    catch (Exception ex)
                    {
                        DiscoveryErrors.Add(Path.GetFileName(dir) + ": " + ex.Message);
                    }
                }
            }

            // 3. Apply activeOrder if provided, otherwise default to official packs first
            if (activeOrder != null)
            {
                var orderMap = activeOrder.Select((id, index) => new { id, index }).ToDictionary(x => x.id, x => x.index);
                discovered = discovered
                    .OrderBy(p => orderMap.TryGetValue(p.Id, out var idx) ? idx : int.MaxValue)
                    .ThenBy(p => p.IsOfficial ? 0 : 1)
                    .ThenBy(p => p.Name)
                    .ToList();

                foreach (var p in discovered)
                {
                    p.IsEnabled = activeOrder.Contains(p.Id);
                }
            }
            else
            {
                discovered = discovered
                    .OrderBy(p => p.IsOfficial ? 0 : 1)
                    .ThenBy(p => p.Name)
                    .ToList();
                foreach (var p in discovered) p.IsEnabled = false;
            }

            for (int i = 0; i < discovered.Count; i++)
            {
                discovered[i].Priority = i;
                _packs.Add(discovered[i]);
            }
        }

        /// <summary>Read pack metadata and replace its extracted local directory.</summary>
        /// <remarks>
        /// Verification completes in staging before activation. A previous version is
        /// retained for rollback; manifest hashes do not authenticate the publisher.
        /// </remarks>
        public PackManifest InstallPack(string archivePath, bool autoDeleteSource = false,
            IProgress<PackInstallProgress>? progress = null)
        {
            if (!File.Exists(archivePath))
            {
                throw new FileNotFoundException("Asset pack file not found", archivePath);
            }

            var manifest = PackStorage.Install(_modsRoot, archivePath, GameId, progress);
            return RegisterInstalled(manifest, archivePath, autoDeleteSource);
        }

        public async System.Threading.Tasks.Task<PackManifest> InstallPackAsync(string archivePath,
            IProgress<PackInstallProgress>? progress = null)
        {
            var manifest = await System.Threading.Tasks.Task.Run(() => PackStorage.Install(_modsRoot, archivePath, GameId, progress));
            return RegisterInstalled(manifest, archivePath, false);
        }

        private PackManifest RegisterInstalled(PackManifest manifest, string archivePath, bool autoDeleteSource)
        {
            var preview = Path.Combine(manifest.DirectoryPath, "preview.png");
            if (File.Exists(preview)) manifest.PreviewImagePath = preview;
            // Remove existing entry with same ID if present
            var existing = _packs.FirstOrDefault(p => p.Id == manifest.Id);
            if (existing != null)
            {
                manifest.IsEnabled = existing.IsEnabled;
                var index = _packs.IndexOf(existing);
                _packs[index] = manifest;
            }
            else _packs.Insert(0, manifest);
            for (int i = 0; i < _packs.Count; i++) _packs[i].Priority = i;

            if (autoDeleteSource && Path.GetDirectoryName(archivePath) == _modsRoot)
            {
                try { File.Delete(archivePath); } catch { }
            }

            return manifest;
        }

        /// <summary>Delete the discovered directory and remove its collection entry.</summary>
        /// <remarks>Only launcher-owned discovered state is intended; caller paths are not validated here.</remarks>
        public bool UninstallPack(PackManifest pack)
        {
            if (pack == null) return false;

            var target = PackStorage.Resolve(_modsRoot, PackStorage.ValidateId(pack.Id));
            if (!string.Equals(Path.GetFullPath(pack.DirectoryPath), target, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Cannot uninstall content outside its owned pack directory.");
            using (var storageLock = PackStorage.Lock(_modsRoot))
            {
                var previous = PackStorage.Resolve(_modsRoot, ".rollback-" + pack.Id);
                if (Directory.Exists(previous)) PackStorage.DeleteOwnedTree(previous);
                if (Directory.Exists(target)) PackStorage.DeleteOwnedTree(target);
            }

            _packs.Remove(pack);
            for (int i = 0; i < _packs.Count; i++) _packs[i].Priority = i;
            return true;
        }

        /// <summary>Swap with the retained previous version without changing enabled order.</summary>
        public void RollbackPack(PackManifest pack)
        {
            using var storageLock = PackStorage.Lock(_modsRoot);
            var target = PackStorage.Resolve(_modsRoot, PackStorage.ValidateId(pack.Id));
            var previous = PackStorage.Resolve(_modsRoot, ".rollback-" + pack.Id);
            if (!Directory.Exists(previous)) throw new InvalidOperationException("No previous version is available.");
            var restored = PackStorage.ReadManifest(Path.Combine(previous, "pack.json"));
            GameCatalog.RequirePackTarget(restored.GameId, GameId);
            if (restored.Id != pack.Id) throw new InvalidDataException("Rollback identity mismatch.");
            // Keep the previous directory until it has been activated; a failed move restores it.
            var swap = PackStorage.Resolve(_modsRoot, ".staging-" + Guid.NewGuid().ToString("N"));
            Directory.Move(target, swap);
            try { Directory.Move(previous, target); }
            catch { Directory.Move(swap, target); throw; }
            Directory.Move(swap, previous);
            restored.DirectoryPath = target;
            restored.IsEnabled = pack.IsEnabled;
            restored.Priority = pack.Priority;
            _packs[_packs.IndexOf(pack)] = restored;
        }

        /// <summary>Move a discovered pack by an index offset and renumber display priorities.</summary>
        public void MovePriority(PackManifest pack, int direction)
        {
            int oldIndex = _packs.IndexOf(pack);
            if (oldIndex < 0) return;

            int newIndex = oldIndex + direction;
            if (newIndex < 0 || newIndex >= _packs.Count) return;

            _packs.Move(oldIndex, newIndex);
            for (int i = 0; i < _packs.Count; i++) _packs[i].Priority = i;
        }

        /// <summary>Report duplicate relative paths; do not copy or merge their contents.</summary>
        public List<PackConflict> InspectConflicts()
        {
            var conflicts = new List<PackConflict>();
            var activePacks = _packs.Where(p => p.IsEnabled).ToList();
            var claimedFiles = new Dictionary<string, PackManifest>(StringComparer.OrdinalIgnoreCase);

            foreach (var pack in activePacks)
            {
                if (!Directory.Exists(pack.DirectoryPath)) continue;

                if (pack.SchemaVersion == 2)
                {
                    if (pack.NativePayload?.Profile == SkinPack.Profile)
                        foreach (var skin in SkinPack.Read(pack.DirectoryPath, pack))
                        {
                            var key = "skin/" + skin.Id;
                            if (claimedFiles.TryGetValue(key, out var winner))
                                conflicts.Add(new PackConflict { RelativePath = key, WinningPackName = winner.Name, OverriddenPackName = pack.Name });
                            else claimedFiles[key] = pack;
                        }
                    if (pack.NativePayload?.Profile == CinematicPack.Profile)
                        foreach (var clip in CinematicPack.Read(pack.DirectoryPath, pack).Where(c => c.Replaces != null))
                        {
                            var key = "cinematic/" + clip.Replaces;
                            if (claimedFiles.TryGetValue(key, out var winner))
                                conflicts.Add(new PackConflict { RelativePath = key, WinningPackName = winner.Name, OverriddenPackName = pack.Name });
                            else claimedFiles[key] = pack;
                        }
                    if (pack.NativePayload?.Profile == UiPack.Profile)
                    {
                        var key = "ui/" + UiPack.Read(pack.DirectoryPath, pack).Kind;
                        if (claimedFiles.TryGetValue(key, out var winner))
                            conflicts.Add(new PackConflict { RelativePath = key, WinningPackName = winner.Name, OverriddenPackName = pack.Name });
                        else claimedFiles[key] = pack;
                    }
                    if (pack.NativePayload?.Profile == MusicPack.Profile)
                    {
                        const string key = "music/cd-soundtrack";
                        if (claimedFiles.TryGetValue(key, out var winner))
                            conflicts.Add(new PackConflict { RelativePath = key, WinningPackName = winner.Name, OverriddenPackName = pack.Name });
                        else claimedFiles[key] = pack;
                    }
                    foreach (var id in pack.Provides?.Mechs ?? new List<string>())
                    {
                        var key = "chassis/" + id;
                        if (claimedFiles.TryGetValue(key, out var winner))
                            conflicts.Add(new PackConflict { RelativePath = key, WinningPackName = winner.Name, OverriddenPackName = pack.Name });
                        else claimedFiles[key] = pack;
                    }
                    continue;
                }
                var files = Directory.GetFiles(pack.DirectoryPath, "*.*", SearchOption.AllDirectories);
                foreach (var file in files)
                {
                    var rel = Path.GetRelativePath(pack.DirectoryPath, file);
                    if (rel.Equals("pack.json", StringComparison.OrdinalIgnoreCase) ||
                        rel.Equals("preview.png", StringComparison.OrdinalIgnoreCase))
                    {
                        continue;
                    }

                    if (claimedFiles.TryGetValue(rel, out var winningPack))
                    {
                        conflicts.Add(new PackConflict
                        {
                            RelativePath = rel,
                            WinningPackName = winningPack.Name,
                            OverriddenPackName = pack.Name
                        });
                    }
                    else
                    {
                        claimedFiles[rel] = pack;
                    }
                }
            }

            return conflicts;
        }

        /// <summary>Snapshot enabled IDs in precedence order for settings persistence.</summary>
        public List<string> GetActivePackIds()
        {
            return _packs.Where(p => p.IsEnabled).Select(p => p.Id).ToList();
        }

        /// <summary>Snapshot enabled local directories without validating or composing their payloads.</summary>
        public List<string> GetActivePackDirectories()
        {
            return _packs.Where(p => p.IsEnabled).Select(p => p.DirectoryPath).ToList();
        }
    }
}
