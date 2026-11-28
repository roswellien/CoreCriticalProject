using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Numerics;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core
{
    /// <summary>
    /// Exception thrown when a schema uses keywords not in the supported JSON Schema subset.
    /// </summary>
    public class UnsupportedSchemaException : Exception
    {
        public UnsupportedSchemaException(string message) : base(message) { }
    }

    /// <summary>
    /// One way a JSON value breaks its schema.
    /// Path is where in the value (JSON Pointer format, "" for root).
    /// Keyword is the schema keyword that failed (e.g., "additionalProperties", "required", "pattern").
    /// </summary>
    public sealed record SchemaViolation(string Path, string Keyword, string Message);

    /// <summary>
    /// Validates a JSON value against the small subset of JSON Schema used by content packs.
    /// Faithfully mirrors tools/packs/json_schema_subset.py.
    /// </summary>
    public static class JsonSchemaSubset
    {
        // Keywords that describe the schema and never reject a value.
        private static readonly HashSet<string> AnnotationKeywords = new(StringComparer.Ordinal)
        {
            "$schema", "$id", "$defs", "title", "description"
        };

        // Keywords that this subset validator knows how to check.
        private static readonly HashSet<string> CheckedKeywords = new(StringComparer.Ordinal)
        {
            "$ref", "type", "const", "enum", "required", "properties",
            "additionalProperties", "items", "pattern", "minLength",
            "maxLength", "minimum", "maximum", "minItems", "maxItems", "uniqueItems"
        };

        /// <summary>
        /// Collects all schema violations in the given JSON value.
        /// </summary>
        public static List<SchemaViolation> FindViolations(JsonElement value, JsonElement schema)
        {
            var violations = new List<SchemaViolation>();
            Check(value, schema, schema, "", violations);
            return violations;
        }

        private static JsonElement ResolveReference(string reference, JsonElement rootSchema)
        {
            const string prefix = "#/$defs/";
            if (!reference.StartsWith(prefix, StringComparison.Ordinal))
            {
                throw new UnsupportedSchemaException($"only {prefix}<name> references are supported: {reference}");
            }

            var name = reference[prefix.Length..];
            if (!rootSchema.TryGetProperty("$defs", out var defs) || !defs.TryGetProperty(name, out var definition))
            {
                throw new UnsupportedSchemaException($"no such definition: {reference}");
            }

            return definition;
        }

        private static bool IsType(JsonElement value, string typeName)
        {
            return typeName switch
            {
                "object" => value.ValueKind == JsonValueKind.Object,
                "array" => value.ValueKind == JsonValueKind.Array,
                "string" => value.ValueKind == JsonValueKind.String,
                "boolean" => value.ValueKind == JsonValueKind.True || value.ValueKind == JsonValueKind.False,
                "integer" => IsInteger(value),
                "number" => value.ValueKind == JsonValueKind.Number,
                _ => throw new UnsupportedSchemaException($"unsupported type: {typeName}")
            };
        }

        // Python's reference reader distinguishes integer tokens from 1.0 and 1e0,
        // even when those tokens describe a mathematically integral value.
        private static bool IsInteger(JsonElement value) =>
            value.ValueKind == JsonValueKind.Number &&
            BigInteger.TryParse(value.GetRawText(), out _);

        private static int CompareIntegerToDouble(BigInteger integer, double number)
        {
            if (double.IsPositiveInfinity(number)) return -1;
            if (double.IsNegativeInfinity(number)) return 1;
            var wholePart = new BigInteger(number);
            var comparison = integer.CompareTo(wholePart);
            if (comparison != 0 || Math.Truncate(number) == number) return comparison;
            return number > 0 ? -1 : 1;
        }

        private static int CompareNumbers(JsonElement left, JsonElement right)
        {
            if (IsInteger(left))
            {
                var integer = BigInteger.Parse(left.GetRawText());
                if (IsInteger(right)) return integer.CompareTo(BigInteger.Parse(right.GetRawText()));
                return CompareIntegerToDouble(integer, right.GetDouble());
            }
            if (IsInteger(right))
                return -CompareIntegerToDouble(BigInteger.Parse(right.GetRawText()), left.GetDouble());
            return left.GetDouble().CompareTo(right.GetDouble());
        }

        private static bool SameJsonValue(JsonElement left, JsonElement right, bool requireSameType = true)
        {
            // Python compares the outer types strictly, but nested list/dict equality
            // uses ordinary Python equality (including true == 1).
            if (!requireSameType && left.ValueKind != right.ValueKind)
            {
                bool IsNumeric(JsonElement item) => item.ValueKind is JsonValueKind.Number or
                    JsonValueKind.True or JsonValueKind.False;
                double Number(JsonElement item)
                {
                    if (item.ValueKind == JsonValueKind.Number) return item.GetDouble();
                    if (item.ValueKind == JsonValueKind.True) return 1;
                    return 0;
                }
                if (IsNumeric(left) && IsNumeric(right)) return Number(left) == Number(right);
            }
            if (left.ValueKind != right.ValueKind) return false;
            switch (left.ValueKind)
            {
                case JsonValueKind.Null:
                case JsonValueKind.Undefined:
                    return true;
                case JsonValueKind.True:
                case JsonValueKind.False:
                    return left.ValueKind == right.ValueKind;
                case JsonValueKind.Number:
                    if (requireSameType && IsInteger(left) != IsInteger(right)) return false;
                    return CompareNumbers(left, right) == 0;
                case JsonValueKind.String:
                    return string.Equals(left.GetString(), right.GetString(), StringComparison.Ordinal);
                case JsonValueKind.Array:
                    var leftArray = left.EnumerateArray().ToList();
                    var rightArray = right.EnumerateArray().ToList();
                    if (leftArray.Count != rightArray.Count) return false;
                    for (int i = 0; i < leftArray.Count; i++)
                    {
                        if (!SameJsonValue(leftArray[i], rightArray[i], requireSameType: false)) return false;
                    }
                    return true;
                case JsonValueKind.Object:
                    var leftProps = left.EnumerateObject().ToDictionary(p => p.Name, p => p.Value);
                    var rightProps = right.EnumerateObject().ToDictionary(p => p.Name, p => p.Value);
                    if (leftProps.Count != rightProps.Count) return false;
                    foreach (var (k, v) in leftProps)
                    {
                        if (!rightProps.TryGetValue(k, out var rv) || !SameJsonValue(v, rv, requireSameType: false))
                            return false;
                    }
                    return true;
                default:
                    return false;
            }
        }

        private static void Check(JsonElement value, JsonElement schema, JsonElement rootSchema, string path, List<SchemaViolation> violations)
        {
            if (schema.ValueKind != JsonValueKind.Object) return;

            foreach (var prop in schema.EnumerateObject())
            {
                if (!AnnotationKeywords.Contains(prop.Name) && !CheckedKeywords.Contains(prop.Name))
                {
                    throw new UnsupportedSchemaException($"unsupported keywords: {prop.Name}");
                }
            }

            void Report(string keyword, string message)
            {
                violations.Add(new SchemaViolation(path, keyword, message));
            }

            if (schema.TryGetProperty("$ref", out var refElem))
            {
                var refStr = refElem.GetString() ?? "";
                var referenced = ResolveReference(refStr, rootSchema);
                Check(value, referenced, rootSchema, path, violations);
            }

            if (schema.TryGetProperty("type", out var typeElem))
            {
                var expectedType = typeElem.GetString() ?? "";
                if (!IsType(value, expectedType))
                {
                    Report("type", $"expected {expectedType}");
                    // Later keywords assume the expected type; checking them would only add noise.
                    return;
                }
            }

            if (schema.TryGetProperty("const", out var constElem))
            {
                if (!SameJsonValue(value, constElem))
                {
                    Report("const", $"expected {constElem.GetRawText()}");
                }
            }

            if (schema.TryGetProperty("enum", out var enumElem) && enumElem.ValueKind == JsonValueKind.Array)
            {
                bool matched = false;
                foreach (var option in enumElem.EnumerateArray())
                {
                    if (SameJsonValue(value, option))
                    {
                        matched = true;
                        break;
                    }
                }
                if (!matched)
                {
                    Report("enum", $"expected one of {enumElem.GetRawText()}");
                }
            }

            if (value.ValueKind == JsonValueKind.String)
            {
                CheckString(value.GetString() ?? "", schema, Report);
            }
            else if (value.ValueKind == JsonValueKind.Number)
            {
                if (schema.TryGetProperty("minimum", out var minElem))
                {
                    if (CompareNumbers(value, minElem) < 0)
                    {
                        Report("minimum", $"less than {minElem.GetRawText()}");
                    }
                }
                if (schema.TryGetProperty("maximum", out var maxElem))
                {
                    if (CompareNumbers(value, maxElem) > 0)
                    {
                        Report("maximum", $"more than {maxElem.GetRawText()}");
                    }
                }
            }
            else if (value.ValueKind == JsonValueKind.Array)
            {
                CheckArray(value, schema, rootSchema, path, violations, Report);
            }
            else if (value.ValueKind == JsonValueKind.Object)
            {
                CheckObject(value, schema, rootSchema, path, violations, Report);
            }
        }

        private static void CheckString(string value, JsonElement schema, Action<string, string> report)
        {
            var characterCount = value.EnumerateRunes().Count();
            if (schema.TryGetProperty("minLength", out var minLenElem) && minLenElem.TryGetInt32(out var minLen))
            {
                if (characterCount < minLen)
                    report("minLength", $"shorter than {minLen} characters");
            }
            if (schema.TryGetProperty("maxLength", out var maxLenElem) && maxLenElem.TryGetInt32(out var maxLen))
            {
                if (characterCount > maxLen)
                    report("maxLength", $"longer than {maxLen} characters");
            }
            if (schema.TryGetProperty("pattern", out var patternElem))
            {
                var pattern = patternElem.GetString() ?? "";
                if (!Regex.IsMatch(value, pattern))
                {
                    report("pattern", $"does not match {pattern}");
                }
            }
        }

        private static void CheckArray(JsonElement value, JsonElement schema, JsonElement rootSchema, string path, List<SchemaViolation> violations, Action<string, string> report)
        {
            var items = value.EnumerateArray().ToList();
            if (schema.TryGetProperty("minItems", out var minItemsElem) && minItemsElem.TryGetInt32(out var minItems))
            {
                if (items.Count < minItems)
                    report("minItems", $"fewer than {minItems} items");
            }
            if (schema.TryGetProperty("maxItems", out var maxItemsElem) && maxItemsElem.TryGetInt32(out var maxItems))
            {
                if (items.Count > maxItems)
                    report("maxItems", $"more than {maxItems} items");
            }
            if (schema.TryGetProperty("uniqueItems", out var uniqueElem) && uniqueElem.ValueKind == JsonValueKind.True)
            {
                for (int i = 0; i < items.Count; i++)
                {
                    for (int j = 0; j < i; j++)
                    {
                        if (SameJsonValue(items[i], items[j]))
                        {
                            report("uniqueItems", $"item {i} repeats an earlier item");
                            break;
                        }
                    }
                }
            }
            if (schema.TryGetProperty("items", out var itemSchema))
            {
                for (int i = 0; i < items.Count; i++)
                {
                    Check(items[i], itemSchema, rootSchema, $"{path}/{i}", violations);
                }
            }
        }

        private static void CheckObject(JsonElement value, JsonElement schema, JsonElement rootSchema, string path, List<SchemaViolation> violations, Action<string, string> report)
        {
            if (schema.TryGetProperty("required", out var reqElem) && reqElem.ValueKind == JsonValueKind.Array)
            {
                foreach (var r in reqElem.EnumerateArray())
                {
                    var reqName = r.GetString() ?? "";
                    if (!value.TryGetProperty(reqName, out _))
                    {
                        report("required", $"missing {reqName}");
                    }
                }
            }

            Dictionary<string, JsonElement>? knownProperties = null;
            if (schema.TryGetProperty("properties", out var propsElem) && propsElem.ValueKind == JsonValueKind.Object)
            {
                knownProperties = propsElem.EnumerateObject().ToDictionary(p => p.Name, p => p.Value, StringComparer.Ordinal);
            }

            JsonElement? additionalPropSchema = null;
            bool additionalAllowed = true;
            if (schema.TryGetProperty("additionalProperties", out var addElem))
            {
                if (addElem.ValueKind == JsonValueKind.False)
                {
                    additionalAllowed = false;
                }
                else if (addElem.ValueKind == JsonValueKind.Object)
                {
                    additionalPropSchema = addElem;
                }
            }

            foreach (var prop in value.EnumerateObject())
            {
                var memberPath = $"{path}/{prop.Name}";
                if (knownProperties != null && knownProperties.TryGetValue(prop.Name, out var propSchema))
                {
                    Check(prop.Value, propSchema, rootSchema, memberPath, violations);
                }
                else if (!additionalAllowed)
                {
                    violations.Add(new SchemaViolation(memberPath, "additionalProperties", "unknown field"));
                }
                else if (additionalPropSchema.HasValue)
                {
                    Check(prop.Value, additionalPropSchema.Value, rootSchema, memberPath, violations);
                }
            }
        }
    }
}
