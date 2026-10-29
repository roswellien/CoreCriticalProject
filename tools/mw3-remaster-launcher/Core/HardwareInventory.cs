using System.Management;
using System.Runtime.InteropServices;

namespace MW3RemasterLauncher.Core;

public sealed record ProcessorInventory(string? Manufacturer, string? Model,
    uint? PhysicalCores, uint? LogicalProcessors);

public sealed record MemoryModuleInventory(ulong? CapacityBytes, string? Type,
    uint? ConfiguredSpeedMhz);

public sealed record MemoryInventory(ulong? TotalBytes,
    IReadOnlyList<MemoryModuleInventory> Modules);

public sealed record GraphicsAdapterInventory(string Name,
    ulong? DedicatedVideoMemoryBytes, ulong? SharedSystemMemoryBytes,
    string? DriverVersion, DateTime? DriverDate);

public sealed record HardwareInventoryData(IReadOnlyList<ProcessorInventory> Processors,
    MemoryInventory? Memory, IReadOnlyList<GraphicsAdapterInventory> GraphicsAdapters);

/// <summary>
/// Collects a small, explicit hardware inventory for crash diagnostics. The WMI
/// queries request only model and capability fields, never device serials.
/// </summary>
public static class HardwareInventory
{
    private static readonly Guid DxgiFactory1Id = new("770aae78-f26f-4dba-a829-253c83d1b387");
    private const int DxgiErrorNotFound = unchecked((int)0x887A0002);

    [DllImport("dxgi.dll", EntryPoint = "CreateDXGIFactory1", PreserveSig = true)]
    private static extern int CreateDxgiFactory1(ref Guid interfaceId, out IntPtr factory);

    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    private delegate int EnumAdapters1Delegate(IntPtr factory, uint adapterIndex, out IntPtr adapter);

    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    private delegate int GetDescription1Delegate(IntPtr adapter, out DxgiAdapterDescription1 description);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct DxgiAdapterDescription1
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)]
        public string Description;
        public uint VendorId;
        public uint DeviceId;
        public uint SubsystemId;
        public uint Revision;
        public UIntPtr DedicatedVideoMemory;
        public UIntPtr DedicatedSystemMemory;
        public UIntPtr SharedSystemMemory;
        public uint LuidLowPart;
        public int LuidHighPart;
        public uint Flags;
    }

    private sealed record DxgiAdapter(string Name, ulong DedicatedVideoMemoryBytes,
        ulong SharedSystemMemoryBytes);
    private sealed record DriverDetails(string Name, string? Version, DateTime? Date);

    public static HardwareInventoryData Capture()
    {
        var processors = ReadProcessors();
        var memory = ReadMemory();
        var graphicsAdapters = CombineGraphicsAdapters(ReadDxgiAdapters(), ReadDriverDetails());
        return new HardwareInventoryData(processors, memory, graphicsAdapters);
    }

    public static string MemoryTypeName(ulong? smbiosType, ulong? legacyType)
    {
        if (smbiosType.HasValue)
        {
            return smbiosType.Value switch
            {
                18 => "DDR",
                19 => "DDR2",
                20 => "DDR2 FB-DIMM",
                24 => "DDR3",
                25 => "FBD2",
                26 => "DDR4",
                27 => "LPDDR",
                28 => "LPDDR2",
                29 => "LPDDR3",
                30 => "LPDDR4",
                34 => "DDR5",
                35 => "LPDDR5",
                _ => $"Unknown (SMBIOS type {smbiosType})"
            };
        }

        if (!legacyType.HasValue) return "Unknown";
        return legacyType.Value switch
        {
            20 => "DDR",
            21 => "DDR2",
            22 => "DDR2 FB-DIMM",
            24 => "DDR3",
            25 => "FBD2",
            26 => "DDR4",
            27 => "LPDDR3",
            28 => "LPDDR4",
            29 => "LPDDR4X",
            30 => "LPDDR5",
            34 => "DDR5",
            35 => "LPDDR5X",
            _ => $"Unknown (legacy type {legacyType})"
        };
    }

    private static IReadOnlyList<ProcessorInventory> ReadProcessors()
    {
        try
        {
            return Query("SELECT Manufacturer, Name, NumberOfCores, NumberOfLogicalProcessors FROM Win32_Processor",
                row => new ProcessorInventory(ReadString(row, "Manufacturer"), ReadString(row, "Name"),
                    ReadUInt32(row, "NumberOfCores"), ReadUInt32(row, "NumberOfLogicalProcessors")));
        }
        catch
        {
            return Array.Empty<ProcessorInventory>();
        }
    }

    private static MemoryInventory? ReadMemory()
    {
        try
        {
            var modules = Query("SELECT Capacity, MemoryType, SMBIOSMemoryType, ConfiguredClockSpeed FROM Win32_PhysicalMemory",
                row => new MemoryModuleInventory(ReadUInt64(row, "Capacity"),
                    MemoryTypeName(ReadUInt64(row, "SMBIOSMemoryType"), ReadUInt64(row, "MemoryType")),
                    ReadUInt32(row, "ConfiguredClockSpeed")));
            var knownCapacity = modules.Where(module => module.CapacityBytes.HasValue)
                .Select(module => module.CapacityBytes!.Value).ToArray();
            ulong? totalBytes = knownCapacity.Length == 0 ? null : knownCapacity.Aggregate(0UL, (total, capacity) =>
                ulong.MaxValue - total < capacity ? ulong.MaxValue : total + capacity);
            return new MemoryInventory(totalBytes, modules);
        }
        catch
        {
            return null;
        }
    }

    private static IReadOnlyList<DriverDetails> ReadDriverDetails()
    {
        try
        {
            return Query("SELECT Name, DriverVersion, DriverDate FROM Win32_VideoController",
                row => new DriverDetails(ReadString(row, "Name") ?? "Unknown graphics adapter",
                    ReadString(row, "DriverVersion"), ReadDriverDate(ReadString(row, "DriverDate"))));
        }
        catch
        {
            return Array.Empty<DriverDetails>();
        }
    }

    private static IReadOnlyList<T> Query<T>(string query, Func<ManagementBaseObject, T> readRow)
    {
        using var searcher = new ManagementObjectSearcher(query);
        using var results = searcher.Get();
        var rows = new List<T>();
        foreach (ManagementBaseObject row in results)
        {
            using (row)
                rows.Add(readRow(row));
        }
        return rows;
    }

    private static string? ReadString(ManagementBaseObject row, string property)
    {
        return row[property] is string value && !string.IsNullOrWhiteSpace(value) ? value.Trim() : null;
    }

    private static uint? ReadUInt32(ManagementBaseObject row, string property)
    {
        try { return row[property] is null ? null : Convert.ToUInt32(row[property]); }
        catch (FormatException) { return null; }
        catch (InvalidCastException) { return null; }
        catch (OverflowException) { return null; }
    }

    private static ulong? ReadUInt64(ManagementBaseObject row, string property)
    {
        try { return row[property] is null ? null : Convert.ToUInt64(row[property]); }
        catch (FormatException) { return null; }
        catch (InvalidCastException) { return null; }
        catch (OverflowException) { return null; }
    }

    private static DateTime? ReadDriverDate(string? value)
    {
        if (string.IsNullOrWhiteSpace(value)) return null;
        try { return ManagementDateTimeConverter.ToDateTime(value); }
        catch (ArgumentException) { return null; }
        catch (FormatException) { return null; }
    }

    private static IReadOnlyList<DxgiAdapter> ReadDxgiAdapters()
    {
        var adapters = new List<DxgiAdapter>();
        IntPtr factory = IntPtr.Zero;
        try
        {
            var interfaceId = DxgiFactory1Id;
            if (CreateDxgiFactory1(ref interfaceId, out factory) < 0 || factory == IntPtr.Zero)
                return adapters;

            var factoryVtable = Marshal.ReadIntPtr(factory);
            var enumerateAddress = Marshal.ReadIntPtr(factoryVtable, 12 * IntPtr.Size);
            var enumerate = Marshal.GetDelegateForFunctionPointer<EnumAdapters1Delegate>(enumerateAddress);
            for (uint index = 0; ; index++)
            {
                var result = enumerate(factory, index, out var adapter);
                if (result == DxgiErrorNotFound) break;
                if (result < 0 || adapter == IntPtr.Zero) break;
                try
                {
                    var adapterVtable = Marshal.ReadIntPtr(adapter);
                    var descriptionAddress = Marshal.ReadIntPtr(adapterVtable, 10 * IntPtr.Size);
                    var getDescription = Marshal.GetDelegateForFunctionPointer<GetDescription1Delegate>(descriptionAddress);
                    if (getDescription(adapter, out var description) >= 0 &&
                        !string.IsNullOrWhiteSpace(description.Description))
                    {
                        adapters.Add(new DxgiAdapter(description.Description.Trim(),
                            description.DedicatedVideoMemory.ToUInt64(),
                            description.SharedSystemMemory.ToUInt64()));
                    }
                }
                finally
                {
                    Marshal.Release(adapter);
                }
            }
        }
        catch
        {
            // Adapter discovery is best effort; WMI driver details remain useful without DXGI.
        }
        finally
        {
            if (factory != IntPtr.Zero) Marshal.Release(factory);
        }
        return adapters;
    }

    private static IReadOnlyList<GraphicsAdapterInventory> CombineGraphicsAdapters(
        IReadOnlyList<DxgiAdapter> adapters, IReadOnlyList<DriverDetails> drivers)
    {
        var graphics = new List<GraphicsAdapterInventory>();
        var matchedDrivers = new HashSet<int>();
        foreach (var adapter in adapters)
        {
            var driverIndex = FindDriver(adapter.Name, drivers, matchedDrivers);
            if (driverIndex >= 0) matchedDrivers.Add(driverIndex);
            var driver = driverIndex >= 0 ? drivers[driverIndex] : null;
            graphics.Add(new GraphicsAdapterInventory(adapter.Name, adapter.DedicatedVideoMemoryBytes,
                adapter.SharedSystemMemoryBytes, driver?.Version, driver?.Date));
        }
        for (var index = 0; index < drivers.Count; index++)
        {
            if (matchedDrivers.Contains(index)) continue;
            var driver = drivers[index];
            graphics.Add(new GraphicsAdapterInventory(driver.Name, null, null, driver.Version, driver.Date));
        }
        return graphics;
    }

    private static int FindDriver(string adapterName, IReadOnlyList<DriverDetails> drivers,
        IReadOnlySet<int> matchedDrivers)
    {
        for (var index = 0; index < drivers.Count; index++)
        {
            if (!matchedDrivers.Contains(index) &&
                string.Equals(adapterName, drivers[index].Name, StringComparison.OrdinalIgnoreCase))
                return index;
        }
        return -1;
    }
}
