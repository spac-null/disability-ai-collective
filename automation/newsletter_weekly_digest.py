#!/usr/bin/env python3
"""Send weekly digest newsletter to weekly subscribers.

Collects articles published in the last 7 days from the Jekyll repo,
sends one digest email every Sunday.

THIS IS THE CANONICAL IMPLEMENTATION. It used to live, unversioned, at
/srv/scripts/ops/newsletter-weekly-digest.py; that path is now a thin wrapper that
execs this file, so there is exactly one copy of the logic and it is in git.

Usage (cron, unchanged): python3 /srv/scripts/ops/newsletter-weekly-digest.py
Preview (never sends):   python3 automation/newsletter_weekly_digest.py --preview out.html

Secrets: /srv/secrets/resend.env (RESEND_KEY)
Data:    /srv/data/newsletter/subscribers.db
Posts:   the canonical repo's _posts/
"""

import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

SECRETS_FILE = "/srv/secrets/resend.env"
DB_PATH      = "/srv/data/newsletter/subscribers.db"
# The repo this file lives in IS the content repo, so the posts directory is found
# relative to the implementation rather than hard-coded to one checkout. The env override
# exists so a test can point it at a fixture without touching production content.
POSTS_DIR    = Path(os.environ.get("CRIPMINDS_POSTS_DIR")
                    or (Path(__file__).resolve().parent.parent / "_posts"))
FROM_EMAIL   = "Crip Minds <newsletter@cripminds.com>"
SITE_URL     = "https://cripminds.com"
SUBSCRIBE_URL = "https://subscribe.cripminds.com"
NOTE_PATH    = "/srv/data/newsletter/editors-note.txt"
KOFI_URL     = "https://ko-fi.com/T8K7Z04KYU"

# Public authorship. Articles still carry per-article `author` strings from an earlier
# editorial system; those are retained provenance in front matter and are never shown to
# readers. Mirrors `public_author` in the site's _config.yml.
PUBLIC_AUTHOR = "Jascha Blume"

# The four canonical editorial perspectives, owner-approved 2026-09-13. Knowledge
# lineages, not authors. A value outside this set is ignored rather than printed, so a
# stray or legacy string can never reach a subscriber's inbox as a byline.
PERSPECTIVES = ("PINA", "MIRA", "SIIRI", "ZENO")


def _load_env():
    if not os.path.exists(SECRETS_FILE):
        return
    with open(SECRETS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))




def _esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))


def get_editors_note():
    if not os.path.exists(NOTE_PATH):
        return ""
    note = open(NOTE_PATH).read().strip()
    if not note:
        return ""
    return note

def get_recent_articles(days=7):
    """Return list of dicts for articles published in last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    articles = []
    for md in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        name = md.name
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})-(.*?)\.md$", name)
        if not m:
            continue
        y, mo, d, slug = m.groups()
        try:
            pub_date = datetime(int(y), int(mo), int(d), tzinfo=timezone.utc)
        except ValueError:
            continue
        if pub_date < cutoff:
            continue

        # Parse front matter
        content = md.read_text(encoding="utf-8")
        fm = {}
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                for line in content[3:end].splitlines():
                    if ":" in line:
                        k2, v2 = line.split(":", 1)
                        fm[k2.strip()] = v2.strip().strip('"').strip("'")

        title = fm.get("title", slug.replace("-", " ").title())

        # Hero image: the canonical one already stored in front matter. No newsletter-specific
        # asset is generated and no image model is called — this is the same file the article
        # page renders, served from the public site so email clients can fetch it.
        image = fm.get("image", "").strip()
        image_url = f"{SITE_URL}{image}" if image.startswith("/") else (image if image.startswith("http") else "")
        image_alt = fm.get("image_alt", "").strip() or title

        # EDITORIAL PERSPECTIVE. Shown only when the article genuinely carries one. It is
        # secondary metadata, never the author, and it is never back-filled from the legacy
        # persona name in `author`: an article without a perspective simply shows none, and
        # "Unknown" is never rendered.
        perspective = fm.get("perspective", "").strip()
        if perspective not in PERSPECTIVES:
            perspective = ""

        # First real paragraph as excerpt
        body = content[content.find("---", 3) + 3:].strip() if "---" in content[3:] else content
        paras = [l.strip() for l in body.split("\n")
                 if l.strip() and not l.startswith("#") and not l.startswith("!") and not l.startswith("*")]
        # Prefer the editorial dek written for exactly this purpose; fall back to the first
        # paragraph, as before, where an article carries no dek.
        dek = fm.get("dek", "").strip()
        excerpt = dek or (paras[0][:200] + ("…" if paras and len(paras[0]) > 200 else "") if paras else "")

        url = f"{SITE_URL}/{y}/{mo}/{d}/{slug}/"
        articles.append({
            "title": title,
            "excerpt": excerpt,
            "url": url,
            "date": pub_date,
            "image_url": image_url,
            "image_alt": image_alt,
            "perspective": perspective,
        })

    return articles


def build_digest(articles, unsub_token):
    unsub_url = f"{SUBSCRIBE_URL}/unsubscribe?token={unsub_token}"
    note = get_editors_note()
    if note:
        note_html_escaped = note.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        editors_note_html = f'''<tr>
      <td style="padding:16px 0 8px;border-bottom:1px solid #eee;">
        <p style="margin:0 0 4px;font-size:0.75rem;color:#888;text-transform:uppercase;letter-spacing:0.08em;">From the editor</p>
        <p style="margin:0;font-size:0.95rem;line-height:1.7;color:#333;font-style:italic;">{note_html_escaped}</p>
      </td>
    </tr>'''
    else:
        editors_note_html = ""

    now = datetime.now(timezone.utc)
    week_label = f"Week of {(now - timedelta(days=6)).strftime('%B %-d')}–{now.strftime('%-d, %Y')}"

    articles_html = ""
    for a in articles:
        # Hero image first, then byline, title, dek, link. An article with no stored image
        # simply renders the text block — the item degrades, it never breaks.
        if a["image_url"]:
            hero_html = (
                f'<a href="{a["url"]}" style="display:block;text-decoration:none;">'
                f'<img src="{a["image_url"]}" alt="{_esc(a["image_alt"])}" width="560" '
                f'style="display:block;width:100%;max-width:560px;height:auto;border:0;'
                f'outline:none;text-decoration:none;margin:0 0 14px;"></a>'
            )
        else:
            hero_html = ""
        persp_html = (
            f' &middot; <span style="letter-spacing:0.06em;">{a["perspective"]}</span>'
            if a.get("perspective") else ""
        )
        articles_html += f"""
    <tr>
      <td style="padding:24px 0;border-bottom:1px solid #eee;">
        {hero_html}
        <p style="margin:0 0 4px;font-size:0.75rem;color:#888;">{PUBLIC_AUTHOR} &middot; {a['date'].strftime('%B %-d, %Y')}{persp_html}</p>
        <h2 style="margin:0 0 10px;font-size:1.15rem;line-height:1.35;"><a href="{a['url']}" style="color:#1a1a1a;text-decoration:none;">{a['title']}</a></h2>
        <p style="margin:0 0 12px;font-size:0.95rem;line-height:1.6;color:#444;">{_esc(a['excerpt'])}</p>
        <a href="{a['url']}" style="font-size:0.85rem;color:#0066cc;text-decoration:none;">Read essay &rarr;</a>
      </td>
    </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Crip Minds — {week_label}</title></head>
<body style="font-family:Georgia,serif;max-width:600px;margin:40px auto;padding:0 20px;color:#1a1a1a;background:#fff;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td style="border-bottom:2px solid #1a1a1a;padding-bottom:12px;">
        <span style="font-size:1.1rem;font-weight:bold;letter-spacing:0.05em;text-transform:uppercase;">Crip Minds</span>
        <span style="float:right;font-size:0.8rem;color:#888;">{week_label}</span>
      </td>
    </tr>
    <tr><td style="height:8px;"></td></tr>
    {editors_note_html}
    <tr>
      <td style="font-size:0.9rem;color:#555;padding-bottom:8px;">
        {len(articles)} new Crip Minds essay{'s' if len(articles) != 1 else ''} this week.
      </td>
    </tr>
    {articles_html}
    <tr><td style="height:32px;"></td></tr>
    <tr>
      <td style="border-top:1px solid #ddd;padding-top:16px;">
        <p style="margin:0;font-size:0.75rem;color:#999;">
          You're receiving this weekly digest because you subscribed at <a href="{SITE_URL}" style="color:#999;">{SITE_URL}</a>.
          &nbsp;<a href="{unsub_url}" style="color:#999;">Unsubscribe</a>
          &nbsp;&middot;&nbsp;<a href="https://ko-fi.com/T8K7Z04KYU" style="color:#999;">Support Crip Minds</a>
        </p>
      </td>
    </tr>
  </table>
</body>
</html>"""


def get_weekly_subscribers():
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT email, token FROM subscribers WHERE confirmed=1 AND unsubscribed_at IS NULL AND frequency='weekly'"
    ).fetchall()
    conn.close()
    return [(r["email"], r["token"]) for r in rows]


def already_sent_digest(week_key):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS digest_log (week_key TEXT PRIMARY KEY, sent_at TEXT NOT NULL)")
    conn.commit()
    row = conn.execute("SELECT 1 FROM digest_log WHERE week_key=?", (week_key,)).fetchone()
    conn.close()
    return row is not None


def mark_digest_sent(week_key):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS digest_log (week_key TEXT PRIMARY KEY, sent_at TEXT NOT NULL)")
    conn.execute("INSERT OR IGNORE INTO digest_log VALUES (?, ?)",
                 (week_key, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()


def send_one(api_key, to_email, subject, html):
    payload = json.dumps({"from": FROM_EMAIL, "to": [to_email], "subject": subject, "html": html}).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails", data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "curl/7.88"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status in (200, 201)
    except urllib.error.HTTPError as e:
        print(f"[digest] Error {e.code} sending to {to_email}: {e.read().decode()}")
        return False


def preview(out_path, days=7):
    """Render the digest to a file and RETURN. Structurally cannot send.

    This function never loads the API key, never opens the subscriber database and never
    calls send_one -- the preview path and the send path do not meet. It exists so the
    digest can be checked, and tested, without a live send being one typo away.
    """
    articles = get_recent_articles(days=days)
    html = build_digest(articles, "PREVIEW-TOKEN-NOT-A-SUBSCRIBER")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"[digest] PREVIEW ONLY -- nothing sent. {len(articles)} article(s) -> {out}")
    for a in articles:
        print("  - %s | %s | image=%s | perspective=%s"
              % (a["date"].date(), a["title"][:52],
                 "yes" if a["image_url"] else "no", a["perspective"] or "-"))
    return html


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # PREVIEW IS CHECKED BEFORE ANYTHING ELSE and returns without touching secrets,
    # the subscriber database or the network.
    if "--preview" in argv:
        i = argv.index("--preview")
        out = argv[i + 1] if len(argv) > i + 1 else "digest-preview.html"
        days = 7
        if "--days" in argv:
            days = int(argv[argv.index("--days") + 1])
        preview(out, days=days)
        return

    _load_env()
    api_key = os.environ.get("RESEND_KEY", "")
    if not api_key:
        print("[digest] RESEND_KEY not set, skipping")
        return

    articles = get_recent_articles(days=7)
    if not articles:
        print("[digest] No articles in last 7 days, skipping")
        return

    week_key = datetime.now(timezone.utc).strftime("%Y-W%U")
    if already_sent_digest(week_key):
        print(f"[digest] Already sent for {week_key}, skipping")
        return

    subscribers = get_weekly_subscribers()
    if not subscribers:
        print("[digest] No weekly subscribers, skipping")
        return

    subject = f"Crip Minds — {len(articles)} new essay{'s' if len(articles) != 1 else ''} this week"
    sent = failed = 0
    for email, token in subscribers:
        html = build_digest(articles, token)
        if send_one(api_key, email, subject, html):
            sent += 1
        else:
            failed += 1

    if sent and failed == 0:
        mark_digest_sent(week_key)
    elif sent and failed > 0:
        print(f"[digest] WARNING: partial send — {failed} failures. Digest NOT marked as sent to allow retry.")
    print(f"[digest] Sent: {sent}, Failed: {failed}, Subscribers: {len(subscribers)}, Articles: {len(articles)}")


if __name__ == "__main__":
    main()
