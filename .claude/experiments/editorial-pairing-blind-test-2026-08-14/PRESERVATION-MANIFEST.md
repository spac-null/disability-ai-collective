# PRESERVATION MANIFEST — Aug-14 editorial-pairing blind test

Preserved 2026-08-19. Copy-and-document only.

## The four candidate drafts are LOST

UNPRESERVED-ARTIFACTS.md group 4 recorded four candidate articles ("Ledger Item", "The Six-Second
Rule", "Nine Days", "Rewind") plus `f1_A/B`…`f4_A/B` and blind-pair files in the reader-lab worker
scratchpad, last modified 2026-08-14 16:57.

They no longer exist. As of 2026-08-19 the directory
`/private/tmp/claude-501/-Users-stargatesgx-code-disability-collective-ai-reader-lab-worker/
0ee8c229-771d-4644-9a43-d9aa1fe9e9b3/scratchpad/editorial_pairing/` contains exactly one thing: an
**empty** `blind/` sub-directory, with an mtime of 2026-08-19 00:00 — minutes after the reconciliation
that catalogued the files was written (23:54–23:56 on 2026-08-18).

Searched and not found: the whole `/private/tmp/claude-501` tree, all Claude job directories, the
canonical repo, and `cripminds-preservation/`. A narrow trident search (title grep across the Hermes
workspace and `/tmp`, plus a search for `editorial_pairing_capture.py` and any reader-lab directory)
returned nothing — this experiment ran on the Mac and has no trident counterpart.

**Classification: LOST** — not NEVER_PERSISTED (they demonstrably existed and were catalogued with
names, sizes and mtimes), and not NOT_FOUND (the containing directory survives and is empty). The
most likely cause is ordinary macOS periodic `/tmp` cleanup, which removes files untouched for several
days while leaving directory skeletons — consistent with a 2026-08-14 mtime being reaped on 2026-08-19.
They were destroyed in the window between being identified as at-risk and being acted on.

Nothing has been reconstructed or regenerated. Only the two survivors below are preserved.

## What survived

| ARTIFACT TYPE | ORIGINAL PATH | PRESERVED PATH | SHA-256 | ORIGINAL MTIME | SIZE | STATUS |
|---|---|---|---|---|---|---|
| persona-biography spotcheck | `/private/tmp/claude-501/-Users-stargatesgx-code-disability-collective-ai-reader-lab-worker/0ee8c229-771d-4644-9a43-d9aa1fe9e9b3/scratchpad/persona_bio_spotcheck/case1.txt` | `persona_bio_spotcheck/case1.txt` | `7c14f569b6f92f0d716fb93cde0f1f6a1dd1e08a9851c28ec9ce8fa230c24b21` | 2026-08-15 03:09:51 | 20572 | RAW |
| persona-biography spotcheck | `/private/tmp/claude-501/-Users-stargatesgx-code-disability-collective-ai-reader-lab-worker/0ee8c229-771d-4644-9a43-d9aa1fe9e9b3/scratchpad/persona_bio_spotcheck/case2.txt` | `persona_bio_spotcheck/case2.txt` | `ecda3bd885c42fe44c268c259743a351125c7334514236c1a56bbdb504f340f8` | 2026-08-15 03:09:51 | 20206 | RAW |

`editorial_pairing_capture.py` (the capture tool, 265 lines) still exists on the unmerged branch
`-editorial-upgrade-v1` and was deliberately **not** touched, merged or extracted here — G-044 covers it,
and it lives on a protected branch ref rather than in ephemeral storage.
