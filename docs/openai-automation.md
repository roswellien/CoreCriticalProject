# OpenAI automation foundation

This is PR 1 of the three-PR rollout tracked by [#258](https://github.com/roswellien/MW3Recomp-Private/issues/258).
It provides offline policy/state evaluation, validated summary/triage proposals,
bounded GitHub/OpenAI adapters and a dormant Actions workflow for this repository
and [project 1](https://github.com/users/roswellien/projects/1). It changes no gameplay,
launcher, runtime, release or pack behavior.

**Live commands are deliberately blocked by code**, including when all variables and
policy approvals are set. No Ready issue is claimed and no live summary, triage or
implementation run starts from landing this PR. The workflow contains no automation
secret references or token-minting step. Ordinary PR checks use authored fixtures.

## Try the offline preview

From the repository root, with Python 3.11 or newer:

```text
python -B tools/github/openai_automation.py preview --snapshot tests/fixtures/openai_automation_snapshot.json
python -B -m unittest discover -s tests -p "test_openai_automation*.py" -v
python tools/check.py --setup
python tools/check.py
```

Preview prints candidate Ready issue numbers, blockers and pending-intent IDs. It does
not read credentials, construct authenticated clients, call a provider or write remote
state. The included fixture has synthetic issues 9001/9002 and is not a live board dump.
Optional `--policy PATH` and `--state PATH` read authored local JSON; omitting state
reports `state_not_loaded`, never an empty production ledger. Files are bounded to
2 MB, unknown/duplicate keys fail, and partial snapshots are rejected.

`reconcile`, `summary` and `triage --issue N` return exit 2 with
`blocked: foundation_rollout_incomplete` before configuration or credential access.
`--admission-only` is the workflow's preliminary check, not an activation bypass.
Preview success returns 0; invalid/configuration input returns 2; unexpected I/O or
record-shape failure returns 1 with a redacted code. No raw issue text, response body,
prompt or credential is printed in error logs.

## Authority and publication

`openai_automation.py` owns strict records, money, leases, intent transitions and queue
decisions. It reuses the read-only board checker's public scope/label constants without
changing that checker. The GitHub adapter has separate App and Projects ports; neither
offers merges, ref updates, arbitrary GraphQL or shell execution. Provider output can
choose only allowlisted type/area labels, P0/P1/P2 and plain Next action text for an exact
issue/revision. Status, assignees, closure and Ready authorization are not model outputs.
Labels are appended and human/capture labels are retained.
GitHub CRLF text is normalized before validation/fingerprinting, with received-byte
limits still enforced; bare carriage returns and other unsafe controls are rejected.

Each write intent contains its operation ID, issue/item, before/desired values and
source revision. Persist `prepared`, then `publishing`, using the current state blob SHA,
before one external write. Check the live disable variable, lease/fence and source again
before publication. Verify the resulting field before recording `applied`. Sibling intents
advance only after a confirmed isolated bot edit. Human/source changes pause; no automatic
rollback overwrites human fields. This is not an atomic compare-and-swap for Projects
fields: GitHub supplies no such precondition, and a human edit can race an API request.

Provably unsent `prepared` work whose source changed is recorded as terminal
`superseded` under the current enable/lease/fence/SHA checks. It does not write the
issue or board and cannot be revived; fresh triage needs a new operation ID. Work
already `publishing` is never superseded or blindly retried. Confirmed label additions
can be acknowledged even if a human also added labels; retain those labels and leave
sibling revisions stale unless the bot edit was isolated. These siblings must pass
their own source checks (or become superseded) before new inference can start.

A lost response leaves `publishing`. If the current field equals the desired value,
reconciliation can record completion without another write. If it still equals the old
value, the first request might remain in flight: pause for owner reconciliation, do not
repeat it. Recovery after a crash can leave sibling intents stale; an owner must inspect
them. A 409/422 state conflict requires a fresh read/evaluation, not a stale replay.

## Durable state and budgets

After later-PR review, the owner seeds one version-1 JSON state record at
`openai-automation/state.json` on `roswellien/ci/260-automation-state`. The controller
never creates that branch or substitutes zero balances for a missing file. Its schema
is the `State` dataclass and `parse_state`; authored examples are in
`tests/test_openai_automation.py`. It records repository/board, UTC cycle bounds,
generation, one publisher lease, operation allocations, mutation intents and Actions
minutes. Empty initial arrays and generation 0 require explicit owner initialization.
Do not reset usage within an active cycle. Owner-reviewed cycle rollover/compaction must
preserve receipts and unresolved work. State is limited to 500 KB and 1000 records per
collection; exhaustion pauses instead of silently deleting evidence.

Lease acquisition proposes a new fencing generation and a deadline of at most five
minutes. Its SHA-preconditioned save determines who actually acquired it; Projects fields
are never locks. Active leases, uncertain spend or publishing/conflicting intents block
new acquisition. Events are hints; hourly reconciliation recovers dropped wake-ups.

The checked-in `tools/github/openai_automation_policy.json` defaults disabled. Every
nullable model/effort, price, cap, controller SHA and cycle value must be deliberately
configured in later reviewed deployment work. Money is integer micro-USD: one dollar
is 1,000,000 micro-USD. Input/output prices are micro-USD per million tokens. No model,
balance, price, monthly renewal or cap is inferred from authentication or an allowance.

`allocate_request` persists a conservative allocation before the single Responses POST.
It bounds the complete serialized request, output tokens and pricing with at least 10%
headroom (default 25%), charges the full input rate without an inferred cache discount,
and budgets five Linux Actions minutes per call. This can overcount shared job time.
Account for polling-only jobs and hosted-worker/tool/reviewer costs before activation;
the foundation does not claim to implement those later streams.

Usage receipts settle integer token-priced costs, not an exact vendor invoice. Refused
or invalid output with known usage still counts. Missing usage/model evidence or an
uncertain response keeps the allocation pending and blocks new requests; no automatic
POST retry or model fallback. Above-allocation usage is recorded and blocks further
dispatch. The ledger is not a vendor credit reservation or a zero-overshoot guarantee.
Require an enforced API project cap as well; hard caps may have asynchronous overshoot.
Never buy credits, raise limits or assume purchased credits cannot be charged.

The provider now requires an explicitly supplied `CompletionJournal` in an existing
private absolute directory, before allocating or making a provider request. A storage
preflight exercises file flushing and exclusive hard-link publication before
allocation; unsupported storage blocks the request with a redacted failure. A known
response is flushed as a separate immutable receipt **before** settlement or another
authority check. It contains only fixed scope, operation ID, a cycle/model/price/
reservation binding, validated response/model IDs and token counts, and fixed anomaly
codes. No input/output text, raw errors or credentials are retained. Conflicting
receipts are not overwritten; an unknown model/usage keeps its reservation pending.
No receipt path is inferred from the home directory or an environment variable.

`OpenAI.reconcile_receipt` is an explicit evidence-only operation: reread current state,
verify the receipt binding and approved prices, then save only settlement (and, if the
old lease expired, a newly acquired lease) under fresh enable/policy/SHA checks. An
active different publisher blocks recovery. Disable still prevents every remote state
or field write; an expired publisher cannot save an old state. Reconciliation never
calls the provider or returns a proposal. Receipts remain for owner-reviewed retention.

This is a local persistence interface, not a deployed Actions receipt service. Files
are fsynced and published using a no-replace same-directory hard link; POSIX additionally
checks owner/private permissions and fsyncs the directory. Windows ACL isolation and
directory-entry crash guarantees require deployment verification. Before activation,
provide protected durable storage that survives runner deletion and verify receipt
retention/recovery on that platform. Ephemeral Actions scratch or an end-of-job upload
alone does not satisfy this gate. No journal storage or uploader is provisioned here.

## Trusted workflow and deployment gates

`.github/workflows/openai-automation.yml` uses indented JSON-compatible YAML so its
actual structure can be checked with Python's standard JSON decoder. Do not introduce
a custom YAML parser or a generated second workflow. Comments/explanations belong here.
It has only hourly `17 * * * *` and manual choice inputs, a non-cancelling publisher
concurrency group, Ubuntu 24.04, a five-minute timeout and `contents: read` permissions.

Unset variables skip the job. Future activation must verify all of these controls:

| Setting | Required contract |
| --- | --- |
| `OPENAI_AUTOMATION_ENABLED` repository variable | Exact `true`; reread through the Variables API before every side effect; missing/read failure means stop |
| `OPENAI_AUTOMATION_ROLLOUT_COMPLETE` repository variable | Exact `true` after all three reviewed PRs and the owner-invoked canary |
| `OPENAI_AUTOMATION_CONTROLLER_SHA` repository variable | Approved lowercase 40-hex commit on `develop`; workflow checks exact checkout and ancestry |
| `openai-automation` environment | Pre-created, verified branch policy permitting only `develop`; required features must actually be available on the private account |
| Environment secrets for later rollout | `OPENAI_API_KEY`, `AUTOMATION_APP_PRIVATE_KEY`, `AUTOMATION_PROJECTS_TOKEN`; never candidate/ordinary CI inputs |
| Future App client ID | `AUTOMATION_APP_CLIENT_ID` environment variable, repository-scoped installation |
| Policy prerequisites | Owner-verified credits, project cap, secret isolation, platform no-merge rules, App/Projects identities, Ready setters, hosted-data controls and canary |

The existing repository-level OpenAI secret must be migrated to the restricted environment
and removed at repository scope **before activation**. No migration or credential change
is performed by this PR. Never export the desktop `gh` OAuth login to Actions. User-owned
Projects do not support fine-grained PATs: a separately tested classic Projects token
has broader authority and needs explicit owner approval for the isolated, fixed-board/
field broker. Do not silently relocate the board or grant broader access.

The future App needs Contents write for the state branch, Issues write for label additions,
Pull requests read for implementation links, and Variables read for the fresh disable
check, restricted to this repository. Contents write can also authorize merges: require
verified platform protections denying the bot final updates to `main`/`develop`, no bot
bypass, and retain the owner's manual merge path. Auto-merge must remain off. If protection
or environment restrictions are unavailable, keep automation off; no automatic upgrade,
visibility change or weaker substitute is authorized.

Existing action pins are checkout `11d5960a326750d5838078e36cf38b85af677262` (v4) and
setup-python `a26af69be951a213d495a4c3e4e4022e16d87065` (v5). The reviewed future token
action is GitHub's MIT-licensed
[`actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510`](https://github.com/actions/create-github-app-token/tree/64ab729a6294000f5aa4a4bc0b73d1f32bc45510),
using Node 24, `client-id`, explicit owner/repository/permissions and revocation enabled.
It avoids a custom JWT signer. **It is not invoked in foundation.** Its pinned metadata
does not expose a `permission-variables` input; future rollout must verify an exact
permission-capable minting path before wiring live dispatch. Never omit permission
selection merely to inherit all App authority. Upstream packages retain their licenses.

## Later PRs and recovery

PR2 adds isolated hosted Agents sessions and validated allowlisted source/patch transfer.
PR3 adds branch/PR production, conflict/check/review repair, fresh independent runtime
review, scoped Ready-path policy, and the bounded canary. Ready remains the authorized
queue with no extra label; foundation only reports it. Existing assignees and linked
implementation PRs are excluded. Keep validation-dependent work open. No Done/closure
before verified manual merge and acceptance, and no automatic merges or releases.

Before activation verify actual service access, credit/cycle evidence, project isolation,
models/effort and all cost streams; test bounded synthetic issue/branches and the owner's
manual merge. Confirm hosted retention/residency and disabled/restricted worker egress
before any private-source upload. Workers get no `.git`, controller credentials, original
media, generated game bodies or private outputs. Missing private/Windows validation
pauses at a draft PR instead of claiming success or retrying indefinitely.

Disable first, fence publication, inspect pending effects/spend and clean up sessions;
revoke compromised credentials if needed. Preserve evidence and branches. Never reset an
uncertain allocation or overwrite board fields automatically. Reverting implementation
uses reviewed PRs in reverse rollout order; it does not erase already-published effects.

Contracts: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs),
[Contents SHA preconditions](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents),
[Variables permissions](https://docs.github.com/en/rest/actions/variables#get-a-repository-variable),
[workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows),
[JSON-compatible YAML](https://yaml.org/spec/1.2.2/#12-yaml-history).
