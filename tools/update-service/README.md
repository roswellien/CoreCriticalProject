# Online update delivery

Core Critical 1.0.38 adds **Settings & Steam → Updates**. Existing installations
need one launcher setup or `.ccupdate` upgrade to acquire this feature. Launcher
and MW3 versions remain independent: the initial catalog promotes launcher
1.0.38-preview and precompiled runtime 1.0.37.

The owner authorized public **update-only** downloads on October 25. The Worker
serves an explicit path-to-object allowlist using the existing private R2
binding. It accepts GET/HEAD only and never accepts a bucket key from a caller.
It does not expose packs, ISO/patch files, bucket listing, write operations or
the private download website. The bucket's public development URL stays disabled.
See [Cloudflare's R2 binding API](https://developers.cloudflare.com/r2/api/workers/workers-api-reference/).

The installed `online-updates.json` contains the approved HTTPS origin and
channel. It is separate from the existing strict `update-trust.json`. Catalogs
and individual packages use installed trusted RSA public keys; fetching an
unknown key from the feed is not supported. The catalog signature covers exact
decoded payload bytes. Each entry identifies a product, numeric/public version,
release sequence, minimum launcher, contract, metadata and payload hashes/sizes,
and exact filenames. Initial delivery supports Windows x64, the promoted
playtest channel, launcher-inno-v1 and precompiled MW3 mw3-local-runtime-v1.
It does not enroll users in unpromoted experiments or implement other games.

The client rejects expired/future catalogs, older/conflicting catalog sequences,
unapproved hosts, redirects, unsupported targets/contracts and package/catalog
disagreements. It downloads outside installation locks, shows byte progress,
and caches by application/product/sequence/hash. Strong ETag and validated
Range/If-Range permit resume. A full 200 restarts the transfer; every finished
artifact is completely hashed before use. The bounded retries distinguish
user cancellation, stalled bodies and sign-in/HTML responses.

A saved plan survives launcher replacement. The restarted launcher offers to
continue; it rechecks online promotion, the saved signed catalog and the owned
helper result before installing the runtime. Runtime installation still uses
the original-input checks, complete validation and atomic selection in
`RuntimeUpdates`. Its rollback retains the sequence high-water mark. The
launch/install gate is acquired before product mutation locks; the launcher
holds its launch lease through its coordinator session. It does not terminate
a player's game. Whole-launcher transactional rollback is not implemented.

## Publishing

1. Build/sign the normal launcher and precompiled runtime packages using the
   existing builders. Give each changed product a new version/sequence. Retain
   `<version>.ccupdate`, `<version>.mw3update`, and each matching `<version>.zip`
   in separate product directories. Installer filenames come from the receipt.
2. Run `build_catalog.py --launcher <version>.ccupdate --runtime <version>.mw3update
   --base-url <approved-origin> --sequence <new-catalog-sequence> --output <fresh-dir>
   --signing-key <external-private-key-path> --key-id <installed-key-id>
   --trust-file <installed-update-trust.json>`. This verifies package signatures
   and payload pins and emits signed discovery metadata plus `publication.json`.
   It performs no uploads. Only explicitly supplied promoted releases are listed.
   Use `--launcher-notes-file <UTF-8-file>` for release-specific launcher notes
   (at most 16,384 characters). Unchanged runtime releases retain their own version.
3. Upload the four immutable metadata/payload objects specified by that receipt.
   Preserve historical artifacts and compatibility URLs. Extend the Worker's
   existing allowlist rather than removing older entries or repointing an
   immutable versioned URL. Worker configuration and publishing credentials
   remain on the publishing machine, outside release inputs.
4. Download all four objects through the actual public endpoint; verify their
   full sizes/SHA-256 and resumed ranges. Run an actual installed upgrade check.
5. Archive the signed catalog under its sequence, then promote its single
   `online-updates/catalogs/playtest/catalog.json` object last. Verify the public
   readback and client discovery. Catalog responses use no-store/revalidation;
   immutable artifacts use long-lived caching. Retain old catalog evidence.

Catalogs expire **30 days** after issuance. Publish a freshly signed catalog
with a higher catalog sequence before expiry, even if product versions have not
changed. Expiry/offline errors never block playing an installed game. No
automatic catalog-renewal job has been created.

Fixture checks: `dotnet run --project tools/mw3-remaster-launcher-tests/LauncherChecks.csproj
 -c Release -- --online-updates-only` and `node --test tools/update-service/worker.test.mjs`.
Real release checks and scope are recorded in
[the 1.0.38 release record](../../docs/archive/playtest-release-1.0.38-2026-10-25.md).
