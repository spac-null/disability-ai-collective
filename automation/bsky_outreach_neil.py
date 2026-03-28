#!/usr/bin/env python3
"""
One-shot Bluesky outreach to Neil Milliken (@neilmilliken.bsky.social).

Run once from trident:
  source /srv/secrets/openclaw.env  # or wherever BSKY_HANDLE / BSKY_APP_PASSWORD live
  python3 automation/bsky_outreach_neil.py

DO NOT run twice — one message only per the outreach plan.
"""
import json, os, urllib.request as ureq
from datetime import datetime, timezone

API     = "https://bsky.social/xrpc"
HANDLE  = "neilmilliken.bsky.social"

POST_TEXT = (
    "@neilmilliken.bsky.social Museums frame access failures as logistics. "
    "Our piece 'The Price of Looking' (Mar 26) runs the actual numbers on what "
    "museum access costs disabled visitors. Might interest the AXS community — "
    "cripminds.com, disability-led AI arts publication.\n\n"
    "#accessibility #DisabilitySky #CripMinds"
)


def bsky(path, payload=None, token=None, method="POST"):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = ureq.Request(
        f"{API}/{path}",
        data=json.dumps(payload).encode() if payload else None,
        headers=headers,
        method=method,
    )
    with ureq.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def resolve_did(handle):
    url = f"{API}/com.atproto.identity.resolveHandle?handle={handle}"
    req = ureq.Request(url, method="GET")
    with ureq.urlopen(req, timeout=10) as r:
        return json.loads(r.read())["did"]


def byte_range(full_text, substring):
    b, sb = full_text.encode("utf-8"), substring.encode("utf-8")
    i = b.find(sb)
    return i, i + len(sb)


def main():
    bsky_handle   = os.environ.get("BSKY_HANDLE", "")
    bsky_password = os.environ.get("BSKY_APP_PASSWORD", "")
    if not bsky_handle or not bsky_password:
        print("ERROR: BSKY_HANDLE and BSKY_APP_PASSWORD must be set")
        raise SystemExit(1)

    # Auth
    session = bsky("com.atproto.server.createSession",
                   {"identifier": bsky_handle, "password": bsky_password})
    token = session["accessJwt"]
    did   = session["did"]
    print(f"Authenticated as {bsky_handle}")

    # Resolve Neil's DID for mention facet
    neil_did = resolve_did(HANDLE)
    print(f"Resolved {HANDLE} → {neil_did}")

    # Build mention facet
    mention_text = f"@{HANDLE}"
    ms, me = byte_range(POST_TEXT, mention_text)
    facets = [
        {
            "index":    {"byteStart": ms, "byteEnd": me},
            "features": [{"$type": "app.bsky.richtext.facet#mention", "did": neil_did}],
        }
    ]
    # Tag facets
    for tag in ["#accessibility", "#DisabilitySky", "#CripMinds"]:
        ts, te = byte_range(POST_TEXT, tag)
        if ts >= 0:
            facets.append({
                "index":    {"byteStart": ts, "byteEnd": te},
                "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tag[1:]}],
            })

    record = {
        "repo":       did,
        "collection": "app.bsky.feed.post",
        "record": {
            "$type":     "app.bsky.feed.post",
            "text":      POST_TEXT,
            "facets":    facets,
            "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }

    print("\nPost text:")
    print("-" * 60)
    print(POST_TEXT)
    print("-" * 60)
    print(f"({len(POST_TEXT.encode('utf-8'))} bytes)")
    confirm = input("\nPost this? [y/N] ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    result = bsky("com.atproto.repo.createRecord", record, token=token)
    uri = result.get("uri", "")
    print(f"\nPosted: {uri}")
    print(f"View:   https://bsky.app/profile/{bsky_handle}/post/{uri.split('/')[-1]}")


if __name__ == "__main__":
    main()
