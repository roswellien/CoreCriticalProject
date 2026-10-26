using System.IO;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

/// <summary>Installed delivery policy. Keys remain in the existing strict update-trust.json.</summary>
public sealed record OnlineUpdateConfiguration(int SchemaVersion, string CatalogUrl, string Channel,
    string DeliveryPolicy, string[] ApprovedHosts, string? BrokerUrl = null)
{
    public static OnlineUpdateConfiguration Read(string application)
    {
        var path = Path.Combine(application, "online-updates.json");
        if (!File.Exists(path))
            throw new InvalidDataException("Online updates are not configured. You can still import a signed update file.");
        PackStorage.EnsureNoLinks(path);
        if (new FileInfo(path).Length > 64 * 1024) throw new InvalidDataException("Online update configuration is too large.");
        var config = JsonSerializer.Deserialize<OnlineUpdateConfiguration>(File.ReadAllBytes(path), RuntimeUpdates.Json)
            ?? throw new InvalidDataException("Empty online update configuration.");
        config.Validate();
        return config;
    }

    public void Validate()
    {
        if (SchemaVersion != 1 || DeliveryPolicy is not ("private-broker-v1" or "public-readonly-v1"))
            throw new InvalidDataException("Unsupported online update delivery configuration.");
        PackStorage.ValidateId(Channel);
        if (ApprovedHosts == null || ApprovedHosts.Length is < 1 or > 16 ||
            ApprovedHosts.Distinct(StringComparer.OrdinalIgnoreCase).Count() != ApprovedHosts.Length ||
            ApprovedHosts.Any(host => Uri.CheckHostName(host) != UriHostNameType.Dns))
            throw new InvalidDataException("Invalid approved update hosts.");
        Destination(CatalogUrl);
        if (DeliveryPolicy == "private-broker-v1" && string.IsNullOrWhiteSpace(BrokerUrl))
            throw new InvalidDataException("Private updates require a configured sign-in service.");
        if (BrokerUrl != null) Destination(BrokerUrl);
    }

    public Uri Destination(string value)
    {
        if (!Uri.TryCreate(value, UriKind.Absolute, out var uri) || uri.Scheme != Uri.UriSchemeHttps ||
            !uri.IsDefaultPort || uri.UserInfo.Length != 0 || uri.Fragment.Length != 0 ||
            !ApprovedHosts.Contains(uri.IdnHost, StringComparer.OrdinalIgnoreCase))
            throw new InvalidDataException("Update delivery address is not an approved HTTPS destination.");
        return uri;
    }
}
