/**
 * Crip Minds Reader Lab — B2 → Reader Lab candidate-pool bridge.
 *
 * The ONE write path for `calibration_candidates`. Before this file
 * existed, `calibration/candidates/README.md` was explicit that seeding
 * this table was "a future pass, not this one," done by "a narrow,
 * reviewed script or a direct INSERT." This is that narrow, reviewed
 * path — never a second ad hoc one, matching the same "one write path"
 * discipline `publish.js` already applies to rounds/items/assignments.
 *
 * This module makes no research judgment. It validates that a candidate
 * bundle already deterministically establishes everything it claims
 * (content hashes, dataset purpose, explicit eligibility, provenance) —
 * the actual decision "is this worth another independent human read" was
 * already made upstream, by whoever built the bundle (a human research
 * pass today; `prepare-calibration-candidates-v1`
 * (`calibration/runner/prepare_calibration_candidates.py`) going
 * forward). If a bundle's claims don't check out, this rejects — it
 * never guesses on the bundle's behalf.
 */

import { newId, nowIso, sha256Hex } from "./util.js";
import { sortedStringify, writeAuditLog } from "./publish.js";

// Never held_out_evaluation — enforced as a hard rejection below, the
// same value this whole system already treats as radioactive
// everywhere else (calibrationWorkflow.js's SQL filter,
// calibration_runner.py's run_prepare_next_round, and now here — a
// third, independent enforcement point for the one rule this system
// exists to never violate).
export const ALLOWED_CANDIDATE_DATASET_PURPOSES = ["pilot", "development", "blind_calibration", "contested"];

export class CandidateValidationError extends Error {
  constructor(errors) {
    super("candidate_validation_failed");
    this.errors = errors;
  }
}

// Deterministic, stable identity: the same claim text always resolves
// to the same candidate_id, regardless of who submits it, how many
// times, or from which path (runner or admin import) — this is what
// makes retries/resubmission idempotent without a separate dedup table.
function candidateIdFor(candidateClaimId) {
  return `cand_${candidateClaimId.replace(/^sha256:/, "")}`;
}

function canonicalRecordContent(normalized) {
  return {
    source_snapshot: normalized.source_snapshot,
    candidate_sentence: normalized.candidate_sentence,
    provenance: normalized.provenance,
    dataset_purpose: normalized.dataset_purpose,
    internal_rationale: normalized.internal_rationale,
    machine_reference_json: normalized.machine_reference_json,
    eligible_for_reader_lab: normalized.eligible_for_reader_lab,
  };
}

async function validateOneCandidate(raw, index) {
  const label = `candidate[${index}]`;
  const errors = [];

  if (!raw || typeof raw !== "object") return { errors: [`${label}: not_an_object`] };
  if (typeof raw.source_snapshot !== "string" || !raw.source_snapshot.trim()) errors.push(`${label}: missing_source_snapshot`);
  if (typeof raw.candidate_sentence !== "string" || !raw.candidate_sentence.trim()) errors.push(`${label}: missing_candidate_sentence`);
  if (typeof raw.provenance !== "string" || !raw.provenance.trim()) errors.push(`${label}: missing_provenance`);

  if (typeof raw.dataset_purpose !== "string" || !raw.dataset_purpose) {
    errors.push(`${label}: missing_dataset_purpose`);
  } else if (raw.dataset_purpose === "held_out_evaluation") {
    errors.push(`${label}: held_out_evaluation material may never enter calibration_candidates`);
  } else if (!ALLOWED_CANDIDATE_DATASET_PURPOSES.includes(raw.dataset_purpose)) {
    errors.push(`${label}: invalid_dataset_purpose "${raw.dataset_purpose}"`);
  }

  // Must be exactly true — never omitted, never false. This pipeline
  // exists to move ALREADY-DECIDED-eligible material into the pool
  // prepare-next-round-v1 selects from; a record the source artifact
  // itself marks not-yet-eligible (or doesn't address at all) has no
  // legitimate reason to enter calibration_candidates through this path
  // at all, inert or otherwise — that's a future research decision to
  // make explicitly, not a row to leave lying around. Rejected, not
  // silently defaulted or silently dropped.
  if (raw.eligible_for_reader_lab !== true) {
    errors.push(
      raw.eligible_for_reader_lab === false
        ? `${label}: eligible_for_reader_lab is false — this pipeline only ingests already-decided-eligible material`
        : `${label}: eligible_for_reader_lab must be explicitly true, never omitted or ambiguous`
    );
  }

  if (errors.length) return { errors };

  // Hashes are always recomputed server-side and checked against any
  // declared value — never trusted, never silently repaired. Same
  // discipline as publish.js's validateManifest.
  const actualSourceId = "sha256:" + (await sha256Hex(raw.source_snapshot));
  const actualClaimId = "sha256:" + (await sha256Hex(raw.candidate_sentence));
  if (raw.source_snapshot_id && raw.source_snapshot_id !== actualSourceId) {
    errors.push(`${label}: hash_mismatch_source_snapshot (declared ${raw.source_snapshot_id}, computed ${actualSourceId})`);
  }
  if (raw.candidate_claim_id && raw.candidate_claim_id !== actualClaimId) {
    errors.push(`${label}: hash_mismatch_candidate_claim_id (declared ${raw.candidate_claim_id}, computed ${actualClaimId})`);
  }
  if (errors.length) return { errors };

  return {
    normalized: {
      source_snapshot: raw.source_snapshot,
      candidate_sentence: raw.candidate_sentence,
      source_snapshot_id: actualSourceId,
      candidate_claim_id: actualClaimId,
      provenance: raw.provenance,
      dataset_purpose: raw.dataset_purpose,
      internal_rationale: typeof raw.internal_rationale === "string" ? raw.internal_rationale : null,
      machine_reference_json: raw.machine_reference_json ? JSON.stringify(raw.machine_reference_json) : null,
      eligible_for_reader_lab: raw.eligible_for_reader_lab,
    },
  };
}

// Reuse of content already shown to a real reviewer requires an
// explicit human/research decision elsewhere (e.g. the existing
// additional-review mechanism, which reuses item content on purpose) —
// never an automatic re-ingestion into the candidate pool. This is a
// per-candidate rejection, not a whole-bundle failure.
async function rejectIfAlreadyLiveInReaderLab(env, candidateClaimId) {
  const existing = await env.DB.prepare("SELECT item_id FROM items WHERE candidate_claim_id = ? LIMIT 1").bind(candidateClaimId).first();
  return existing ? existing.item_id : null;
}

async function ingestOneCandidate(env, raw, index, { actor, ingestedVia }) {
  const { errors, normalized } = await validateOneCandidate(raw, index);
  if (errors) return { outcome: "rejected", index, errors };

  const liveItemId = await rejectIfAlreadyLiveInReaderLab(env, normalized.candidate_claim_id);
  if (liveItemId) {
    return {
      outcome: "rejected",
      index,
      errors: [
        `candidate_claim_id already exists as production Reader Lab item ${liveItemId} — reuse requires an explicit decision elsewhere, not automatic re-ingestion`,
      ],
    };
  }

  const candidateId = candidateIdFor(normalized.candidate_claim_id);
  const contentHash = await sha256Hex(sortedStringify(canonicalRecordContent(normalized)));
  const now = nowIso();

  const existingRow = await env.DB.prepare("SELECT content_sha256 FROM calibration_candidates WHERE candidate_id = ?")
    .bind(candidateId)
    .first();

  if (existingRow) {
    if (existingRow.content_sha256 === contentHash) {
      return { outcome: "already_present", index, candidate_id: candidateId };
    }
    return {
      outcome: "rejected",
      index,
      errors: [
        `candidate_id ${candidateId} already exists with different content — never silently overwritten; a genuine correction needs an explicit, reviewed change, not a re-ingestion`,
      ],
    };
  }

  await env.DB.prepare(
    `INSERT INTO calibration_candidates (
      candidate_id, source_snapshot, candidate_sentence, source_snapshot_id, candidate_claim_id,
      provenance, dataset_purpose, internal_rationale, machine_reference_json, eligible_for_reader_lab,
      created_at, content_sha256, ingested_via, ingestion_actor
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)`
  )
    .bind(
      candidateId,
      normalized.source_snapshot,
      normalized.candidate_sentence,
      normalized.source_snapshot_id,
      normalized.candidate_claim_id,
      normalized.provenance,
      normalized.dataset_purpose,
      normalized.internal_rationale,
      normalized.machine_reference_json,
      normalized.eligible_for_reader_lab ? 1 : 0,
      now,
      contentHash,
      ingestedVia,
      actor
    )
    .run();

  await writeAuditLog(env, {
    action: "calibration_candidate_ingested",
    entityType: "calibration_candidate",
    entityId: candidateId,
    actor,
    contentHash,
    detail: {
      dataset_purpose: normalized.dataset_purpose,
      eligible_for_reader_lab: normalized.eligible_for_reader_lab,
      provenance: normalized.provenance,
      ingested_via: ingestedVia,
    },
  });

  return { outcome: "inserted", index, candidate_id: candidateId, eligible_for_reader_lab: normalized.eligible_for_reader_lab };
}

const REQUIRED_BUNDLE_FIELDS = ["workflow_name", "workflow_version", "candidates"];
const ALLOWED_INGESTED_VIA = ["runner", "admin_import"];

/**
 * Ingests a whole candidate bundle. Never partial-fails silently: every
 * candidate is validated and (if valid) inserted independently, and the
 * full per-candidate outcome list is always returned — a bad candidate
 * at index 2 never blocks a good one at index 0 or 4.
 *
 * Throws CandidateValidationError only for a malformed BUNDLE itself
 * (missing envelope fields, empty candidates array, missing actor) —
 * per-candidate problems are never thrown, only reported in `results`.
 */
export async function ingestCalibrationCandidates(env, bundle, { actor, ingestedVia } = {}) {
  if (!bundle || typeof bundle !== "object") {
    throw new CandidateValidationError(["bundle_must_be_an_object"]);
  }
  const missing = REQUIRED_BUNDLE_FIELDS.filter((f) => !(f in bundle));
  if (missing.length) throw new CandidateValidationError([`missing_bundle_fields: ${missing.join(", ")}`]);
  if (!Array.isArray(bundle.candidates) || bundle.candidates.length === 0) {
    throw new CandidateValidationError(["bundle.candidates must be a non-empty array"]);
  }
  if (!actor) throw new CandidateValidationError(["actor is required for audit attribution"]);
  if (!ALLOWED_INGESTED_VIA.includes(ingestedVia)) {
    throw new CandidateValidationError([`invalid ingestedVia: ${String(ingestedVia)}`]);
  }

  const results = [];
  for (let i = 0; i < bundle.candidates.length; i++) {
    results.push(await ingestOneCandidate(env, bundle.candidates[i], i, { actor, ingestedVia }));
  }

  await writeAuditLog(env, {
    action: "calibration_candidate_bundle_ingested",
    entityType: "calibration_candidate_bundle",
    entityId: `${bundle.workflow_name}@${bundle.workflow_version}`,
    actor,
    detail: {
      workflow_name: bundle.workflow_name,
      workflow_version: bundle.workflow_version,
      source_experiment_ids: bundle.source_experiment_ids || null,
      selection_rationale: bundle.selection_rationale || null,
      inserted: results.filter((r) => r.outcome === "inserted").length,
      already_present: results.filter((r) => r.outcome === "already_present").length,
      rejected: results.filter((r) => r.outcome === "rejected").length,
      ingested_via: ingestedVia,
    },
  });

  const newlyEligibleCount = results.filter((r) => r.outcome === "inserted" && r.eligible_for_reader_lab).length;

  return {
    results,
    newly_eligible_candidate_count: newlyEligibleCount,
    has_rejections: results.some((r) => r.outcome === "rejected"),
  };
}
