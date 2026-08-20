# Capture Schema

`shadow-capture-v1`. Written by `automation/shadow_capture.py`.

## Bundle layout

```
<root>/<run-id>/
  manifest.jsonl          append-only, one JSON object per event
  COMPLETE                seal marker; absence => CAPTURE_INVALID
  source/
    raw_cached_source.txt   R1  full cached extraction
    returned_source.txt     R2  get_source_text() returned slice
    packet_source.txt       R3  post-downgrade value given to build_evidence_packet
    evidence_packet.json    R4  the packet threaded through every stage
    provenance.json         url, origin, ids, lengths, caps
  legacy/
    commission_input.json
    fable_brief.json
    writer_prompt.txt       writer-visible evidence, as assembled
    writer_output_raw.md    RAW writer output, BEFORE rewrite
    writer_meta.json        provider, model
    pre_rewrite.md
    post_rewrite.md
    disposition.json        gate, degraded stages, should_block, review, fact_check, disposition
```

Run id: `YYYYMMDDTHHMMSSZ-<8 hex>` — chronologically sortable, collision-free.

## `manifest.jsonl` entry

```json
{
  "schema_version": "shadow-capture-v1",
  "event": "evidence|commission|writer|rewrite|disposition",
  "captured_at": "<ISO-8601 UTC>",
  "entries": {
    "<relative path>": {"path": "...", "sha256": "...", "bytes": 1234}
  }
}
```

A refused artifact records `{"status": "REFUSED_POSSIBLE_SECRET", "markers": [...]}` instead
of a hash, and no file is written.

## Integrity properties

| Property | Mechanism |
|---|---|
| Per-artifact hash | SHA-256 recorded in the manifest at write time |
| Tamper detection | the harness rehashes every file and compares |
| Partial-write safety | temp file + `fsync` + `os.replace` |
| Incomplete-bundle detection | missing `COMPLETE` ⇒ `CAPTURE_INVALID` |
| Append-only | `manifest.jsonl` is opened `"a"`; no line is ever rewritten |

## Required artifacts for a sound comparison

`source/packet_source.txt`, `source/evidence_packet.json`, `legacy/writer_output_raw.md`.
A bundle missing any of these is `CAPTURE_INVALID`.
