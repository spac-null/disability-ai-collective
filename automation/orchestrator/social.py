"""
social.py — social platform posting (Bluesky, Mastodon, Tumblr, newsletter)
and the site-wide canonical-link audit.

Extracted 2026-08-09 (module-split, Stage 3 continued). Groups: per-agent post
hooks (_social_hook, _bsky_hook), the three platform posters (post_to_bluesky,
post_to_mastodon, post_to_tumblr — the last needs _tumblr_oauth_header for its
OAuth1 signing), social-URI bookkeeping (_store_pending_social, _store_social_uri),
retract_article (deletes a file + removes its social posts), _send_newsletter,
and link_audit (bulk canonical-link injection across all published articles).
Zero behavior change -- bodies copied verbatim, confirmed via direct substring
containment against git HEAD.
"""
import json
import os
import re
import sqlite3
import time
import urllib.request

from .config import OPENROUTER_URL, OPENROUTER_API_KEY, _SOCIAL_PROMPTS


class SocialMixin:
    def _social_hook(self, agent_name, title, body, max_chars=250):
        """Generate a per-agent social post. Falls back to generic _bsky_hook."""
        import os
        template = _SOCIAL_PROMPTS.get(agent_name)
        if not template:
            return self._bsky_hook(title, body, max_chars)
        try:
            prompt = template.format(title=title, excerpt=body[:1500])
            raw = self._call_openai_compat_api(
                url=OPENROUTER_URL,
                api_key=OPENROUTER_API_KEY,
                system_prompt="Return only the post text. No quotes around it. Maximum 250 characters.",
                user_prompt=prompt,
                model="anthropic/claude-sonnet-4.6",
                max_tokens=80,
                timeout=30,
            )
            if not raw:
                return self._bsky_hook(title, body, max_chars)
            raw = raw.strip().strip('"').strip("'")
            if len(raw) > max_chars:
                cut = raw[:max_chars].rfind(".")
                raw = raw[:cut + 1] if cut > max_chars // 2 else raw[:max_chars].rstrip()
            return raw
        except Exception:
            return self._bsky_hook(title, body, max_chars)

    def _bsky_hook(self, title, body, max_chars=160):
        """Generate a complete punchy hook for Bluesky, fits within max_chars."""
        import os
        budget = max_chars - 15  # safety buffer
        try:
            raw = self._call_openai_compat_api(
                url=OPENROUTER_URL,
                api_key=OPENROUTER_API_KEY,
                system_prompt=(
                    f"Write ONE complete sentence (strictly under {budget} characters, hard limit) "
                    "as a Bluesky post for a disability culture article. "
                    "Use the most specific, concrete detail in the piece — a number, a date, a named place, a quoted phrase. "
                    "Show the argument through evidence, not by stating it. "
                    "The sentence should be incomplete in meaning — the reader fills in the rest by clicking. "
                    "Must end with a period. No hashtags. No ellipsis. Do NOT start with the article title."
                ),
                user_prompt=f"Title: {title}\n\nOpening:\n{body[:600]}",
                model="anthropic/claude-sonnet-4.6",
                max_tokens=60,
                timeout=30,
            )
            if raw and len(raw) > max_chars:
                cut = raw[:max_chars].rfind(".")
                if cut > max_chars // 2:
                    raw = raw[:cut + 1]
                else:
                    word_cut = raw[:max_chars].rfind(" ")
                    raw = raw[:word_cut].rstrip() if word_cut > 0 else raw[:max_chars]
            return raw or body[:max_chars]
        except Exception:
            return body[:max_chars]

    def post_to_bluesky(self, title, body, article_file, image_filenames=None, agent_name=None):
        """Post article to Bluesky after successful commit. Non-blocking."""
        import os, json, mimetypes, urllib.request as ureq
        from datetime import datetime, timezone

        handle   = os.environ.get("BSKY_HANDLE", "")
        password = os.environ.get("BSKY_APP_PASSWORD", "")
        if not handle or not password:
            self.logger.debug("Bluesky: no credentials, skipping")
            return

        # Pure setup — no network calls, safe to do before try/except
        slug_md    = article_file.name
        parts = slug_md[:10].split("-")
        if len(parts) != 3:
            self.logger.error("Unexpected article filename format: %s", slug_md)
            return
        y, m, d = parts
        slug       = slug_md[11:].replace(".md", "")
        site_url   = os.environ.get("SITE_URL", "https://spac-null.github.io/disability-ai-collective")
        url        = f"{site_url.rstrip('/')}/{y}/{m}/{d}/{slug}/"
        auth_payload = json.dumps({"identifier": handle, "password": password}).encode()

        _agent_tags = {
            "Pixel Nova":   "#DeafCulture",
            "Siri Sage":    "#BlindLife",
            "Maya Flux":    "#CripLife",
            "Zen Circuit":  "#Neurodivergent",
        }
        _agent_tag = _agent_tags.get(agent_name, "")
        tags = f"#accessibility #DisabilitySky #CripMinds #DisabilityJustice{' ' + _agent_tag if _agent_tag else ''}"
        subscribe_line = "\ncripminds.com/subscribe"
        overhead = len(f"\n\n{tags}{subscribe_line}")
        max_hook = 300 - overhead
        hook = self._social_hook(agent_name, title, body, max_chars=max_hook)
        text = f"{hook}\n\n{tags}{subscribe_line}"

        def byte_range(s, sub):
            b, sb = s.encode(), sub.encode()
            i = b.find(sb)
            return i, i + len(sb)

        _all_tags = ["#accessibility", "#DisabilitySky", "#CripMinds", "#DisabilityJustice"]
        if _agent_tag:
            _all_tags.append(_agent_tag)
        facets = []
        for tag in _all_tags:
            ts, te = byte_range(text, tag)
            if ts >= 0:
                facets.append({"index": {"byteStart": ts, "byteEnd": te},
                               "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tag[1:]}]})
        sub_text = "cripminds.com/subscribe"
        sub_s, sub_e = byte_range(text, sub_text)
        if sub_s >= 0:
            facets.append({"index": {"byteStart": sub_s, "byteEnd": sub_e},
                           "features": [{"$type": "app.bsky.richtext.facet#link",
                                         "uri": "https://cripminds.com/subscribe"}]})

        record = None  # initialised here so retry block can always reference it

        try:
            # Auth
            with ureq.urlopen(ureq.Request(
                "https://bsky.social/xrpc/com.atproto.server.createSession",
                data=auth_payload, headers={"Content-Type": "application/json"}, method="POST",
            ), timeout=15) as r:
                session = json.loads(r.read())
            token = session["accessJwt"]
            did   = session["did"]

            # Build external card embed — article link with thumbnail
            embed = None
            thumb_blob = None
            hero = None
            if image_filenames:
                hero_name = next((fn for fn in image_filenames if "_setting_1" in fn), image_filenames[0])
                hero = self.assets_dir / hero_name
            if hero and hero.exists():
                img_bytes = hero.read_bytes()
                mime = mimetypes.guess_type(str(hero))[0] or "image/png"
                blob_req = ureq.Request(
                    "https://bsky.social/xrpc/com.atproto.repo.uploadBlob",
                    data=img_bytes,
                    headers={"Content-Type": mime, "Authorization": f"Bearer {token}"},
                    method="POST",
                )
                with ureq.urlopen(blob_req, timeout=30) as r:
                    thumb_blob = json.loads(r.read())["blob"]
                self.logger.info("Bluesky: thumbnail uploaded (%d bytes)", len(img_bytes))
            # Extract clean description — skip frontmatter first
            import re as _re
            _body = body
            if body.lstrip().startswith("---"):
                _fm_end = body.find("\n---\n", 3)
                if _fm_end != -1:
                    _body = body[_fm_end + 5:]
            desc = ""
            for line in _body.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("!") and not line.startswith("-") and not line.startswith("*") and len(line) > 40:
                    desc = _re.sub(r"\*\*|\*|`", "", line)[:200]
                    break
            external = {"uri": url, "title": title, "description": desc}
            if thumb_blob:
                external["thumb"] = thumb_blob
            embed = {"$type": "app.bsky.embed.external", "external": external}

            # Post
            record = {
                "$type": "app.bsky.feed.post",
                "text": text,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "facets": facets,
            }
            if embed:
                record["embed"] = embed

            with ureq.urlopen(ureq.Request(
                "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                data=json.dumps({"repo": did, "collection": "app.bsky.feed.post", "record": record}).encode(),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
                method="POST",
            ), timeout=15) as r:
                result = json.loads(r.read())
            uri = result.get("uri", "")
            self.logger.info("Bluesky: posted %s", uri)
            return uri

        except Exception as e:
            self.logger.warning("Bluesky post failed (attempt 1): %s — retrying in 10s", e)
            import time as _time
            _time.sleep(10)
            try:
                # Retry: re-auth and re-post
                with ureq.urlopen(ureq.Request(
                    "https://bsky.social/xrpc/com.atproto.server.createSession",
                    data=auth_payload, headers={"Content-Type": "application/json"}, method="POST",
                ), timeout=15) as r:
                    session = json.loads(r.read())
                token = session["accessJwt"]
                if record is None:
                    record = {
                        "$type": "app.bsky.feed.post",
                        "text": text,
                        "createdAt": datetime.now(timezone.utc).isoformat(),
                        "facets": facets,
                    }
                post_payload = json.dumps({"repo": session["did"], "collection": "app.bsky.feed.post", "record": record}).encode()
                with ureq.urlopen(ureq.Request(
                    "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                    data=post_payload,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    method="POST",
                ), timeout=20) as r:
                    result = json.loads(r.read())
                uri = result.get("uri", "")
                self.logger.info("Bluesky: posted on retry %s", uri)
                return uri
            except Exception as e2:
                self.logger.warning("Bluesky post failed (attempt 2): %s", e2)
                return ""


    def _store_pending_social(self, slug, title, agent):
        """Write a pending-social marker so publish_best.py can fire social posts on promotion."""
        import json as _json
        social_dir = self.repo_root / "_social"
        social_dir.mkdir(exist_ok=True)
        fpath = social_dir / f"{slug}.json"
        data = {}
        if fpath.exists():
            try:
                data = _json.loads(fpath.read_text())
            except Exception:
                pass
        data["pending_social"] = True
        data["title"] = title
        data["agent"] = agent
        fpath.write_text(_json.dumps(data, indent=2))

    def _store_social_uri(self, slug, bsky_uri, agent=None, mastodon_url=None, tumblr_url=None):
        """Persist Bluesky/Mastodon/Tumblr post identifiers so retract_article() can find them later."""
        import json as _json
        social_dir = self.repo_root / "_social"
        social_dir.mkdir(exist_ok=True)
        fpath = social_dir / f"{slug}.json"
        data = {}
        if fpath.exists():
            try:
                data = _json.loads(fpath.read_text())
            except Exception:
                pass
        if bsky_uri:
            data["bsky_uri"] = bsky_uri
        if mastodon_url:
            data["mastodon_url"] = mastodon_url
        if tumblr_url:
            data["tumblr_url"] = tumblr_url
        if agent:
            data["agent"] = agent
        fpath.write_text(_json.dumps(data, indent=2))

    def retract_article(self, slug):
        """Remove article from _posts/, assets, _reviews, _social and delete the
        Bluesky, Mastodon, and Tumblr posts, for whichever of those were recorded.

        Usage: python3 production_orchestrator.py --retract <slug>
        Slug is the part after the date, e.g. 'the-map-that-doesn-t-know-you-re-standing-in-it'
        """
        import os, json as _json, urllib.request as ureq, urllib.parse, subprocess, glob as _glob

        # Find article file (any date prefix)
        matches = list(self.posts_dir.glob(f"*-{slug}.md"))
        if not matches:
            print(f"No article found matching slug: {slug}")
            return False
        article_file = matches[0]
        date_prefix = article_file.stem[:10]

        # Collect files to remove
        to_remove = [article_file]
        review = self.repo_root / "_reviews" / f"{article_file.stem}-review.md"
        if review.exists():
            to_remove.append(review)
        social_file = self.repo_root / "_social" / f"{slug}.json"
        bsky_uri = ""
        mastodon_url = ""
        tumblr_url = ""
        if social_file.exists():
            try:
                _social_data = _json.loads(social_file.read_text())
                bsky_uri = _social_data.get("bsky_uri", "")
                mastodon_url = _social_data.get("mastodon_url", "")
                tumblr_url = _social_data.get("tumblr_url", "")
            except Exception:
                pass
            to_remove.append(social_file)
        for asset in self.assets_dir.glob(f"{slug}_*.jpg"):
            to_remove.append(asset)
        for asset in self.assets_dir.glob(f"{slug}_*.png"):
            to_remove.append(asset)

        # Delete Bluesky post
        if bsky_uri:
            handle   = os.environ.get("BSKY_HANDLE", "")
            password = os.environ.get("BSKY_APP_PASSWORD", "")
            if handle and password:
                try:
                    auth_payload = _json.dumps({"identifier": handle, "password": password}).encode()
                    with ureq.urlopen(ureq.Request(
                        "https://bsky.social/xrpc/com.atproto.server.createSession",
                        data=auth_payload, headers={"Content-Type": "application/json"}, method="POST",
                    ), timeout=15) as r:
                        session = _json.loads(r.read())
                    token = session["accessJwt"]
                    did   = session["did"]
                    # uri format: at://did:plc:xxx/app.bsky.feed.post/rkey
                    rkey = bsky_uri.split("/")[-1]
                    del_payload = _json.dumps({"repo": did, "collection": "app.bsky.feed.post", "rkey": rkey}).encode()
                    with ureq.urlopen(ureq.Request(
                        "https://bsky.social/xrpc/com.atproto.repo.deleteRecord",
                        data=del_payload,
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
                        method="POST",
                    ), timeout=15) as r:
                        r.read()
                    print(f"Bluesky post deleted: {bsky_uri}")
                except Exception as e:
                    print(f"Bluesky delete failed: {e}")
            else:
                print(f"No Bluesky credentials — skipping delete (URI was: {bsky_uri})")
        else:
            print("No Bluesky URI stored — skipping delete")

        # Delete Mastodon post — mastodon_url has been persisted since the
        # post_to_mastodon fix, but retraction never actually used it, leaving a
        # live Mastodon post pointing at a 404 on every retraction until now.
        if mastodon_url:
            token    = os.environ.get("MASTODON_ACCESS_TOKEN", "")
            instance = os.environ.get("MASTODON_INSTANCE", "").rstrip("/")
            if token and instance:
                try:
                    status_id = mastodon_url.rstrip("/").split("/")[-1]
                    del_req = ureq.Request(
                        f"{instance}/api/v1/statuses/{status_id}",
                        headers={"Authorization": f"Bearer {token}"},
                        method="DELETE",
                    )
                    with ureq.urlopen(del_req, timeout=15) as r:
                        r.read()
                    print(f"Mastodon post deleted: {mastodon_url}")
                except Exception as e:
                    print(f"Mastodon delete failed: {e}")
            else:
                print(f"No Mastodon credentials — skipping delete (URL was: {mastodon_url})")
        else:
            print("No Mastodon URL stored — skipping delete")

        # Delete Tumblr post — same story as Mastodon: post_to_tumblr's own
        # docstring implies retraction covers it, but nothing ever called the
        # delete endpoint. tumblr_url is "https://{blog}.tumblr.com/post/{id}";
        # blog is re-derived from the URL rather than trusting TUMBLR_BLOG's
        # current env value, in case that ever changes.
        if tumblr_url:
            ck  = os.environ.get("TUMBLR_CONSUMER_KEY", "")
            cs  = os.environ.get("TUMBLR_CONSUMER_SECRET", "")
            at  = os.environ.get("TUMBLR_ACCESS_TOKEN", "")
            ats = os.environ.get("TUMBLR_ACCESS_TOKEN_SECRET", "")
            if all([ck, cs, at, ats]):
                try:
                    _parts = tumblr_url.rstrip("/").split("/")
                    post_id = _parts[-1]
                    blog_host = tumblr_url.split("//", 1)[1].split("/", 1)[0]  # "<blog>.tumblr.com"
                    api_url = f"https://api.tumblr.com/v2/blog/{blog_host}/post/delete"
                    body_params = {"id": post_id}
                    auth = self._tumblr_oauth_header("POST", api_url, ck, cs, at, ats, {}, body_params)
                    del_req = ureq.Request(
                        api_url,
                        data=urllib.parse.urlencode(body_params).encode(),
                        headers={"Authorization": auth,
                                 "Content-Type": "application/x-www-form-urlencoded"},
                        method="POST",
                    )
                    with ureq.urlopen(del_req, timeout=20) as r:
                        r.read()
                    print(f"Tumblr post deleted: {tumblr_url}")
                except Exception as e:
                    print(f"Tumblr delete failed: {e}")
            else:
                print(f"No Tumblr credentials — skipping delete (URL was: {tumblr_url})")
        else:
            print("No Tumblr URL stored — skipping delete")

        # git rm + commit + push
        for f in to_remove:
            subprocess.run(["git", "rm", "-f", str(f)], cwd=str(self.repo_root), capture_output=True)
        msg = f"retract: remove {article_file.name}"
        subprocess.run(["git", "commit", "-m", msg], cwd=str(self.repo_root), check=True)
        self._git_push_safe()
        print(f"Retracted: {article_file.name}")
        return True


    def post_to_mastodon(self, title, body, article_file, image_filenames=None, agent_name=None):
        """Post article to Mastodon after successful commit. Non-blocking."""
        import os, json, mimetypes, urllib.request as ureq, urllib.parse

        token    = os.environ.get("MASTODON_ACCESS_TOKEN", "")
        instance = os.environ.get("MASTODON_INSTANCE", "").rstrip("/")
        if not token or not instance:
            self.logger.debug("Mastodon: no credentials, skipping")
            return None

        try:
            slug_md  = article_file.name
            parts = slug_md[:10].split("-")
            if len(parts) != 3:
                self.logger.error("Unexpected article filename format: %s", slug_md)
                return None
            y, m, d  = parts
            slug     = slug_md[11:].replace(".md", "")
            site_url = os.environ.get("SITE_URL", "https://cripminds.com")
            url      = f"{site_url.rstrip('/')}/{y}/{m}/{d}/{slug}/"

            # Hook — 500 char limit; URL counts as ~23; leave room for tags + spacing
            tags = "#DisabilityJustice #CripMinds #DisabilityArts #AccessibilityMatters"
            # url(23) + newlines(2) + tags + newlines(2) = overhead
            overhead = 23 + 2 + len(tags) + 2
            max_hook = 500 - overhead
            hook = self._social_hook(agent_name, title, body, max_chars=max_hook)
            status_text = f"{hook}\n\n{url}\n\n{tags}"

            headers = {"Authorization": f"Bearer {token}"}

            # Upload hero image as media attachment
            media_id = None
            hero = None
            if image_filenames:
                hero_name = next((fn for fn in image_filenames if "_setting_1" in fn), image_filenames[0])
                hero = self.assets_dir / hero_name
            if hero and hero.exists():
                img_bytes = hero.read_bytes()
                mime = mimetypes.guess_type(str(hero))[0] or "image/jpeg"
                boundary = "----MastodonBoundary"
                body_parts = (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="file"; filename="{hero.name}"\r\n'
                    f"Content-Type: {mime}\r\n\r\n"
                ).encode() + img_bytes + f"\r\n--{boundary}--\r\n".encode()
                media_req = ureq.Request(
                    f"{instance}/api/v2/media",
                    data=body_parts,
                    headers={**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"},
                    method="POST",
                )
                with ureq.urlopen(media_req, timeout=30) as r:
                    media = json.loads(r.read())
                media_id = media.get("id")
                self.logger.info("Mastodon: media uploaded id=%s", media_id)

            # Post status
            params = {"status": status_text, "visibility": "public"}
            if media_id:
                params["media_ids[]"] = media_id
            post_req = ureq.Request(
                f"{instance}/api/v1/statuses",
                data=urllib.parse.urlencode(params).encode(),
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with ureq.urlopen(post_req, timeout=15) as r:
                result = json.loads(r.read())
            self.logger.info("Mastodon: posted %s", result.get("url", "?"))
            return result.get("url")

        except Exception as e:
            self.logger.warning("Mastodon post failed: %s", e)
            return None


    @staticmethod
    def _tumblr_oauth_header(method, url, ck, cs, at, ats, params=None, body_params=None):
        """OAuth 1.0a HMAC-SHA1 Authorization header for a Tumblr API request.

        Extracted from post_to_tumblr (previously a local closure there, so
        retract_article had no way to sign a delete request and could never
        actually remove a Tumblr post despite post_to_tumblr's own docstring
        mentioning it).
        """
        import hmac, hashlib, base64, time, uuid, urllib.parse
        ts    = str(int(time.time()))
        nonce = uuid.uuid4().hex
        oauth = {
            "oauth_consumer_key":     ck,
            "oauth_nonce":            nonce,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp":        ts,
            "oauth_token":            at,
            "oauth_version":          "1.0",
        }
        all_params = {k: v for k, v in {**oauth, **(params or {}), **(body_params or {})}.items() if v is not None}
        sorted_params = "&".join(
            f"{urllib.parse.quote(k, safe='')}"
            f"={urllib.parse.quote(str(v), safe='')}"
            for k, v in sorted(all_params.items())
        )
        base = "&".join([
            urllib.parse.quote(method.upper(), safe=""),
            urllib.parse.quote(url, safe=""),
            urllib.parse.quote(sorted_params, safe=""),
        ])
        signing_key = f"{urllib.parse.quote(cs, safe='')}&{urllib.parse.quote(ats, safe='')}"
        sig = base64.b64encode(
            hmac.new(signing_key.encode(), base.encode(), hashlib.sha1).digest()
        ).decode()
        oauth["oauth_signature"] = sig
        return "OAuth " + ", ".join(
            f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
            for k, v in sorted(oauth.items())
        )

    def post_to_tumblr(self, title, body, article_file, image_filenames=None, agent_name=None):
        """Post article to Tumblr after successful commit. Non-blocking. OAuth 1.0a HMAC-SHA1."""
        import os, json, mimetypes, urllib.request as ureq, urllib.parse

        ck  = os.environ.get("TUMBLR_CONSUMER_KEY", "")
        cs  = os.environ.get("TUMBLR_CONSUMER_SECRET", "")
        at  = os.environ.get("TUMBLR_ACCESS_TOKEN", "")
        ats = os.environ.get("TUMBLR_ACCESS_TOKEN_SECRET", "")
        blog = os.environ.get("TUMBLR_BLOG", "").strip().rstrip(".tumblr.com")
        if not all([ck, cs, at, ats, blog]):
            self.logger.debug("Tumblr: no credentials, skipping")
            return None

        def _oauth_header(method, url, params, body_params=None):
            return self._tumblr_oauth_header(method, url, ck, cs, at, ats, params, body_params)

        try:
            slug_md  = article_file.name
            parts = slug_md[:10].split("-")
            if len(parts) != 3:
                self.logger.error("Unexpected article filename format: %s", slug_md)
                return None
            y, m, d  = parts
            slug     = slug_md[11:].replace(".md", "")
            site_url = os.environ.get("SITE_URL", "https://cripminds.com")
            url      = f"{site_url.rstrip('/')}/{y}/{m}/{d}/{slug}/"

            hook = self._bsky_hook(title, body, max_chars=250)
            tags = "disability justice,crip culture,disability arts,accessibility,creative technology,cripminds"

            api_url = f"https://api.tumblr.com/v2/blog/{blog}/post"

            # Try photo post with hero image, fall back to link post
            hero = None
            if image_filenames:
                hero_name = next((fn for fn in image_filenames if "_setting_1" in fn), image_filenames[0])
                hero = self.assets_dir / hero_name

            if hero and hero.exists():
                img_bytes = hero.read_bytes()
                mime = mimetypes.guess_type(str(hero))[0] or "image/jpeg"
                boundary = "----TumblrBoundary"
                def _part(name, value):
                    return (f"--{boundary}\r\nContent-Disposition: form-data; "
                            f'name="{name}"\r\n\r\n{value}\r\n').encode()
                body_bytes = (
                    b"".join([
                        _part("type", "photo"),
                        _part("caption", f'<p>{__import__("html").escape(hook)}</p><p><a href="{url}">{__import__("html").escape(title)}</a></p>'),
                        _part("link", url),
                        _part("tags", tags),
                        _part("native_inline_images", "true"),
                        f"--{boundary}\r\nContent-Disposition: form-data; "
                        f'name="data[0]"; filename="{hero.name}"\r\n'
                        f"Content-Type: {mime}\r\n\r\n".encode()
                        + img_bytes
                        + f"\r\n--{boundary}--\r\n".encode()
                    ])
                )
                # Multipart body params must NOT be included in OAuth signature (OAuth 1.0a spec)
                auth = _oauth_header("POST", api_url, {}, {})
                req = ureq.Request(
                    api_url, data=body_bytes,
                    headers={"Authorization": auth,
                             "Content-Type": f"multipart/form-data; boundary={boundary}"},
                    method="POST",
                )
            else:
                body_params = {
                    "type": "link", "title": title, "url": url,
                    "description": hook, "tags": tags,
                }
                auth = _oauth_header("POST", api_url, {}, body_params)
                req = ureq.Request(
                    api_url,
                    data=urllib.parse.urlencode(body_params).encode(),
                    headers={"Authorization": auth,
                             "Content-Type": "application/x-www-form-urlencoded"},
                    method="POST",
                )

            with ureq.urlopen(req, timeout=20) as r:
                result = json.loads(r.read())
            post_id = result.get("response", {}).get("id", "?")
            tumblr_url = f"https://{blog}.tumblr.com/post/{post_id}"
            self.logger.info("Tumblr: posted id=%s → %s", post_id, tumblr_url)
            return tumblr_url

        except Exception as e:
            self.logger.warning("Tumblr post failed: %s", e)
            return None


    def _send_newsletter(self, title, content, article_file, agent_name):
        """Send newsletter to subscribers via newsletter-send.py (non-blocking)."""
        import subprocess, os
        try:
            slug_md = article_file.name
            parts = slug_md[:10].split("-")
            if len(parts) != 3:
                self.logger.error("Unexpected article filename format: %s", slug_md)
                return
            y, m, d = parts
            slug = slug_md[11:].replace(".md", "")
            site_url = os.environ.get("SITE_URL", "https://cripminds.com")
            url = f"{site_url.rstrip('/')}/{y}/{m}/{d}/{slug}/"

            # Extract first paragraph as excerpt
            lines = [l.strip() for l in content.split("\n") if l.strip() and not l.startswith("#") and not l.startswith("!") and not l.startswith("*")]
            excerpt = lines[0][:280] + ("…" if len(lines[0]) > 280 else "") if lines else ""

            result = subprocess.run(
                ["python3", "/srv/scripts/ops/newsletter-send.py",
                 "--title", title, "--url", url, "--excerpt", excerpt, "--author", agent_name],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                self.logger.warning("Newsletter send failed (exit %d): %s", result.returncode, result.stderr.strip())
            else:
                self.logger.info("Newsletter: %s", result.stdout.strip() or result.stderr.strip())
        except Exception as e:
            self.logger.warning("Newsletter send failed: %s", e)

    def link_audit(self, dry_run: bool = False) -> dict:
        """Scan all published articles and inject links for any that slipped through.

        Equivalent to the Opus rewrite guard — catches articles where smart_inject_links
        failed (network timeout, Haiku error, predates the system, etc.).

        Args:
            dry_run: if True, report what would change without writing files.

        Returns:
            {"audited": N, "updated": [...filenames], "skipped": [...]}
        """
        import re as _re

        posts = sorted(self.posts_dir.glob("*.md"), reverse=True)
        results = {"audited": len(posts), "updated": [], "skipped": []}

        for post in posts:
            try:
                content = post.read_text(encoding="utf-8")
                parts = content.split("---", 2)
                if len(parts) != 3:
                    results["skipped"].append(post.name)
                    continue

                fm, body = "---" + parts[1] + "---", parts[2]

                new_body = self.smart_inject_links(body)
                new_body = self.inject_canonical_links(new_body)

                if new_body == body:
                    self.logger.debug("link_audit: clean — %s", post.name)
                    continue

                # Diff: what was added?
                old_links = set(_re.findall(r'\[([^\]]+)\]\(([^)]+)\)', body))
                new_links = set(_re.findall(r'\[([^\]]+)\]\(([^)]+)\)', new_body))
                added = new_links - old_links

                self.logger.info(
                    "link_audit: %s — +%d links: %s",
                    post.name, len(added),
                    ", ".join(f"[{t}]" for t, _ in added)
                )

                if not dry_run:
                    post.write_text(fm + new_body, encoding="utf-8")

                results["updated"].append({
                    "file": post.name,
                    "added": [{"text": t, "url": u} for t, u in sorted(added)],
                })

            except Exception as e:
                self.logger.warning("link_audit: error on %s — %s", post.name, e)
                results["skipped"].append(post.name)

        if not dry_run and results["updated"]:
            # Commit all updated articles in one batch
            try:
                import subprocess as _sp
                updated_paths = [str(self.posts_dir / r["file"]) for r in results["updated"]]
                for p in updated_paths:
                    _sp.run(["git", "add", p], check=True, cwd=self.repo_root)
                count = len(results["updated"])
                _sp.run(
                    ["git", "commit", "-m",
                     f"audit: inject missing links in {count} article(s)\n\n"
                     + "\n".join(f"- {r['file']}: +{len(r['added'])} links" for r in results["updated"])],
                    check=True, cwd=self.repo_root,
                )
                self._git_push_safe()
                self.logger.info("link_audit: committed + pushed %d article(s)", count)
            except Exception as e:
                self.logger.warning("link_audit: git commit failed — %s", e)

        return results
