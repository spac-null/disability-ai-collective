# EVIDENCE MANIFEST — Edinburgh human & cross-model evidence

Preserved 2026-08-19. Copy-and-document only. No model was called, nothing was reconstructed,
no canonical doc edited, nothing committed.

## Search performed before any handoff text was used

Read-only search for original raw material across: all 648 Claude session transcripts under
`~/.claude/projects/`, all job directories and `timeline.jsonl` files under `~/.claude/jobs/`,
the `/private/tmp/claude-501` scratchpad tree, the canonical repo, and `cripminds-preservation/`.
Searched on the distinctive strings supplied for each source.

Result: the Edinburgh session transcript
`6ad3d0e7-4cce-417a-a13f-8119f0832382.jsonl` (4.0 MB, ends 2026-08-18 23:33) survives and
contains seven verbatim operator briefs, preserved here. **No raw model output from Grok, Qwen or**
**Perplexity exists in any local store, and no verbatim transcript of either reader's words exists.**
The father's Dutch text returns zero hits locally; the strings `almost comfortable`,
`nice narrative`, `drifts at will`, `the contrast lies in agency`, `trapped in presentation`,
`the maker remained unseen` and `Blijft minder op een lijn` return zero hits anywhere on this machine.

## Artifacts

| EVIDENCE ID | TYPE | SUBJECT | ORIGINAL LOCATION / ORIGIN | PRESERVED PATH | CLASS | SHA-256 | SIZE | NOTES |
|---|---|---|---|---|---|---|---|---|
| E-01 | reader feedback | Father (WhatsApp) | `HISTORICAL SESSION HANDOFF — not the original WhatsApp export` | `human-reading/father-whatsapp-2026-08-18-RAW.txt` | RAW_VERBATIM (as handed forward) | `5831ba07a1cd97e3480f933f97cce929d2bef9ac49ce83cdc25b9ee207c19dde` | 727 | Dutch/English preserved exactly as supplied; no spelling or punctuation altered. No local copy of this text exists in any searched store. |
| E-02 | reader feedback | Father | `derived this pass from E-01` | `human-reading/father-feedback-INTERPRETATION.md` | HUMAN_INTERPRETATION | `9790606ff8d1d285a731151ba673d7eaa7e556745313b11153d0e9d550e9fdc5` | 1534 | Kept separate from raw per instruction. |
| E-03 | reader reading | Jascha | `bullets: HISTORICAL SESSION HANDOFF; quoted blocks: local session briefs` | `human-reading/jascha-legacy-reading-INTERPRETATION.md` | HUMAN_INTERPRETATION (+ PARTIAL_VERBATIM of briefs) | `71792ed8af047abe40ed8b5b87931ac1177581e621c7e4a8e953c56d4f200401` | 2701 | No verbatim transcript of the reading recovered; 'almost comfortable' and 'nice narrative' appear in no local artifact. Includes an attribution correction: two lines circulated as his are Legacy article text. |
| E-04 | model output excerpts | Grok | `HISTORICAL SESSION HANDOFF` | `cross-model/grok-excerpts-SUPPLIED.md` | PARTIAL_VERBATIM as supplied / FULL_RAW_NOT_FOUND | `82ccdf54e7addf918de3500c4a2f3e92cdd5c189e242bd3d54853d9b9ac88da8` | 2386 | All four supplied excerpts are verbatim Opus B.3 text. Independence in question. |
| E-05 | model output + reasoning excerpts | Qwen 3.7 Plus | `HISTORICAL SESSION HANDOFF` | `cross-model/qwen-excerpts-SUPPLIED.md` | PARTIAL_VERBATIM as supplied / FULL_RAW_NOT_FOUND | `99c96e687ce044c0a62a5b2e473f4f033fafd94a888fefc3cb0bd9df7f1d30df` | 2080 | Excerpts diverge from B.3 in word order, contraction and named artists — consistent with a separate generation. Reasoning trace not recovered; connective text NOT reconstructed. |
| E-06 | model output excerpts | Perplexity | `HISTORICAL SESSION HANDOFF` | `cross-model/perplexity-CONTAMINATED.md` | CONTAMINATED / FULL_RAW_NOT_FOUND | `9a109274fc8a97c72e265ddea31d14b6c2ff48846800dc446cabb7d2739fa236` | 1585 | Opening clause is verbatim B.3. Confirmed contamination, not merely suspected. |
| E-07 | analysis | cross-model convergence claim | `derived this pass from preserved artifacts` | `cross-model/CROSS-MODEL-CONVERGENCE-FINDING.md` | HUMAN_INTERPRETATION | `f5ae9e78f8cbd0fe2e170a7608919e6174f01f1d894897f76df0f5f65397a88f` | 2854 | Read-only analysis. No model called. |
| E-B1004 | operator session brief | Edinburgh iteration brief | `~/.claude/projects/-Users-stargatesgx-code-trident/6ad3d0e7-4cce-417a-a13f-8119f0832382.jsonl (verbatim user message)` | `source-session-briefs/brief-2026-08-18T17-39-49-line1004.txt` | RAW_VERBATIM (local) | `5dd49d0520f7a116baa13ed389fc50cdfe2f86e4191c7e735d17aa7bfd0a3ed2` | 8140 | Operator brief written during the Edinburgh session. Contains the human reading in summarised form, not verbatim reader wording. |
| E-B1065 | operator session brief | Edinburgh iteration brief | `~/.claude/projects/-Users-stargatesgx-code-trident/6ad3d0e7-4cce-417a-a13f-8119f0832382.jsonl (verbatim user message)` | `source-session-briefs/brief-2026-08-18T17-51-58-line1065.txt` | RAW_VERBATIM (local) | `41f8a33f8b9c0908350fe2cb18e28754138e57cc9a754e0b8f130f68876c0917` | 8591 | Operator brief written during the Edinburgh session. Contains the human reading in summarised form, not verbatim reader wording. |
| E-B1131 | operator session brief | Edinburgh iteration brief | `~/.claude/projects/-Users-stargatesgx-code-trident/6ad3d0e7-4cce-417a-a13f-8119f0832382.jsonl (verbatim user message)` | `source-session-briefs/brief-2026-08-18T19-03-20-line1131.txt` | RAW_VERBATIM (local) | `6723214dac1303a0f10688e9fe45def61272184f8c0987fcc0ff4e7d5a01afa8` | 4926 | Operator brief written during the Edinburgh session. Contains the human reading in summarised form, not verbatim reader wording. |
| E-B1170 | operator session brief | Edinburgh iteration brief | `~/.claude/projects/-Users-stargatesgx-code-trident/6ad3d0e7-4cce-417a-a13f-8119f0832382.jsonl (verbatim user message)` | `source-session-briefs/brief-2026-08-18T19-11-07-line1170.txt` | RAW_VERBATIM (local) | `1698884d95707259913a0bac06dae23e0c0ca28fee0848c5185fb5b9ef146e9f` | 2903 | Operator brief written during the Edinburgh session. Contains the human reading in summarised form, not verbatim reader wording. |
| E-B1249 | operator session brief | Edinburgh iteration brief | `~/.claude/projects/-Users-stargatesgx-code-trident/6ad3d0e7-4cce-417a-a13f-8119f0832382.jsonl (verbatim user message)` | `source-session-briefs/brief-2026-08-18T21-12-45-line1249.txt` | RAW_VERBATIM (local) | `d3cfe714c9bd8e38d1cea1603e072e699d12964c43c8497576453aecf3972962` | 5657 | Operator brief written during the Edinburgh session. Contains the human reading in summarised form, not verbatim reader wording. |
| E-B1259 | operator session brief | Edinburgh iteration brief | `~/.claude/projects/-Users-stargatesgx-code-trident/6ad3d0e7-4cce-417a-a13f-8119f0832382.jsonl (verbatim user message)` | `source-session-briefs/brief-2026-08-18T21-15-15-line1259.txt` | RAW_VERBATIM (local) | `68f66871dc662bac70c9211dcb20f42006641688e8b19b1cb444ee3994cff723` | 3596 | Operator brief written during the Edinburgh session. Contains the human reading in summarised form, not verbatim reader wording. |
| E-B991 | operator session brief | Edinburgh iteration brief | `~/.claude/projects/-Users-stargatesgx-code-trident/6ad3d0e7-4cce-417a-a13f-8119f0832382.jsonl (verbatim user message)` | `source-session-briefs/brief-2026-08-18T15-18-49-line991.txt` | RAW_VERBATIM (local) | `d22fad12155ed70cba05cecc78961575f47988630bfce12b6d4efe248395fe7a` | 2490 | Operator brief written during the Edinburgh session. Contains the human reading in summarised form, not verbatim reader wording. |

## Classification summary

| Source | Full raw recovered | Class |
|---|---|---|
| Jascha's Legacy reading | No | HUMAN_INTERPRETATION + PARTIAL_VERBATIM of local briefs; FULL_RAW_NOT_FOUND |
| Father's WhatsApp | No original export | RAW_VERBATIM as handed forward; FULL_RAW_NOT_FOUND for the export |
| Grok first clean generation | No | PARTIAL_VERBATIM as supplied; FULL_RAW_NOT_FOUND; independence in question |
| Qwen output + reasoning | No | PARTIAL_VERBATIM as supplied; FULL_RAW_NOT_FOUND |
| Perplexity | No | CONTAMINATED; FULL_RAW_NOT_FOUND |
| Opus B.3 / B.4 (reference runs) | **Yes** | Already preserved in `../iterations/` with packets and grounding audits |

## Not done, deliberately

- No model called, no generation recreated, no connective text manufactured between excerpts.
- Later Grok rewrites (prompted to restyle the first thesis) were excluded as non-clean; none
  were found locally in any case.
- The lost editorial-pairing drafts were not reconstructed; no excerpts of them surfaced.

---

## SUPPLEMENT — raw cross-model material recovered 2026-08-19

The owner supplied the raw Grok and Perplexity sessions, the blind-writer prompt, and — decisively —
**the text actually pasted into the prompt's `FULL SOURCE` slot**. These were previously recorded as
FULL_RAW_NOT_FOUND. ORIGIN = OWNER-SUPPLIED IN PRESERVATION SESSION; these are not recovered local
files and no local copy exists. Preserved verbatim, including the corruption in the pasted source.

| EVIDENCE ID | TYPE | SUBJECT | ORIGIN | PRESERVED PATH | CLASS | SHA-256 | SIZE |
|---|---|---|---|---|---|---|---|
| E-10 | prompt | blind-writer prompt | OWNER-SUPPLIED IN PRESERVATION SESSION | `cross-model/raw/blind-writer-prompt-as-supplied.md` | RAW_VERBATIM | `aa11b4833720616ccfe8cbecd173c61df6666a8652f47dccb106c90f26de87fe` | 3181 |
| E-08 | model session (3 outputs) | Grok | OWNER-SUPPLIED IN PRESERVATION SESSION | `cross-model/raw/grok-session-verbatim.md` | RAW_VERBATIM / CONTAMINATED INPUT | `5ff3b6ee23c995c3b516684624cfef9857f0bc55947010128575e0d8032097f8` | 12383 |
| E-09 | model session (3 outputs) | Perplexity | OWNER-SUPPLIED IN PRESERVATION SESSION | `cross-model/raw/perplexity-session-verbatim.md` | RAW_VERBATIM / CONTAMINATED INPUT | `53282fdc1b739d13c9b21d7c26ff49c798dd706d6fbec607db2abc4aba30ac02` | 18818 |
| E-11 | contaminated source paste | text given to models as 'FULL SOURCE' | OWNER-SUPPLIED IN PRESERVATION SESSION | `cross-model/raw/source-text-as-supplied-to-models.txt` | RAW_VERBATIM — key evidence | `2cbff6a00e2d295e5982ab4effac56822c514ded3d6071870dc8c51414767286` | 4991 |

**Finding**: the pasted `FULL SOURCE` is not the Guardian review — it is a damaged capture with
Opus B.3's article interleaved into it. Ten B.3-specific phrases appear 0x in the real source and 1x
in what the models were given. Grok repaired B.3's corrupted sentence; Perplexity opened with the
paste's final line. The cross-model convergence was supplied, not independent. Full analysis in
`cross-model/CONTAMINATION-FINDING.md`.

**Revised classification summary**:

| Source | Raw | Class |
|---|---|---|
| Grok | **Recovered** | RAW_VERBATIM; independence REFUTED (contaminated input) |
| Perplexity | **Recovered** | RAW_VERBATIM; CONTAMINATED, now demonstrated |
| Qwen | Still not found | PARTIAL_VERBATIM; independence UNKNOWN (downgraded from plausible) |
| Opus B.3 / B.4 | Preserved | Valid — clean pipeline runs against the real source snapshot |

---

## SUPPLEMENT 2 — father's read artifact and second WhatsApp rendering (2026-08-19)

| EVIDENCE ID | TYPE | SUBJECT | ORIGIN | PRESERVED PATH | CLASS | SHA-256 | SIZE |
|---|---|---|---|---|---|---|---|
| E-12 | read artifact (PDF) | father's reader feedback | `~/Downloads/Sandra George Was Underground Twice.pdf`, mtime 2026-08-18 17:22 | `human-reading/father-read-artifact-Sandra-George-Was-Underground-Twice.pdf` | RAW_VERBATIM — the LEGACY arm, matches iterations/original-AB/legacy-shadow.md | `5f6777d5a55203327d8265ae2c58fc8b111a115955265085892b429c34d94da9` | 52346 |
| E-13 | reader feedback, 2nd rendering | father's reader feedback | OWNER-SUPPLIED IN PRESERVATION SESSION | `human-reading/father-whatsapp-2026-08-18-VARIANT-2-pdf-extraction.txt` | RAW_VERBATIM — ligature-damaged; NOT corrected; lacks the third message | `aebcc17b89499bb044c0d7d9091fe1b87b611d9e95ece439a323d7a890aa76be` | 668 |
| E-14 | provenance note | father's reader feedback | derived this pass | `human-reading/README-variants.md` | HUMAN_INTERPRETATION | `836b8318bbf9b20109f6f24488061d801b7c0ce60a57066b984fdffb3467d537` | 2029 |

**Finding**: the father's feedback is bound to a specific artifact — the **Legacy** arm, not Sofa
or any B.x/FORM iteration. Timeline: legacy-shadow.md 16:51 -> PDF 17:22 -> his first message 19:02.
His opening message restates the Legacy article's own discovery because he had just read it; it is
not independent arrival at the same idea. Both renderings of his messages are preserved uncorrected.
