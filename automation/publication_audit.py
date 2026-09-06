#!/usr/bin/env python3
"""
publication_audit.py -- what a published article keeps, so it can still be audited.

THE INCIDENT. On 2026-09-06 a small approved correction was applied to two live
articles. It needed the three factual gates re-run on the changed published bytes.
Grounding ran. Fact Check ran. SAFETY COULD NOT -- for either article, by anyone.
`composition.safety_audit` takes the writer packet, the architecture, the ledger and
the cut report from the run that published the article, and for Tollymore no run
existed anywhere on the host, while WildSumaco's run held its writer packet only as a
rendered prompt. A live article on the public site could not have its safety stage
reconstructed. That silently weakens every claim the site makes about its own checking.

WHAT THIS MODULE IS. At the publication boundary -- and only there, when an article is
actually promoted -- the run directory that produced it is copied, verbatim, into a
durable store outside the repo and outside the run workspace, together with the exact
published bytes and a manifest that binds the two. The bundle is then made read-only.
The article carries a pointer to it in its own front matter.

WHAT IT IS NOT. It is not automatic replay. `safety_audit` reaches no provider and no
network, so SAFETY is genuinely reproducible from a bundle, byte for byte, forever.
GROUNDING and FACT CHECK are model and web calls: their inputs and their original
verdicts are preserved, and a re-run is possible, but an identical verdict is not
promised and this module never says it is. `PUBLICATION.json` states which of the three
is replayable and which is merely inspectable, in those words.

WHY THE WHOLE RUN DIRECTORY. A curated subset is a subset of what someone believed the
gates consumed, and that belief is exactly what was wrong here. A run costs ~170 KB;
fifteen published articles a year is under 4 MB. Copy it all.

WHY NOT IN THE REPO. The repo is public. A run directory carries every fetched source
in full, and a research pack is other publishers' bytes. The store lives beside the
evidence root, not in the tree that ships.

BINDING. The bundle is bound to `translate_publication.bundle_sha256` -- the hash of the
published article PLUS its editorial furniture, which the Dutch edition already records
as `translation_source_bundle_sha256`. Reused rather than reinvented, and it deliberately
hashes no front matter, so stamping the pointer into the post does not invalidate it.

CLI
    python3 automation/publication_audit.py retain  _posts/<file>.md [--run <id>]
    python3 automation/publication_audit.py verify  _posts/<file>.md
    python3 automation/publication_audit.py status  [--all]
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

REPO = HERE.parent
POSTS = REPO / "_posts"

RETENTION_VERSION = 1
RETENTION_CONTRACT = "publication-audit-v1"

# Outside the repo and outside the run workspace. Both of those are the failure.
DEFAULT_AUDIT_ROOT = "/srv/data/cripminds-publication-audit"


def audit_root_default() -> str:
    """Read at call time, not import time: the cron line that runs the publisher sets
    this, and a value frozen at import is a value an operator cannot change."""
    return os.environ.get("CRIPMINDS_PUBLICATION_AUDIT_ROOT", DEFAULT_AUDIT_ROOT)


def evidence_roots() -> list:
    """Where a run directory may live. The production root first; extra roots (a replay
    capture, a rescue workspace) come from CRIPMINDS_EVIDENCE_ROOTS, colon-separated."""
    roots = [os.environ.get("NEW_ENGINE_EVIDENCE_ROOT",
                            "/srv/data/cripminds-new-engine-v1")]
    roots += [r for r in os.environ.get("CRIPMINDS_EVIDENCE_ROOTS", "").split(":") if r]
    out, seen = [], set()
    for r in roots:
        if r and r not in seen:
            seen.add(r)
            out.append(pathlib.Path(r))
    return out


# The files `composition.safety_audit` actually consumes, in the shape it takes them.
# WRITER_PACKET.txt is NOT on this list and never will be: it is the rendered prompt,
# and a prompt is not a packet. EDITORIAL_PACKAGE.json and FACTUAL_REPAIR.json are
# conditional -- a run without a package or without a repair passed neither.
SAFETY_REQUIRED = (
    "WRITER_PACKET.json", "ARCHITECTURE.json", "LEDGER.json", "CUT_REPORT.json",
    "WRITER_DRAFT.md", "ARTICLE_FINAL.md",
)
# Inputs and result for the two gates that cannot be replayed to a promised verdict.
GROUNDING_INPUTS = ("RESEARCH_PACK.json", "SOURCE_SNAPSHOT.json")
GROUNDING_RESULT = ("GROUNDING_FINDINGS.json",)
FACT_CHECK_RESULT = ("FACT_CHECK.json", "COMPOSITION_FACT_CHECK.json")

# High-precision only. A false positive here refuses a real publication, so nothing
# that could plausibly appear in prose is on this list.
SECRET_PATTERNS = (
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}")),
    ("openrouter_key", re.compile(r"sk-or-v1-[A-Za-z0-9]{16,}")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("aws_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("google_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("telegram_token", re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_\-]{30,}")),
)


class RetentionError(Exception):
    """A publication that would lose its audit inputs. Never caught-and-continued."""


# ── reading the post ────────────────────────────────────────────────────────────────

def read_post(path: pathlib.Path) -> tuple:
    """Front matter and body, via the same reader the translation stage uses, so a
    published bundle is read exactly one way in this codebase."""
    import translate_publication as TP
    return TP.read_post(path)


def published_bundle_sha256(path: pathlib.Path) -> str:
    """The hash of the published article AND its furniture -- the binding this module
    uses, and the same value a derivative edition records as its source."""
    import translate_publication as TP
    return TP.bundle_sha256(TP.english_bundle(path))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: pathlib.Path) -> str:
    return sha256_bytes(p.read_bytes())


def is_current_engine(fm: dict) -> bool:
    """Is this article from the era that HAS a run to retain?

    Three markers, any one of which is enough, because the classification decides
    whether an article may publish without retained provenance and the cheapest way
    to defeat that gate would be to drop a single front-matter line. `engine_run` is
    on the list for the same reason: an article that names a run is claiming one.
    """
    if str(fm.get("engine_generation", "")).strip() == "CURRENT_ENGINE":
        return True
    if str(fm.get("editorial_engine", "")).strip() == "NEW_ENGINE_V1":
        return True
    return bool(str(fm.get("engine_run", "") or "").strip())


def bundle_id(post_path: pathlib.Path) -> str:
    return post_path.stem


# ── locating the run ────────────────────────────────────────────────────────────────

def find_run_dir(run_id: str, roots=None) -> pathlib.Path | None:
    if not run_id:
        return None
    for root in (roots if roots is not None else evidence_roots()):
        cand = pathlib.Path(root) / run_id
        if cand.is_dir():
            return cand
    return None


def missing_safety_inputs(run_dir: pathlib.Path) -> list:
    return [n for n in SAFETY_REQUIRED if not (run_dir / n).is_file()]


def retention_feasible(fm: dict, *, roots=None) -> tuple:
    """Could this article be published AND keep what a later auditor needs?

    Returns (ok, reason). A legacy or manual article -- one carrying no CURRENT_ENGINE
    generation marker -- returns ok with its reason named. It is not blocked and its
    history is not invented: the architecture already distinguishes the two eras by
    `engine_generation`, and this reads that distinction rather than inventing one.
    """
    if not is_current_engine(fm):
        return True, "legacy/manual: no engine_generation: CURRENT_ENGINE to retain a run for"
    run_id = str(fm.get("engine_run", "") or "").strip()
    if not run_id:
        return False, ("no engine_run in front matter -- a CURRENT_ENGINE article that "
                       "cannot name its run cannot retain it")
    run_dir = find_run_dir(run_id, roots)
    if run_dir is None:
        return False, ("engine_run %r resolves to no run directory under %s"
                       % (run_id, ", ".join(str(r) for r in
                                            (roots if roots is not None
                                             else evidence_roots()))))
    missing = missing_safety_inputs(run_dir)
    if missing:
        return False, ("run %s is missing the Safety stage's own inputs: %s -- Safety "
                       "could not be re-audited after publication"
                       % (run_id, ", ".join(missing)))
    return True, "run %s carries every Safety input" % run_id


# ── assembling the bundle ───────────────────────────────────────────────────────────

def _scan_secrets(root: pathlib.Path) -> list:
    hits = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, rx in SECRET_PATTERNS:
            if rx.search(text):
                hits.append({"file": str(p.relative_to(root)), "pattern": name})
    return hits


def _inventory(root: pathlib.Path, subdir: str) -> dict:
    d = root / subdir
    if not d.is_dir():
        return {}
    return {"%s/%s" % (subdir, p.relative_to(d).as_posix()): sha256_file(p)
            for p in sorted(d.rglob("*")) if p.is_file()}


def _freeze(root: pathlib.Path) -> None:
    """Immutable after publication, as far as a filesystem can say so. Files lose write
    permission; directories keep +x so the bundle stays readable."""
    for p in sorted(root.rglob("*"), reverse=True):
        try:
            if p.is_dir():
                p.chmod(stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP
                        | stat.S_IROTH | stat.S_IXOTH)
            else:
                p.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        except OSError:
            pass


def _unfreeze(root: pathlib.Path) -> None:
    """Restore write permission so a bundle can be removed. Used on exactly two paths:
    an operator's deliberate --force replacement, and this module withdrawing a bundle
    whose publication did not complete. Never for an edit in place -- a bundle that has
    outlived its own retain() call is immutable, and the only lawful change to it is its
    removal by someone who said so."""
    for p in [root] + sorted(root.rglob("*")):
        try:
            p.chmod(0o755 if p.is_dir() else 0o644)
        except OSError:
            pass


def _remove_bundle(dest: pathlib.Path) -> None:
    _unfreeze(dest)
    shutil.rmtree(dest, ignore_errors=True)


def _reaudit_report(run_dir: pathlib.Path | None) -> dict:
    """What can honestly be done with this bundle later. Written as a claim someone can
    check, not as reassurance."""
    if run_dir is None:
        return {
            "SAFETY": {"possible": False, "kind": "NO_RUN_RETAINED",
                       "detail": "no engine run was retained for this article"},
            "GROUNDING": {"possible": False, "kind": "NO_RUN_RETAINED", "detail": ""},
            "FACT_CHECK": {"possible": False, "kind": "NO_RUN_RETAINED", "detail": ""},
        }
    missing = missing_safety_inputs(run_dir)
    have = lambda names: [n for n in names if (run_dir / n).is_file()]   # noqa: E731
    return {
        "SAFETY": {
            "possible": not missing,
            "kind": "DETERMINISTIC_REPLAY" if not missing else "INCOMPLETE",
            "function": "new_engine_v1.composition.safety_audit",
            "missing": missing,
            "detail": ("safety_audit reaches no provider and no network. Called with the "
                       "retained packet, architecture, ledger, cut report, negative "
                       "lineage, draft and final text it reproduces its verdict exactly, "
                       "at any later date, whatever the models have since become."
                       if not missing else
                       "the retained run does not carry every input safety_audit takes"),
            "original_result": "run/SAFETY_AUDIT.json",
            "replay_descriptor": "run/SAFETY_REPLAY.json",
        },
        "GROUNDING": {
            "possible": bool(have(GROUNDING_INPUTS)),
            "kind": "INPUTS_AND_RESULT_PRESERVED",
            "detail": ("grounding is a model call against fetched sources. The frozen "
                       "research pack, the source snapshot and the original findings are "
                       "retained, so the question and the answer stay inspectable and a "
                       "re-run is possible -- but an identical verdict is NOT promised, "
                       "because the provider is not frozen with them."),
            "inputs_retained": ["run/%s" % n for n in have(GROUNDING_INPUTS)],
            "original_result": ["run/%s" % n for n in have(GROUNDING_RESULT)],
        },
        "FACT_CHECK": {
            "possible": bool(have(FACT_CHECK_RESULT)),
            "kind": "INPUTS_AND_RESULT_PRESERVED",
            "detail": ("the fact check reads the live web. Its per-claim record is "
                       "retained; the web it read is not, and cannot be. A re-run "
                       "answers today's web, not the web of the publication date."),
            "original_result": ["run/%s" % n for n in have(FACT_CHECK_RESULT)],
        },
    }


def _translation_editions(post_path: pathlib.Path, binding: str) -> list:
    """Derivative editions and whether each one still renders the bytes it names."""
    import translate_publication as TP
    out = []
    for lang, cfg in TP.LANGUAGES.items():
        p = REPO / cfg["collection"] / ("%s.md" % TP.slug_of(post_path))
        if not p.is_file():
            continue
        fm, _ = TP.read_post(p)
        declared = str(fm.get("translation_source_bundle_sha256", "") or "")
        out.append({"lang": lang, "path": str(p.relative_to(REPO)),
                    "translation_source_bundle_sha256": declared,
                    "matches_published_bundle": declared == binding})
    return out


def _stamp(post_path: pathlib.Path, fields: list) -> None:
    """Write the pointer into the article's own front matter.

    Inserted directly after the opening delimiter, which is the one position that cannot
    land inside the `sources:` block sequence at the end. It changes no field the binding
    hash reads -- bundle_sha256 hashes the article and the package fields, never the
    front matter -- so stamping cannot invalidate the bundle it points at.
    """
    text = post_path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL)
    if not m:
        raise RetentionError("%s has no front matter to stamp" % post_path.name)
    fm_text, body = m.group(1), text[m.end():]
    # Idempotent, and confined to the front matter: a re-stamp replaces the previous
    # pointer rather than stacking one, and the body is never rewritten by this.
    for k, _v in fields:
        fm_text = re.sub(r"^%s:.*\n" % re.escape(k), "", fm_text, count=1,
                         flags=re.MULTILINE)
    block = "".join("%s: %s\n" % (k, json.dumps(v) if isinstance(v, str) else v)
                    for k, v in fields)
    post_path.write_text("---\n" + block + fm_text + "---\n" + body, encoding="utf-8")


def retain(post_path, *, audit_root=None, roots=None, run_id=None,
           stamp=True, force=False, now=None) -> dict:
    """Assemble, verify and freeze the publication audit bundle for one published article.

    Raises RetentionError rather than returning a partial bundle. A caller at the
    publication boundary is expected to let that abort the publication.
    """
    post_path = pathlib.Path(post_path)
    root = pathlib.Path(audit_root or audit_root_default())
    now = now or datetime.datetime.now(datetime.timezone.utc)
    fm, body = read_post(post_path)
    bid = bundle_id(post_path)
    dest = root / bid
    tmp = root / (".tmp-%s" % bid)

    if dest.exists() and not force:
        raise RetentionError(
            "a publication audit bundle already exists at %s. A bundle is immutable "
            "after publication; re-retaining is an operator decision (--force)." % dest)

    rid = str(run_id or fm.get("engine_run", "") or "").strip()
    run_dir = find_run_dir(rid, roots)
    modern = is_current_engine(fm)
    if modern:
        ok, why = retention_feasible(dict(fm, engine_run=rid), roots=roots)
        if not ok:
            raise RetentionError(
                "%s is a CURRENT_ENGINE article and %s. Publishing it would put an "
                "article on the site whose safety stage nobody can ever re-audit."
                % (post_path.name, why))

    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    if run_dir is not None:
        shutil.copytree(run_dir, tmp / "run")

    hits = _scan_secrets(tmp)
    if hits:
        shutil.rmtree(tmp, ignore_errors=True)
        raise RetentionError(
            "refusing to retain: secret-shaped material in the run directory (%s)"
            % ", ".join("%s in %s" % (h["pattern"], h["file"]) for h in hits[:5]))

    inv = _inventory(tmp, "run")
    audit_sha = sha256_bytes(json.dumps(inv, sort_keys=True).encode("utf-8"))
    binding = published_bundle_sha256(post_path)

    shutil.copy2(post_path, tmp / "PUBLISHED.md")
    manifest = {
        "retention_version": RETENTION_VERSION,
        "retention_contract": RETENTION_CONTRACT,
        "bundle_id": bid,
        "retained_at": now.isoformat(),
        "article": {
            "path": str(post_path.relative_to(REPO)) if post_path.is_relative_to(REPO)
                    else post_path.name,
            "title": fm.get("title", ""),
            "date": str(fm.get("date", "")),
            "author": fm.get("author", ""),
            "published_copy": "PUBLISHED.md",
        },
        "binding": {
            "published_bundle_sha256": binding,
            "published_body_sha256": sha256_bytes(body.encode("utf-8")),
            "published_file_sha256": sha256_file(tmp / "PUBLISHED.md"),
            "published_file_sha256_is": ("the file BEFORE the audit pointer was stamped "
                                         "into its front matter. The pointer is written "
                                         "last, on purpose -- a bundle that exists "
                                         "without a pointer is recoverable, a pointer to "
                                         "a bundle that does not exist is a lie."),
            "audit_bundle_sha256": audit_sha,
            "audit_bundle_sha256_is": ("sha256 of the canonical JSON map of every "
                                       "retained run/ file to its own sha256"),
        },
        "provenance": {
            "engine_generation": fm.get("engine_generation", ""),
            "editorial_engine": fm.get("editorial_engine", ""),
            "engine_version": fm.get("engine_version", ""),
            "engine_decision": fm.get("engine_decision", ""),
            "engine_run": rid,
            "source_url": fm.get("source_url", ""),
            "source_sha256": fm.get("source_sha256", ""),
            "provider_model": fm.get("provider_model", ""),
            "publication_safety_profile": fm.get("publication_safety_profile", ""),
            "publication_safety_version": fm.get("publication_safety_version", ""),
            "run_dir_origin": str(run_dir) if run_dir else "",
        },
        "class": "CURRENT_ENGINE" if modern else "LEGACY_OR_MANUAL",
        "class_note": ("" if modern else
                       "This article carries no CURRENT_ENGINE generation marker. No "
                       "engine run is claimed for it and none has been invented; what is "
                       "retained is the published bytes and this record."),
        "reaudit": _reaudit_report(run_dir),
        "translations": _translation_editions(post_path, binding),
        "secret_scan": {"patterns_checked": [n for n, _ in SECRET_PATTERNS], "hits": []},
        "files": inv,
    }
    (tmp / "PUBLICATION.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8")

    if dest.exists():
        # Only reachable under --force: the guard at the top of retain() has already
        # refused an existing bundle otherwise. Frozen files cannot simply be removed.
        _remove_bundle(dest)
    tmp.rename(dest)
    _freeze(dest)

    # THE POINTER GOES IN LAST, once the bundle it names is on disk and frozen. It
    # changes no field `bundle_sha256` reads -- that hash covers the article and the
    # package, never the front matter -- and the check below proves it on every run
    # rather than trusting the comment.
    if stamp:
        # AND IF THE POINTER CANNOT BE WRITTEN, THE BUNDLE IS WITHDRAWN. A bundle whose
        # article never came to point at it is not a spare: it is an orphan that would
        # refuse the next honest attempt at the same publication, and there is
        # deliberately no override flag to get past that refusal. So this call leaves
        # either a stamped article beside a frozen bundle, or neither.
        try:
            _stamp(post_path, [("audit_bundle", bid),
                               ("audit_bundle_sha256", audit_sha),
                               ("published_bundle_sha256", binding)])
            after = published_bundle_sha256(post_path)
            if after != binding:
                raise RetentionError(
                    "stamping the pointer changed the published bundle hash (%s -> %s); "
                    "the bundle would not describe the article it is attached to"
                    % (binding[:12], after[:12]))
        except Exception:
            _remove_bundle(dest)
            raise
    return manifest


# ── verifying afterwards ────────────────────────────────────────────────────────────

def load(bid: str, *, audit_root=None) -> dict:
    p = pathlib.Path(audit_root or audit_root_default()) / bid / "PUBLICATION.json"
    if not p.is_file():
        raise RetentionError("no publication audit bundle at %s" % p)
    return json.loads(p.read_text(encoding="utf-8"))


def verify(post_path, *, audit_root=None) -> dict:
    """Does this published article still resolve to a bundle that describes it?"""
    post_path = pathlib.Path(post_path)
    root = pathlib.Path(audit_root or audit_root_default())
    fm, _body = read_post(post_path)
    problems = []
    bid = str(fm.get("audit_bundle", "") or "").strip()
    if not bid:
        return {"ok": False, "post": post_path.name, "bundle": "",
                "problems": ["no audit_bundle pointer in front matter"],
                "class": "CURRENT_ENGINE" if is_current_engine(fm) else "LEGACY_OR_MANUAL"}
    man = load(bid, audit_root=root)
    binding = published_bundle_sha256(post_path)
    if binding != man["binding"]["published_bundle_sha256"]:
        problems.append(
            "published bundle hash %s does not match the retained %s -- the article has "
            "changed since it was retained"
            % (binding[:12], man["binding"]["published_bundle_sha256"][:12]))
    if str(fm.get("audit_bundle_sha256", "")) != man["binding"]["audit_bundle_sha256"]:
        problems.append("audit_bundle_sha256 in front matter does not match the manifest")
    live = _inventory(root / bid, "run")
    if live != man["files"]:
        gone = sorted(set(man["files"]) - set(live))
        changed = sorted(k for k in set(man["files"]) & set(live)
                         if live[k] != man["files"][k])
        if gone:
            problems.append("missing from the bundle: %s" % ", ".join(gone[:6]))
        if changed:
            problems.append("altered in the bundle: %s" % ", ".join(changed[:6]))
    return {"ok": not problems, "post": post_path.name, "bundle": bid,
            "class": man.get("class", ""), "problems": problems,
            "reaudit": {k: v.get("kind") for k, v in man.get("reaudit", {}).items()}}


def status(*, audit_root=None, roots=None) -> list:
    out = []
    for p in sorted(POSTS.glob("*.md")):
        fm, _ = read_post(p)
        row = {"post": p.name,
               "class": "CURRENT_ENGINE" if is_current_engine(fm) else "LEGACY_OR_MANUAL",
               "engine_run": str(fm.get("engine_run", "") or ""),
               "audit_bundle": str(fm.get("audit_bundle", "") or "")}
        if row["audit_bundle"]:
            try:
                row["verify"] = verify(p, audit_root=audit_root)["ok"]
            except RetentionError as e:
                row["verify"] = False
                row["problem"] = str(e)[:160]
        else:
            ok, why = retention_feasible(fm, roots=roots)
            row["verify"] = None
            row["retention_feasible"] = ok
            row["problem"] = "" if ok else why
        out.append(row)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("retain", help="assemble and freeze the bundle for a published post")
    r.add_argument("post")
    r.add_argument("--run", default=None, help="engine run id, if not in front matter")
    r.add_argument("--audit-root", default=None)
    r.add_argument("--no-stamp", action="store_true")
    r.add_argument("--force", action="store_true",
                   help="replace an existing bundle (an operator decision)")
    v = sub.add_parser("verify", help="check a published post against its bundle")
    v.add_argument("post")
    v.add_argument("--audit-root", default=None)
    s = sub.add_parser("status", help="every published post and its retention state")
    s.add_argument("--audit-root", default=None)
    a = ap.parse_args(argv)

    try:
        if a.cmd == "retain":
            man = retain(a.post, audit_root=a.audit_root, run_id=a.run,
                         stamp=not a.no_stamp, force=a.force)
            print(json.dumps({k: man[k] for k in
                              ("bundle_id", "class", "binding", "reaudit")},
                             indent=2, sort_keys=True))
            return 0
        if a.cmd == "verify":
            res = verify(a.post, audit_root=a.audit_root)
            print(json.dumps(res, indent=2, sort_keys=True))
            return 0 if res["ok"] else 1
        rows = status(audit_root=a.audit_root)
        for row in rows:
            print("%-70s %-18s %s" % (row["post"][:70], row["class"],
                                      row.get("problem") or
                                      ("bundle=%s verify=%s" % (row["audit_bundle"] or "-",
                                                                row["verify"]))))
        return 0
    except RetentionError as e:
        print("RETENTION ERROR: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
