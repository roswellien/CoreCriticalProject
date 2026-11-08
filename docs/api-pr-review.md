# Direct API PR reviews

Issue20 connects OpenAI Responses and Mistral Chat Completions directly to PR
review. These calls use provider API allowances, not Copilot or signed-in Codex
usage. Existing Copilot and the separate inactive coding controller stay intact.

The owner approved `gpt-5.4-2026-03-05` and `mistral-large-4-0`, one request per
provider/PR-head and a $0.50 per-provider admission ceiling. Required repository
variables name each model, input/output micro-USD per million tokens and the cap;
the runner refuses missing/unpriced configuration. Standard uncached rates are
$2.50/$15 per million for GPT-5.4 and $0.70/$2.10 for Large4. Input-byte and output-
token limits bound the admission estimate; it is not a vendor reservation or an
invoice. Native credit availability and overages-off settings must be verified.
No purchase, recharge, billing change or fallback is performed by this code.

The automatic workflow runs trusted default-branch code after exact-head successful
Bootstrap checks. It reads bounded authored patches as untrusted text. It never
checks out or executes candidate code with review secrets. Secrets exist only in
the provider review step. GitHub authority is contents/actions read and PR write;
reviews are COMMENTED, never approval, merge or branch updates.

A durable bot review reservation precedes each inference. Completed reservations
are reused, and pending/conflicting reservations block replay. Provider output is
strict JSON, limited to shown patch lines. Receipts retain model/request/token/cost
evidence before publication; they exclude prompts, source and credentials. An
unknown outcome needs owner reconciliation, not an automatic retry or deletion
of evidence. Actual costs use conservative uncached rates; missing usage cannot
be assumed free. A stale head prevents publishing the result.

For an owner-invoked canary before default-branch activation, the existing build
workflow can call the reusable reviewer from a reviewed topic revision:

```text
gh workflow run build.yml --repo roswellien/MW3Recomp-Private --ref roswellien/ci/20-api-pr-reviews -f review_pr=254 -f review_head=b07997e68fc0fe7e3248ecac344f74cc9f0f293d
```

Only an owner manual dispatch can review a draft; automatic runs exclude drafts
and forks. The exact PR head must already have successful bootstrap CI. The
manual job does not mark a draft ready, run normal build jobs, approve or merge.
Automatic activation requires the reviewed workflow to land through the normal
manual PR merge path. A stored key or dispatch acknowledgment alone is not proof
of a successful review; inspect actual current-head provider receipts and results.

Run `python -B -m unittest discover -s tests -p test_api_pr_review.py -v` and the
normal repository checks. Tests use only authored real loopback HTTP fixtures.
There is no live provider call in ordinary tests. Receipt artifacts are private
repository artifacts retained for30 days; durable review markers remain on the PR.
The artifact step uses MIT-licensed GitHub
[`actions/upload-artifact` v4.6.2](https://github.com/actions/upload-artifact/tree/ea165f8d65b6e75b540449e92b4886f43607fa02),
pinned by that exact commit, to retain redacted evidence even after a failed job.

To stop new dispatches, disable Direct API PR reviews in Actions and cancel any
active review run. Preserve reservations and receipts for reconciliation. Revoke
keys only through an owner-authorized incident action. Reverting code needs a
reviewed PR and does not erase already incurred usage or posted comments.
