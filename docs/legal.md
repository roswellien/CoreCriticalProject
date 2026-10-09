# Legal and distribution policy

MW34 RECOMP contains project-authored interoperability and research tooling.
Users must supply their own legally obtained game installation or media.
The project does not supply games or grant rights to their content.

Do not commit, redistribute, or package proprietary executables, DLLs, assets,
music, video, installers, disc images, or memory dumps, including derived
replacements. Do not download game content as part of builds or tests.
Local analysis reads user-provided inputs without executing them. For the
user-authorized work-ahead track, decoded research previews and requested
enhancement experiments may be saved under ignored `local/work-ahead/`, with
source identities and processing metadata. This local experiment exception
does not authorize public replacement packs or
change distribution eligibility. The build and tests operate without any
game installation.

Acceptable repository material includes project-authored code and documentation,
cryptographic hashes, format metadata, evidence-backed addresses, symbolic
annotations, and narrowly scoped authored patch descriptions. Review any
signatures or extracts for necessity and rights before submission. Generated
translations and large disassembly/string dumps remain local and ignored;
their availability does not establish permission to distribute them.

The MIT license applies to the project's own contributions, not original game
content or third-party tools. Third-party dependencies retain their own licenses.
No affiliation or endorsement by the MechWarrior rights holders is implied.

Reverse-engineering and interoperability rules depend on jurisdiction and the
applicable agreements. This repository policy is deliberately conservative;
it is not a determination that any specific distribution or circumvention is
lawful. Resolve those questions before public release of derived artifacts.

Inputs should live outside Git or in `local/`. Reports belong in `reports/`;
review and redact evidence before copying selected metadata into documentation.
`.gitignore` blocks common proprietary formats, but contributors must still
inspect staged files. No install media are uploaded to CI or release storage.
