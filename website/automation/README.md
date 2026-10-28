# Legacy MechLab publishing handoff

This workflow template documents the old cross-repository publishing bridge.
The active copy is `.github/workflows/publish-mechlab.yml` in
`roswellien/MW3Recomp-Private`: it copies dated `docs/mechlab/` notes into
`data/mechlab.json` in `roswellien/corecritical-website` using the
`CORECRITICAL_WEBSITE_DEPLOY_KEY` Actions secret.

The moved site build reads those notes directly from this repository instead.
Do not install or re-enable this template after Pages has switched to this
repository. Keep the current workflow, secret and deploy key until the
maintainer has verified the first deploy from this repository, so the existing
live site can continue receiving its updates during the cutover.

After that verification, the maintainer removes the game-repository workflow,
deletes the `CORECRITICAL_WEBSITE_DEPLOY_KEY` secret, and revokes its public key
from the old website repository. The old website repository can then be
archived with a README pointing to `website/` here. The workflow in this folder
is retained as source-migration history until that cleanup is complete; it is
not active from this path.

No deploy key, private key, token or credential is stored in this repository.
