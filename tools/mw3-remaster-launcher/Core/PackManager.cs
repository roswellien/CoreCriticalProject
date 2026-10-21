using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.Json;

namespace MW3RemasterLauncher.Core
{
    public class PackConflict
    {
        public string RelativePath { get; set; } = string.Empty;
        public string WinningPackName { get; set; } = string.Empty;
        public string OverriddenPackName { get; set; } = string.Empty;
    }

    public class PackManager
    {
        private readonly string _modsRoot;
        private readonly ObservableCollection<PackManifest> _packs = new();

        public ObservableCollection<PackManifest> Packs => _packs;

        public PackManager(string basePath)
        {
            _modsRoot = Path.Combine(basePath, "mods");
            if (!Directory.Exists(_modsRoot))
            {
                Directory.CreateDirectory(_modsRoot);
            }
        }

        public void RefreshPacks(List<string>? activeOrder = null)
        {
            _packs.Clear();
            if (!Directory.Exists(_modsRoot)) return;

            var discovered = new List<PackManifest>();

            // 1. Scan subdirectories under mods/
            foreach (var dir in Directory.GetDirectories(_modsRoot))
            {
                var manifestFile = Path.Combine(dir, "pack.json");
                if (File.Exists(manifestFile))
                {
                    try
                    {
                        var json = File.ReadAllText(manifestFile);
                        var manifest = JsonSerializer.Deserialize<PackManifest>(json);
                        if (manifest != null && !string.IsNullOrWhiteSpace(manifest.Id))
                        {
                            manifest.DirectoryPath = dir;
                            var preview = Path.Combine(dir, "preview.png");
                            if (File.Exists(preview))
                            {
                                manifest.PreviewImagePath = preview;
                            }
                            manifest.IsOfficial = manifest.Id.StartsWith("com.mw3remaster.");
                            discovered.Add(manifest);
                        }
                    }
                    catch
                    {
                        // Ignore malformed packs
                    }
                }
            }

            // 2. Scan standalone .mw3pack or .zip files directly in mods/ and extract them if needed
            foreach (var archive in Directory.GetFiles(_modsRoot, "*.mw3pack").Concat(Directory.GetFiles(_modsRoot, "*.zip")))
            {
                try
                {
                    InstallPack(archive, autoDeleteSource: false);
                }
                catch
                {
                    // Ignore non-pack zips
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
            }

            for (int i = 0; i < discovered.Count; i++)
            {
                discovered[i].Priority = i;
                _packs.Add(discovered[i]);
            }
        }

        public PackManifest InstallPack(string archivePath, bool autoDeleteSource = false)
        {
            if (!File.Exists(archivePath))
            {
                throw new FileNotFoundException("Asset pack file not found", archivePath);
            }

            using var archive = ZipFile.OpenRead(archivePath);
            var manifestEntry = archive.Entries.FirstOrDefault(e => e.FullName.Equals("pack.json", StringComparison.OrdinalIgnoreCase) || e.FullName.EndsWith("/pack.json", StringComparison.OrdinalIgnoreCase));
            if (manifestEntry == null)
            {
                throw new InvalidOperationException("Archive does not contain a valid pack.json manifest.");
            }

            PackManifest? manifest;
            using (var stream = manifestEntry.Open())
            {
                manifest = JsonSerializer.Deserialize<PackManifest>(stream);
            }

            if (manifest == null || string.IsNullOrWhiteSpace(manifest.Id))
            {
                throw new InvalidOperationException("Manifest in archive is invalid or missing 'id'.");
            }

            var targetDir = Path.Combine(_modsRoot, manifest.Id);
            if (Directory.Exists(targetDir))
            {
                Directory.Delete(targetDir, true);
            }
            Directory.CreateDirectory(targetDir);

            // Determine if entries are inside a root folder
            var rootPrefix = string.Empty;
            if (manifestEntry.FullName.Contains('/'))
            {
                rootPrefix = manifestEntry.FullName.Substring(0, manifestEntry.FullName.LastIndexOf('/') + 1);
            }

            foreach (var entry in archive.Entries)
            {
                var relativePath = entry.FullName;
                if (!string.IsNullOrEmpty(rootPrefix) && relativePath.StartsWith(rootPrefix))
                {
                    relativePath = relativePath.Substring(rootPrefix.Length);
                }

                if (string.IsNullOrWhiteSpace(relativePath)) continue;

                var destPath = Path.Combine(targetDir, relativePath.Replace('/', Path.DirectorySeparatorChar));
                if (entry.FullName.EndsWith("/") || entry.FullName.EndsWith("\\"))
                {
                    Directory.CreateDirectory(destPath);
                }
                else
                {
                    var parent = Path.GetDirectoryName(destPath);
                    if (!string.IsNullOrEmpty(parent) && !Directory.Exists(parent))
                    {
                        Directory.CreateDirectory(parent);
                    }
                    entry.ExtractToFile(destPath, true);
                }
            }

            manifest.DirectoryPath = targetDir;
            var preview = Path.Combine(targetDir, "preview.png");
            if (File.Exists(preview))
            {
                manifest.PreviewImagePath = preview;
            }

            // Remove existing entry with same ID if present
            var existing = _packs.FirstOrDefault(p => p.Id == manifest.Id);
            if (existing != null)
            {
                _packs.Remove(existing);
            }

            _packs.Insert(0, manifest);
            for (int i = 0; i < _packs.Count; i++) _packs[i].Priority = i;

            if (autoDeleteSource && Path.GetDirectoryName(archivePath) == _modsRoot)
            {
                try { File.Delete(archivePath); } catch { }
            }

            return manifest;
        }

        public bool UninstallPack(PackManifest pack)
        {
            if (pack == null) return false;

            if (Directory.Exists(pack.DirectoryPath))
            {
                try
                {
                    Directory.Delete(pack.DirectoryPath, true);
                }
                catch (Exception ex)
                {
                    throw new IOException($"Could not delete mod folder: {ex.Message}", ex);
                }
            }

            _packs.Remove(pack);
            for (int i = 0; i < _packs.Count; i++) _packs[i].Priority = i;
            return true;
        }

        public void MovePriority(PackManifest pack, int direction)
        {
            int oldIndex = _packs.IndexOf(pack);
            if (oldIndex < 0) return;

            int newIndex = oldIndex + direction;
            if (newIndex < 0 || newIndex >= _packs.Count) return;

            _packs.Move(oldIndex, newIndex);
            for (int i = 0; i < _packs.Count; i++) _packs[i].Priority = i;
        }

        public List<PackConflict> InspectConflicts()
        {
            var conflicts = new List<PackConflict>();
            var activePacks = _packs.Where(p => p.IsEnabled).ToList();
            var claimedFiles = new Dictionary<string, PackManifest>(StringComparer.OrdinalIgnoreCase);

            foreach (var pack in activePacks)
            {
                if (!Directory.Exists(pack.DirectoryPath)) continue;

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

        public List<string> GetActivePackIds()
        {
            return _packs.Where(p => p.IsEnabled).Select(p => p.Id).ToList();
        }

        public List<string> GetActivePackDirectories()
        {
            return _packs.Where(p => p.IsEnabled).Select(p => p.DirectoryPath).ToList();
        }
    }
}
