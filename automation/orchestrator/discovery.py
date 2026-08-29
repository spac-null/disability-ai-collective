"""
discovery.py — topic/discovery pipeline: RSS fetching, news-seed DB, article-
diversity nudges (beats, themes, references, title patterns, openings), and
the register/length/article-type pickers.

Extracted 2026-08-09 (module-split, Stage 3 continued). This is everything
that decides WHAT to write about and how to keep daily output from repeating
itself (overused themes, recent title patterns, blocked theorists, cross-
persona reference tracking) — one coherent concern, even though it spans many
small methods. Zero behavior change -- bodies copied verbatim, confirmed via
direct substring containment against git HEAD.
"""
import html as _html_entities
import http.client
import io
import json
import random
import re
import socket
import sqlite3
import sys
from pathlib import Path
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from .grounding import STORY_REJECTION_CONTRACT_VERSION
from .config import (
    _REGISTERS, _LENGTHS, _ARTICLE_TYPES, _THEME_CLUSTERS, _AGENT_BEATS,
    _PERSONA_CONFLICTS, _STRUCTURAL_SHAPES, _SCRIPT_DIR,
)

try:
    from curl_cffi import requests as _curl_cffi_requests
except ImportError:
    _curl_cffi_requests = None

try:
    import trafilatura as _trafilatura
except ImportError:
    _trafilatura = None

# Canonical source-text ceiling (raised 2026-08-14, human-detail provenance +
# source-truncation audit; was 6000, itself raised from an original 3000-char
# default set 2026-03-15, the day source fetching was first built -- no
# technical justification for either number was ever recorded, same class of
# stale, unrevisited limit as item H's engagement-read truncation fixed
# earlier this pass). Confirmed live during this audit: a 2026-05-04 Conversation
# source article ran ~1,800-1,900 words (~10,800 chars) -- the OLD 3000-char
# generation-path cap would have captured barely a quarter of it, and even the
# old 6000-char repair-path cap misses over 40%. Whatever this pipeline's own
# quote-hoisting/testimony logic operates on must be the FULL article, not an
# arbitrary early slice, or evidence appearing later in a source is silently
# invisible to every downstream stage regardless of how good that logic is.
# 20000 is a generous multiple of the longest real source measured this
# session, not a literal "no limit" -- still a safety ceiling against a
# genuinely malformed/runaway extraction, not a load-bearing token budget.
# get_source_text always fetches/caches at this size and slices down for
# smaller callers (none request less today -- see generate.py's
# _SOURCE_TEXT_MAX_CHARS, now unified with this same value), so whichever
# pipeline stage calls first serves every later stage regardless of call
# order or requested size.
_SOURCE_TEXT_CACHE_MAX_CHARS = 20000

# SOURCE_ACQUISITION_RETRY_V1 (2026-08-23).
#
# The 2026-08-23 natural run fetched ~286 chars of JavaScript/error shell from
# lemonde.fr. Crucially that is ABOVE fetch_source_article's own long-standing
# "<200 chars" extraction-failure check, so the snapshot was labelled
# `fetched_article` and flowed downstream as if it were a real article; Story
# Rejection then correctly found no story content and the whole daily run ended.
#
# The gate below therefore does NOT lean on a single character count. Primary
# signals are structured/structural -- the fetch's own origin state and the
# absence of an article body (paragraph count) -- with markers and a length
# floor only as backstops. See classify_source_acquisition.
# ACQUISITION_HARD_BOUND_V1 (2026-08-29).
#
# urlopen(timeout=N) is a SOCKET-OPERATION timeout, not a total-transfer one: it
# bounds each individual blocking recv, and every recv that returns data resets it.
# A server returning one byte every N-1 seconds therefore keeps a fetch alive
# indefinitely -- 500,000 bytes at 1 byte per 9.9s is roughly 57 days -- and no
# exception is ever raised, so no amount of exception handling upstream helps.
# Nothing outside Python bounds it either: the cron line has no timeout(1) wrapper.
#
# That mattered little while acquisition happened once per run for one anchor. It
# matters now: Selector V2's shadow acquires up to a day's candidates BEFORE the
# authoritative article pipeline, so one stalled read would stall the daily run.
#
# The bound below is a real wall-clock deadline, enforced by shrinking the socket
# timeout to the time remaining before each read. Each individual read is therefore
# itself bounded by what is left of the budget, which is what makes the total a
# hard maximum rather than a hopeful one. If the underlying socket cannot be
# reached to do that, the leg REFUSES rather than proceeding unbounded -- the
# impersonated leg below has a genuine total-transfer timeout of its own and takes
# over. No global socket state is touched and no thread or process is left behind.
_SOURCE_SOCKET_TIMEOUT = 10               # one blocking socket operation
_SOURCE_MAX_REDIRECTS = 3                 # urllib's own default is 10
_SOURCE_LEG_DEADLINE = 25                 # total wall clock for one urllib leg
_SOURCE_READ_CHUNK = 65536
_SOURCE_IMPERSONATED_TIMEOUT = 15         # libcurl CURLOPT_TIMEOUT_MS, total transfer

_SOURCE_MIN_USABLE_CHARS = 600            # backstop, not the primary signal

class SourceAcquisitionTimeout(Exception):
    """One acquisition leg hit its wall-clock deadline. A fetch failure like any
    other: fetch_source_article already catches Exception on both legs and falls
    through, so this reaches no caller as a raise."""


class _BoundedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """urllib follows up to 10 redirects, each a fresh request. Fewer hops means less
    surface for a hostile server, and the deadline covers all of them either way."""
    max_redirections = _SOURCE_MAX_REDIRECTS


class _DeadlineSocket:
    """A socket that cannot be read past a wall-clock deadline.

    Every read is budgeted, not merely the body reads: the response HEADERS are read
    by http.client with the same trickle-resettable timeout, and a server dripping
    bytes inside a header line stalls getresponse() before a caller ever sees a
    response object to bound. Measured: a header drip ran past a 25s body deadline
    without stopping, because the body loop had not started yet.

    Budgeting here instead means the bound holds over connect, request, headers,
    redirects and body alike -- there is no phase left that reads unbudgeted. Reads
    still go through io.BufferedReader, whose read(n) loops until it has n bytes, but
    each of those underlying reads now passes through _budget() and cannot outlive
    what is left. No global socket state is touched, and no thread or process exists
    to be left behind: the deadline is checked by the very call that would block.
    """

    def __init__(self, sock, deadline):
        self._sock = sock
        self._deadline = deadline

    def _budget(self):
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise SourceAcquisitionTimeout("acquisition deadline of %ss reached"
                                           % _SOURCE_LEG_DEADLINE)
        self._sock.settimeout(min(remaining, _SOURCE_SOCKET_TIMEOUT))

    def recv(self, *a, **kw):
        self._budget()
        return self._sock.recv(*a, **kw)

    def recv_into(self, *a, **kw):
        self._budget()
        return self._sock.recv_into(*a, **kw)

    def send(self, *a, **kw):
        self._budget()
        return self._sock.send(*a, **kw)

    def sendall(self, *a, **kw):
        self._budget()
        return self._sock.sendall(*a, **kw)

    def makefile(self, mode="rb", buffering=None, **kw):
        # SocketIO reads through THIS object, so http.client's header and body reads
        # are budgeted too. That is the whole point of the wrapper.
        #
        # The _io_refs bookkeeping is socket.makefile's, reproduced because we are
        # standing in for it: urllib closes the connection socket as soon as it has a
        # response and relies on this count to keep the descriptor alive for whoever
        # still holds the file object. Skip it and the first body read fails with
        # "Bad file descriptor" -- which it did, before this line existed.
        self._sock._io_refs += 1
        raw = socket.SocketIO(self, "rb")
        return raw if buffering == 0 else io.BufferedReader(raw)

    def __getattr__(self, name):
        return getattr(self._sock, name)


def _bounded_opener(deadline):
    """Built per call, carrying this fetch's deadline into the connection classes.
    Per-opener rather than module-level so nothing global is mutated and two
    concurrent fetches cannot inherit each other's deadline."""

    def _wrap(conn):
        conn.sock = _DeadlineSocket(conn.sock, deadline)

    class _Conn(http.client.HTTPConnection):
        def connect(self):
            super().connect()
            _wrap(self)

    class _SConn(http.client.HTTPSConnection):
        def connect(self):
            super().connect()
            _wrap(self)

    class _H(urllib.request.HTTPHandler):
        def http_open(self, req):
            return self.do_open(_Conn, req)

    class _SH(urllib.request.HTTPSHandler):
        def https_open(self, req):
            return self.do_open(_SConn, req)

    return urllib.request.build_opener(_BoundedRedirectHandler(), _H(), _SH())


def _response_socket(resp):
    """The socket under an http.client.HTTPResponse, or None if it cannot be reached.

    HTTPResponse.fp is sock.makefile("rb") -- a BufferedReader over a SocketIO that
    holds the socket. There is no public accessor, so this is defensive: a None
    return makes the caller refuse the leg rather than read without a bound, which
    is the safe direction for something reaching into a private attribute.
    """
    sock = getattr(getattr(resp, "fp", None), "raw", None)
    sock = getattr(sock, "_sock", None)
    return sock if hasattr(sock, "settimeout") else None


_SOURCE_MIN_USABLE_PARAGRAPHS = 3         # structural: an article has a body

# Interstitial / access-wall / JS-shell markers. Deliberately a short, literal
# list of things that are never article prose -- NOT a general web-content
# classifier, which the brief explicitly rules out.
_SOURCE_FAILURE_MARKERS = (
    "enable javascript", "javascript is disabled", "javascript to continue",
    "access denied", "403 forbidden", "are you a robot", "unusual traffic",
    "subscribe to continue", "subscribers only", "create an account to continue",
    "page not found", "404 not found", "service unavailable",
)

# Hard, finite budget per scheduled run: candidate 1, 2, 3. Only
# SOURCE_ACQUISITION_FAILED consumes it -- never an editorial defer or decline.
MAX_SOURCE_ACQUISITION_ATTEMPTS = 3


# Aggregator isolation (Story Rejection V1.1, 2026-08-17 -- SRF3 forensic
# audit): a link-aggregator permalink (e.g. Techmeme) resolves to a page
# listing MANY unrelated stories. trafilatura's readability extraction has no
# concept of "the one item this feed entry pointed at" -- it extracts the
# page's whole main-content block, so fetch_source_article on an aggregator
# permalink returns text spanning every neighbouring headline too. That is
# exactly how an unrelated lawsuit item sharing the same Techmeme page
# contaminated a real commission decision and contributed the finished
# article's title motif. An aggregator URL must therefore NEVER be treated as
# `fetched_article` material for ITSELF -- see fetch_source_article's
# aggregator branch below.
_AGGREGATOR_DOMAINS = {"techmeme.com", "www.techmeme.com"}


def _url_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url or "").netloc.lower()
    except Exception:
        return ""


_NAV_FUNCTION_WORDS = {
    "the", "a", "an", "of", "to", "and", "in", "is", "was", "that", "it", "for",
    "on", "with", "as", "at", "by", "from", "but", "this", "which", "are", "be",
    "been", "were", "has", "have", "had", "its", "their", "his", "her", "they",
    "we", "you", "he", "she", "not", "or", "would", "will", "said", "says",
    "more", "than", "when", "who", "what", "there",
}


def _looks_like_nav(text: str) -> bool:
    """True if a paragraph reads like nav/menu chrome rather than prose.

    Discriminator is function-word density. English prose runs ~0.26-0.42
    function words per token; concatenated nav menus ('Magazine Awards Jobs
    Events Guide Showroom...') run 0.00-0.19 however long they get, because
    they are lists of nouns with no grammar. Measured across seven live
    news/design sites the populations do not overlap: every nav blob scored
    <=0.19, every genuine article paragraph >=0.26.

    English-only signal, and it only gates the regex FALLBACK path (used
    when trafilatura is unavailable or fails) -- never the trafilatura
    primary path -- so a non-English page can't lose text to it unless
    trafilatura is also unavailable.
    """
    words = [w.strip('.,;:!?"\'()[]').lower() for w in text.split()]
    words = [w for w in words if w]
    if len(words) < 8:
        return False
    return sum(1 for w in words if w in _NAV_FUNCTION_WORDS) / len(words) < 0.20


def _extract_paragraphs_regex(html: str, max_paras: int = 12) -> str:
    """Legacy regex extraction, now nav-guarded and entity-unescaped. Fallback only."""
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)
    clean = []
    for p in paragraphs:
        text = _html_entities.unescape(re.sub(r'<[^>]+>', '', p)).strip()
        text = re.sub(r'\s+', ' ', text)
        if len(text) > 80 and not _looks_like_nav(text):
            clean.append(text)
    return "\n\n".join(clean[:max_paras])


sys.path.insert(0, str(Path(__file__).parent.parent))
import material_policy as MP                                          # noqa: E402


class DiscoveryMixin:
    def _rotation_eligible_agents(self):
        """The rotation/fairness-eligible persona SET, computed BEFORE any
        mechanism-aware decision is made (Persona Brief <-> Writer
        Reconciliation, 2026-08-16 -- see the conceptual-architecture audit's
        CA2 finding and `.claude/persona-architecture-audit.md` finding #3).

        This runs the SAME rotation rule `_balance_agent` below has always
        applied (no same persona within 3 days; no persona with 2+ articles
        in the last 4 days), against the same `article_beats` data, but
        returns the full eligible SET instead of collapsing it into one
        pick -- so a mechanism-aware caller (Fable's editorial brief) can be
        given the list of currently-permitted voices as a hard constraint UP
        FRONT, instead of freely picking any persona and having that choice
        silently overridden afterward by a second, subject-blind rotation
        check (the exact failure mode this fix closes -- see generate.py's
        Fable-brief call site). Deliberately a SEPARATE query rather than a
        refactor of `_balance_agent` sharing this method's internals: the
        two functions answer different questions (one persona in/one out,
        vs. the whole eligible set) and their "all blocked" fallback
        behavior is shaped differently enough (single min-freq pick vs. a
        full ranked list) that a shared-internals refactor risks subtly
        changing `_balance_agent`'s existing, already-relied-upon behavior
        for a routing-safety-critical function -- the query itself is cheap
        and runs at most once per generation run, so the small duplication
        is the safer trade. `_balance_agent` itself is otherwise unchanged
        and remains the right tool for the crude keyword-seeded fallback
        paths that run BEFORE any brief exists (news_seed/discovery-domain
        seeding, the generic-topic-list fallback branch) and as the sole
        fallback persona when a Fable brief is unavailable/discarded.

        Returns a non-empty list of persona names. Never returns an empty
        list -- if the strict rotation rule would block everyone, falls back
        to all personas ranked least-used-first (same "somebody has to
        write today" reasoning `_balance_agent`'s own all-blocked branch
        already used). On any DB/query failure, fails OPEN (returns every
        persona) rather than constraining Fable's choice to a broken/partial
        read -- the same fail-open spirit as `_balance_agent`'s own
        except-path (which returns `preferred` unchanged, i.e. blocks
        nothing, on error).
        """
        all_agents = list(self.agents.keys())
        if getattr(self, 'override_agent', None):
            return [self.override_agent]
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            self._init_beats_table(conn)
            cutoff4 = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")
            cutoff3 = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

            rows = conn.execute(
                "SELECT agent, COUNT(*) FROM article_beats WHERE date >= ? GROUP BY agent",
                (cutoff4,)
            ).fetchall()
            freq = {r[0]: r[1] for r in rows}

            recent = conn.execute(
                "SELECT DISTINCT agent FROM article_beats WHERE date >= ?",
                (cutoff3,)
            ).fetchall()
            conn.close()

            blocked = {r[0] for r in recent}
            for a, c in freq.items():
                if c >= 2:
                    blocked.add(a)

            candidates = [a for a in all_agents if a not in blocked]
            if not candidates:
                candidates = sorted(all_agents, key=lambda a: freq.get(a, 0))
            return candidates or all_agents

        except Exception as e:
            self.logger.debug("_rotation_eligible_agents failed: %s", e)
            return all_agents

    def _balance_agent(self, preferred: str) -> str:
        """
        Guard against agent overuse. Rules (in priority order):
          1. --agent CLI override always wins.
          2. If preferred agent ran yesterday → rotate to least-recently-used agent.
          3. If preferred agent has 2+ articles in last 4 days → rotate.
          4. Otherwise keep preferred.
        Returns final agent name.

        Persona Brief <-> Writer Reconciliation (2026-08-16): still used by
        the crude keyword-seeded persona guesses that run BEFORE a Fable
        brief exists (news_seed/discovery-domain routing, the generic
        fallback-topic branch) and as the sole fallback persona when a Fable
        brief is unavailable/discarded -- unchanged, byte-for-byte, from
        before this fix. NOT used anymore to re-check a brief's own persona
        choice after the fact -- that silent post-hoc override (Fable
        chooses persona A, this function silently substitutes B, B writes
        A's mechanism/angle unchanged) was the exact confirmed bug; see
        `_rotation_eligible_agents` above, used instead at generate.py's
        Fable-brief call site to constrain Fable's choice BEFORE it's made,
        with nothing downstream allowed to override it afterward.
        """
        if getattr(self, 'override_agent', None):
            return self.override_agent

        try:
            conn   = sqlite3.connect(str(self.discovery_db))
            self._init_beats_table(conn)
            cutoff4 = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")
            cutoff3 = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

            # Count per agent last 4 days
            rows = conn.execute(
                "SELECT agent, COUNT(*) FROM article_beats WHERE date >= ? GROUP BY agent",
                (cutoff4,)
            ).fetchall()
            freq = {r[0]: r[1] for r in rows}

            # Agents used in last 3 days — block all of them
            recent = conn.execute(
                "SELECT DISTINCT agent FROM article_beats WHERE date >= ?",
                (cutoff3,)
            ).fetchall()
            conn.close()

            all_agents = list(self.agents.keys())

            # Rule: no same persona within 3 days + no 2+ articles in 4 days
            blocked = {r[0] for r in recent}
            for a, c in freq.items():
                if c >= 2:
                    blocked.add(a)

            candidates = [a for a in all_agents if a not in blocked]
            if not candidates:
                # All blocked — pick least recently used
                candidates = sorted(all_agents, key=lambda a: freq.get(a, 0))

            if preferred not in blocked:
                return preferred

            # Prefer least-used among candidates
            chosen = min(candidates, key=lambda a: freq.get(a, 0))
            self.logger.info("Agent rebalanced: %s → %s (blocked: %s)", preferred, chosen, blocked)
            return chosen

        except Exception as e:
            self.logger.debug("_balance_agent failed: %s", e)
            return preferred

    def _check_title_freshness(self, title: str, current_agent: str = "") -> list[str]:
        """
        Check proposed title for overlap with articles from last 14 days.
        Returns list of conflict descriptions (empty = clean).

        Three checks:
        1. Signal-word overlap (any 2+ domain-specific terms)
        2. Content-word overlap (3+ shared non-stopwords)
        3. Title template collision — same structural pattern, regardless of words
           e.g. "The X Is the Argument" used twice (stricter for same agent: 1 match blocks)
        """
        stopwords = {
            'the','a','an','and','or','of','in','on','at','to','for','is','are',
            'was','were','with','this','that','from','by','as','it','its','not',
            'but','how','why','what','when','who','you','your','that','they'
        }
        signal_words = {
            'body', 'frequency', 'door', 'map', 'sound', 'space', 'design',
            'city', 'office', 'time', 'floor', 'wall', 'building', 'navigation',
            'access', 'voice', 'language', 'argument', 'route', 'schedule',
            'brain', 'silence', 'noise', 'touch', 'light', 'ramp', 'street',
            'work', 'crip', 'deaf', 'blind', 'care', 'pain', 'cost', 'rule',
        }

        def _template(t: str) -> str:
            """Replace content words with _ to extract structural pattern."""
            words = t.lower().split()
            return ' '.join('_' if w not in stopwords and len(w) > 3 else w for w in words)

        try:
            conn   = sqlite3.connect(str(self.discovery_db))
            cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
            rows   = conn.execute(
                "SELECT title, agent FROM article_beats WHERE date >= ?", (cutoff,)
            ).fetchall()
            conn.close()

            new_words    = {w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", title)
                            if w.lower() not in stopwords}
            new_template = _template(title)
            conflicts    = []

            for old_title, agent in rows:
                old_words    = {w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", old_title)
                                if w.lower() not in stopwords}
                overlap         = new_words & old_words
                signal_overlap  = overlap & signal_words
                old_template    = _template(old_title)
                same_agent      = current_agent and current_agent == agent

                # Template collision — same structural pattern
                if new_template == old_template:
                    conflicts.append(
                        f"TEMPLATE COLLISION with '{old_title}' ({agent}): identical title structure"
                    )
                    continue

                # Same-agent: stricter — 1 signal word is enough
                if same_agent and len(signal_overlap) >= 1:
                    conflicts.append(
                        f"same-agent overlap with '{old_title}' ({agent}): {signal_overlap}"
                    )
                    continue

                # General: 2+ signal words or 3+ content words
                if len(signal_overlap) >= 2 or len(overlap) >= 3:
                    conflicts.append(
                        f"overlaps with '{old_title}' ({agent}): {overlap & (old_words | signal_words)}"
                    )

            return conflicts
        except Exception as e:
            self.logger.debug("_check_title_freshness failed: %s", e)
            return []

    def check_for_existing_article_today(self):
        """Check if today's article already exists. Returns filename or None."""
        if getattr(self, 'force_run', False):
            return None
        today_str = self._today()
        # Was globbing self.posts_dir — but create_article_file() writes to
        # self.drafts_dir (_drafts/), and promotion to _posts/ happens on a separate
        # ~2-day cron cycle. A same-day article essentially never exists in _posts/
        # yet, so this guard was dead: a same-day re-run would generate a second draft.
        for file in self.drafts_dir.glob(f"{today_str}-*.md"):
            if file.is_file():
                self.logger.info(f"Skipping — already have article for today: {file.name}")
                return file.name
        return None


    def get_pool_links(self, keywords: list[str], n: int = 15) -> list[dict]:
        """Query link_pool for URLs relevant to article keywords.

        Scores by keyword overlap against title and tags columns (both text-searchable).
        Falls back to random alive URLs if no keywords match. Graceful if table missing.
        """
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            if keywords:
                # Build a relevance score: 1 point per keyword hit in title or tags
                case_parts = ' + '.join(
                    [f"(CASE WHEN lower(title) LIKE ? THEN 1 ELSE 0 END)" for _ in keywords] +
                    [f"(CASE WHEN lower(tags)  LIKE ? THEN 1 ELSE 0 END)" for _ in keywords]
                )
                params = [f'%{kw}%' for kw in keywords] * 2 + [n]
                rows = conn.execute(f"""
                    SELECT url, title, domain FROM link_pool
                    WHERE is_alive = 1
                    ORDER BY ({case_parts}) DESC, RANDOM()
                    LIMIT ?
                """, params).fetchall()
            else:
                rows = conn.execute(
                    "SELECT url, title, domain FROM link_pool WHERE is_alive = 1 ORDER BY RANDOM() LIMIT ?",
                    (n,)
                ).fetchall()
            conn.close()
            return [{"url": r[0], "title": r[1] or r[2], "domain": r[2]} for r in rows]
        except Exception:
            return []


    def _init_beats_table(self, conn):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS article_beats (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                date     TEXT NOT NULL,
                agent    TEXT NOT NULL,
                title    TEXT NOT NULL,
                beat     TEXT,
                keywords TEXT,
                shape    TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_beats_agent ON article_beats(agent, date)")
        try:
            conn.execute("ALTER TABLE article_beats ADD COLUMN shape TEXT")
        except Exception:
            pass
        conn.commit()

    def _classify_beat(self, agent: str, title: str, first_para: str) -> str:
        text   = f"{title} {first_para}".lower()
        beats  = _AGENT_BEATS.get(agent, [])
        scores = {b: sum(1 for kw in b.replace("-", " ").split() if kw in text) for b in beats}
        return max(scores, key=scores.get) if any(scores.values()) else "general"

    def _record_beat(self, agent: str, title: str, content: str):
        """Store article beat in DB after generation."""
        try:
            first_para = ""
            for line in content.splitlines():
                line = line.strip()
                if len(line) > 80 and not line.startswith("#") and not line.startswith("!"):
                    first_para = line[:300]
                    break
            beat = self._classify_beat(agent, title, first_para)
            conn = sqlite3.connect(str(self.discovery_db))
            self._init_beats_table(conn)
            shape = self._classify_shape(title, first_para)
            conn.execute(
                "INSERT INTO article_beats (date, agent, title, beat, keywords, shape) VALUES (?, ?, ?, ?, ?, ?)",
                (self._today(), agent, title, beat, "", shape)
            )
            conn.commit()
            conn.close()
            self.logger.info("Beat recorded: %s → %s", agent, beat)
        except Exception as e:
            self.logger.debug("_record_beat failed: %s", e)

    def _get_recent_dates_nudge(self) -> str:
        """Extract date anchors used in recent posts and return a nudge to avoid repeating them."""
        import glob as _glob, re as _re
        posts = sorted(_glob.glob(str(self.posts_dir / "*.md")))[-7:]
        dates_seen = []
        for p in posts:
            try:
                with open(p) as f:
                    body = f.read()
                for m in _re.findall(r'In (January|February|March|April|May|June|July|August|September|October|November|December) (20\d\d)', body):
                    label = f"{m[0]} {m[1]}"
                    if label not in dates_seen:
                        dates_seen.append(label)
            except Exception:
                continue
        if not dates_seen:
            return ""
        return (
            f"DATE VARIETY: Recent articles used these temporal anchors: {', '.join(dates_seen)}. "
            "Do not open with the same month/year combination. Pick a different date for your opening anchor.\n\n"
        )

    def _get_beat_nudge(self, agent: str) -> str:
        """Return a prompt nudge if agent hasn't covered a beat in 14+ days."""
        try:
            cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
            conn   = sqlite3.connect(str(self.discovery_db))
            self._init_beats_table(conn)
            recent = [r[0] for r in conn.execute(
                "SELECT beat FROM article_beats WHERE agent = ? AND date > ?", (agent, cutoff)
            ).fetchall()]
            # Count coverage
            all_beats = _AGENT_BEATS.get(agent, [])
            uncovered = [b for b in all_beats if b not in recent]
            overused  = [b for b in all_beats if recent.count(b) >= 3]
            conn.close()
            nudges = []
            if uncovered:
                nudges.append(f"You haven't written about {uncovered[0].replace('-', ' ')} recently — if this topic connects, explore that angle.")
            if overused:
                nudges.append(f"You've written about {overused[0].replace('-', ' ')} three times recently — find a different angle or territory.")
            return ("BEAT NOTE: " + " ".join(nudges) + "\n\n") if nudges else ""
        except Exception:
            return ""

    def _fetch_rss_news(self, persona_name: str, days: int = 14) -> list:
        """Fetch recent items from persona-specific + general RSS/Atom feeds.
        Returns list of dicts sorted newest-first. Gracefully skips dead feeds."""
        import xml.etree.ElementTree as ET
        from email.utils import parsedate_to_datetime
        import re as _re

        # _SCRIPT_DIR (from config.py, already corrected for its own one-level-deeper
        # location) resolves to automation/ — using Path(__file__).parent here directly
        # would resolve to automation/orchestrator/ instead, silently pointing at a
        # nonexistent feeds.json. The bare `except: return []` below would have
        # swallowed that with zero error logged — this pipeline would have quietly
        # stopped fetching RSS news with nothing to indicate why. Caught before this
        # method ever ran with the wrong path, via a direct behavioral test.
        feeds_path = _SCRIPT_DIR / "feeds.json"
        try:
            feeds_cfg = json.loads(feeds_path.read_text())
        except Exception:
            return []

        feeds = feeds_cfg.get(persona_name, []) + feeds_cfg.get("general", [])
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        ATOM = "http://www.w3.org/2005/Atom"
        items = []

        def _strip_html(text):
            return _re.sub(r"<[^>]+>", " ", text or "").strip()[:400]

        def _parse_dt(s):
            if not s:
                return datetime.now(timezone.utc)
            for fn in (
                lambda x: parsedate_to_datetime(x),
                lambda x: datetime.fromisoformat(x.rstrip("Z")).replace(tzinfo=timezone.utc),
                lambda x: datetime.strptime(x[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc),
            ):
                try:
                    return fn(s)
                except Exception:
                    pass
            return datetime.now(timezone.utc)

        for feed in feeds:
            url = feed.get("url", "")
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "cripminds/1.0 (+https://cripminds.com)"}
                )
                with urllib.request.urlopen(req, timeout=6) as r:
                    raw = r.read()
                root = ET.fromstring(raw)

                # RSS 2.0
                for item in root.findall(".//item"):
                    title = _strip_html(item.findtext("title", ""))
                    link  = (item.findtext("link") or "").strip()
                    desc  = _strip_html(item.findtext("description", ""))
                    dt    = _parse_dt(item.findtext("pubDate", ""))
                    if dt >= cutoff and title and link:
                        items.append({
                            "title": title, "url": link, "summary": desc,
                            "source": feed.get("name", url), "date": dt.strftime("%Y-%m-%d"),
                            "_dt": dt,
                        })

                # Atom
                ns = {"a": ATOM}
                for entry in root.findall("a:entry", ns):
                    title = _strip_html(
                        entry.findtext("a:title", "", ns) or entry.findtext("title", "")
                    )
                    link_el = (
                        entry.find(f"a:link[@rel='alternate']", ns)
                        or entry.find("a:link", ns)
                        or entry.find("link")
                    )
                    link = (link_el.get("href", "") if link_el is not None else "").strip()
                    desc = _strip_html(
                        entry.findtext("a:summary", "", ns)
                        or entry.findtext("a:content", "", ns)
                        or entry.findtext("summary", "")
                    )
                    dt = _parse_dt(
                        entry.findtext("a:updated", "", ns)
                        or entry.findtext("a:published", "", ns)
                        or entry.findtext("updated", "")
                    )
                    if dt >= cutoff and title and link:
                        items.append({
                            "title": title, "url": link, "summary": desc,
                            "source": feed.get("name", url), "date": dt.strftime("%Y-%m-%d"),
                            "_dt": dt,
                        })

            except Exception as e:
                self.logger.debug("RSS feed skipped (%s): %s", url, e)

        items.sort(key=lambda x: x["_dt"], reverse=True)
        self.logger.info("RSS: %d items from last %d days across %d feeds", len(items), days, len(feeds))
        return items

    def _pick_news_item(self, items: list, focus_keywords: list) -> dict | None:
        """Score news items against persona focus keywords.
        80% → highest scorer. 20% → random from top-5 (blackbox surprise)."""
        if not items:
            return None
        scored = []
        for item in items:
            text  = f"{item['title']} {item['summary']}".lower()
            score = sum(1 for kw in focus_keywords if kw.lower() in text)
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)

        # 20% chance: pick any of the top-5 regardless of score (surprise factor)
        if random.random() < 0.20:
            pool = [x[1] for x in scored[:5]]
            chosen = random.choice(pool)
            self.logger.info("RSS blackbox pick: '%s' (score ignored)", chosen["title"][:60])
            return chosen

        best_score, best_item = scored[0]
        if best_score >= 1:
            self.logger.info("RSS matched: '%s' (score %d)", best_item["title"][:60], best_score)
            return best_item

        # No keyword match at all — still use the most recent item (full surprise)
        if items:
            self.logger.info("RSS no-match fallback: '%s'", items[0]["title"][:60])
            return items[0]
        return None

    def _get_overused_themes(self, days: int = 7) -> set:
        """Return set of theme names that appear >=2 times in last N days of published posts."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        counts = {theme: 0 for theme in _THEME_CLUSTERS}
        try:
            for post_file in sorted(self.posts_dir.glob("*.md"), reverse=True):
                if post_file.stem[:10] < cutoff:
                    break
                # Only scan frontmatter + first 300 chars to avoid false positives in body
                text = post_file.read_text(errors="ignore")[:800].lower()
                for theme, keywords in _THEME_CLUSTERS.items():
                    if any(kw in text for kw in keywords):
                        counts[theme] += 1
        except Exception as e:
            self.logger.debug("_get_overused_themes failed: %s", e)
        overused = {theme for theme, count in counts.items() if count >= 2}
        if overused:
            self.logger.info("Overused themes (last %d days): %s", days, overused)
        return overused

    def _get_recent_references(self, days: int = 14) -> list:
        """Scan recent posts (live + recently deleted) for named references.
        Returns list of names used in the last N days — to be excluded from new articles."""
        import subprocess
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        seen = set()

        def _extract_refs(text):
            for m in re.finditer(r'\[([A-Z][^\]]{3,40})\]\(http', text):
                name = m.group(1).strip()
                if len(name.split()) <= 4:
                    seen.add(name)

        # 1. Live posts still on disk
        try:
            for post_file in sorted(self.posts_dir.glob("*.md"), reverse=True):
                if post_file.stem[:10] < cutoff:
                    break
                _extract_refs(post_file.read_text(errors="ignore"))
        except Exception as e:
            self.logger.debug("_get_recent_references (live) failed: %s", e)

        # 2. Recently deleted posts (retracted articles) — scan git history
        try:
            result = subprocess.run(
                ["git", "log", "--diff-filter=D", "--name-only", "--pretty=format:%H %ai",
                 f"--since={days} days ago", "--", "_posts/*.md"],
                cwd=str(self.repo_root), capture_output=True, text=True, timeout=10
            )
            commit_hash = None
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("_posts/"):
                    # line is a deleted file path — retrieve content from parent commit
                    if commit_hash:
                        show = subprocess.run(
                            ["git", "show", f"{commit_hash}^:{line}"],
                            cwd=str(self.repo_root), capture_output=True, text=True, timeout=5
                        )
                        if show.returncode == 0:
                            _extract_refs(show.stdout)
                else:
                    # line is "<hash> <date>" — extract hash
                    commit_hash = line.split()[0] if line else None
        except Exception as e:
            self.logger.debug("_get_recent_references (deleted) failed: %s", e)

        refs = sorted(seen)
        if refs:
            self.logger.info("Recently used references (last %d days, incl. retracted): %s", days, refs)
        return refs

    def _classify_shape(self, title: str, first_para: str) -> str:
        text = (title + " " + first_para).lower()
        scores = {shape: sum(1 for kw in kws if kw in text)
                  for shape, kws in _STRUCTURAL_SHAPES.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "general"

    def _get_shape_nudge(self) -> str:
        """Nudge away from overused shapes; suggest absent ones (especially historical-anchor)."""
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            self._init_beats_table(conn)
            rows = conn.execute(
                "SELECT shape FROM article_beats WHERE shape IS NOT NULL AND shape != 'general' ORDER BY date DESC LIMIT 10"
            ).fetchall()
            conn.close()
            shapes = [r[0] for r in rows]
            if not shapes:
                return ""
            nudges = []
            # Warn if last 3 share the same shape
            if len(shapes) >= 3 and len(set(shapes[:3])) == 1:
                label = shapes[0].replace("-", " ")
                nudges.append("The last three articles all used the " + label + " structure. Find a different argumentative entry point.")
            # Suggest historical-anchor if absent from last 10 articles
            if "historical-anchor" not in shapes:
                nudges.append(
                    "No recent article has anchored its argument in a specific historical event. "
                    "Consider: a specific date, a court case, a protest, a piece of legislation, "
                    "a building that was built or torn down — and show how the same dynamic repeats today."
                )
            if "comparative-case" not in shapes:
                nudges.append(
                    "COMPARATIVE CASE — worth considering (it has been absent from every recent piece): "
                    "two parallel situations — person A and person B, system X and system Y, before and after — "
                    "run side by side with no commentary, the reader drawing the contrast themselves. "
                    "Only use it if the material actually contains two comparable cases you found. "
                    "Do not manufacture a second case to satisfy the shape; a forced pairing is worse than none."
                )
            if nudges:
                return "SHAPE NOTE: " + " ".join(nudges) + "\n\n"
        except Exception:
            pass
        return ""

    def _get_scholar_nudge(self) -> str:
        """Scan last 7 articles for overused scholar citations. Nudge away from wallpaper repetition."""
        _WATCHED = ['Mike Oliver', 'Sunaura Taylor', 'Gregory Bateson', 'Rebecca Solnit']
        try:
            cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            recent_posts = sorted(self.posts_dir.glob("*.md"), reverse=True)[:7]
            counts = {s: 0 for s in _WATCHED}
            for post in recent_posts:
                try:
                    text = post.read_text(encoding='utf-8')
                    for scholar in _WATCHED:
                        if scholar.split()[-1] in text:  # match on last name
                            counts[scholar] += 1
                except Exception:
                    continue
            nudges = []
            for scholar, count in counts.items():
                if count >= 3:
                    nudges.append(
                        f"{scholar} has appeared in {count} of the last 7 articles. "
                        f"Do not cite or explain {scholar.split()[0]} again unless your argument "
                        f"specifically requires it and cannot be made without them. "
                        f"Find a different theoretical anchor."
                    )
                elif count >= 2:
                    nudges.append(
                        f"{scholar} has appeared in {count} recent articles. "
                        f"If you cite them, do not re-explain their core concept — assume the reader knows it."
                    )
            return ("SCHOLAR NOTE: " + " ".join(nudges) + "\n\n") if nudges else ""
        except Exception:
            return ""

    # Calendar events for brief injection (#8 — time + event injection)
    _CALENDAR_EVENTS = [
        (1,  4,  7,  "World Braille Day"),
        (2, 28,  7,  "Rare Disease Day"),
        (3,  3,  5,  "World Hearing Day"),
        (3, 21,  5,  "World Down Syndrome Day"),
        (4,  2,  7,  "World Autism Day / start of Autism Acceptance Month"),
        (4,  7,  5,  "World Health Day"),
        (4, 27,  3,  "King's Day (Netherlands)"),
        (5, 21,  7,  "Global Accessibility Awareness Day (GAAD, 3rd Thursday of May — approximate)"),
        (6, 14,  5,  "Deafblind Awareness Week"),
        (6, 28,  5,  "Pride Month peak / Stonewall anniversary"),
        (7, 26,  7,  "ADA Anniversary"),
        (8,  1, 31,  "Disability Pride Month"),
        (9, 23,  7,  "International Day of Sign Languages"),
        (9, 25,  7,  "Deaf Awareness Week (UK/International)"),
        (10,15,  5,  "White Cane Safety Day"),
        (11, 1, 30,  "Disability History Month (UK)"),
        (12, 3,  7,  "International Day of Persons with Disabilities"),
    ]

    def _get_calendar_event_nudge(self) -> str:
        """Return a nudge if today is within window of a disability/cultural calendar event."""
        try:
            today = datetime.now()
            for month, day, window, label in self._CALENDAR_EVENTS:
                try:
                    event_date = datetime(today.year, month, day)
                except ValueError:
                    continue
                delta = (today - event_date).days
                if -window <= delta <= window:
                    return (
                        f"CALENDAR NOTE: {label} falls this week (or very recently — within {window} days). "
                        f"Personas experience the same calendar the reader lives in. "
                        f"If your angle connects to this moment, anchor the piece here. "
                        f"If it does not connect at all, ignore this note.\n\n"
                    )
        except Exception:
            pass
        return ""

    def _get_claims_nudge(self, agent_name: str) -> str:
        """Inject the persona's active falsifiable claims — flags for return post if news contradicts one."""
        try:
            state = self._load_persona_state(agent_name)
            claims = state.get("claims_on_record", [])
            if not claims:
                return ""
            claim_lines = "\n".join(
                f"  - \"{c.get('claim', '')}\" (article: {c.get('article', '?')}, {c.get('date', '?')})"
                for c in claims[-5:]
            )
            return (
                f"YOUR CLAIMS ON RECORD: You have made these falsifiable claims in recent articles:\n"
                f"{claim_lines}\n"
                f"If today's news or source material directly contradicts or confirms one, "
                f"that IS the article — a return post updating your position with new evidence. "
                f"Name the claim, name what changed, update your position explicitly. "
                f"If nothing contradicts or confirms, treat this as background context only.\n\n"
            )
        except Exception:
            return ""

    # Theorists watched for citation frequency (14-day window)
    _CITATION_WATCHED = [
        'Henri Lefebvre', 'Gregory Bateson', 'Mike Oliver', 'Nick Walker',
        'Georgina Kleege', 'Christine Sun Kim', 'Sunaura Taylor', 'Rebecca Solnit',
        'Alison Kafer', 'Robert McRuer', 'Rosemarie Garland-Thomson',
    ]

    def _init_citation_ledger(self, conn):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS citation_ledger (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                date          TEXT NOT NULL,
                agent         TEXT NOT NULL,
                theorist      TEXT NOT NULL,
                article_title TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_citation_date ON citation_ledger(date)")
        conn.commit()

    def _get_blocked_theorists(self, days: int = 14) -> list[str]:
        """Return theorists that have appeared ≥2× in the last N days."""
        try:
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            conn = sqlite3.connect(str(self.discovery_db))
            self._init_citation_ledger(conn)
            rows = conn.execute("""
                SELECT theorist, COUNT(*) as cnt FROM citation_ledger
                WHERE date >= ? GROUP BY theorist HAVING cnt >= 2
            """, (cutoff,)).fetchall()
            conn.close()
            blocked = [r[0] for r in rows]
            if blocked:
                self.logger.info("Blocked theorists (14d ≥2×): %s", blocked)
            return blocked
        except Exception as e:
            self.logger.debug("_get_blocked_theorists failed: %s", e)
            return []

    def _record_cited_theorists(self, agent: str, article_title: str, content: str):
        """Extract and record theorist citations from generated content."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(str(self.discovery_db))
            self._init_citation_ledger(conn)
            for theorist in self._CITATION_WATCHED:
                last_name = theorist.split()[-1]
                if last_name in content:
                    conn.execute(
                        "INSERT INTO citation_ledger (date, agent, theorist, article_title) VALUES (?, ?, ?, ?)",
                        (today, agent, theorist, article_title)
                    )
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.debug("_record_cited_theorists failed: %s", e)

    def _get_recent_title_patterns(self, n: int = 10) -> str:
        """Return a compact list of recent title structures to avoid."""
        try:
            recent = sorted(self.posts_dir.glob("*.md"), reverse=True)[:n]
            titles = []
            for p in recent:
                for line in p.read_text(errors="ignore").splitlines():
                    if line.startswith("title:"):
                        t = line[6:].strip().strip('"\'')
                        if t:
                            titles.append(t)
                        break
            return "; ".join(titles[:8]) if titles else ""
        except Exception:
            return ""

    def _get_recent_openings(self, n: int = 5) -> str:
        """Return the opening sentences of the last n posts, so the brief can vary from them.

        Repetition of opening SHAPE across consecutive pieces is invisible from inside
        any single article — it only shows up reading them back to back. Fable can see
        the template if we show it the actual sentences.
        """
        try:
            recent = sorted(self.posts_dir.glob("*.md"), reverse=True)[:n]
            openings = []
            for path in recent:
                text = path.read_text(errors="ignore")
                in_body = False
                fm_count = 0
                for line in text.splitlines():
                    if line.strip() == "---":
                        fm_count += 1
                        if fm_count == 2:
                            in_body = True
                        continue
                    s = line.strip()
                    if in_body and len(s) > 80 and not s.startswith(("!", "<", "#", "*", "-")):
                        first = re.split(r"(?<=[.!?])\s", s)[0]
                        openings.append(first[:160])
                        break
            return "\n".join(f"  - {o}" for o in openings) if openings else ""
        except Exception:
            return ""

    def _should_cross_reference(self) -> bool:
        return random.random() < 0.20

    def _read_first_paragraph(self, title: str, date: str) -> str:
        """Read first body paragraph from a published post by title/date."""
        try:
            candidates = list(self.posts_dir.glob(f"{date}-*.md"))
            if not candidates:
                candidates = list(self.posts_dir.glob("*.md"))
            for path in sorted(candidates, reverse=True)[:20]:
                text = path.read_text()
                in_body = False
                fm_count = 0
                for line in text.splitlines():
                    if line.strip() == "---":
                        fm_count += 1
                        if fm_count == 2:
                            in_body = True
                        continue
                    if in_body and len(line.strip()) > 80 and not line.startswith("!"):
                        return line.strip()[:300]
        except Exception:
            pass
        return ""

    def _get_cross_reference(self, current_agent: str) -> dict | None:
        """Get a recent article by a different agent to respond to (20% of runs)."""
        if not self._should_cross_reference():
            return None
        try:
            cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            conn   = sqlite3.connect(str(self.discovery_db))
            self._init_beats_table(conn)
            rows = conn.execute("""
                SELECT agent, title, date FROM article_beats
                WHERE agent != ? AND date > ?
                ORDER BY date DESC LIMIT 5
            """, (current_agent, cutoff)).fetchall()
            conn.close()
            if not rows:
                return None
            pick       = random.choice(rows)
            first_para = self._read_first_paragraph(pick[1], pick[2])
            if not first_para:
                return None
            conflict_vector = _PERSONA_CONFLICTS.get((current_agent, pick[0]), "")
            return {"agent": pick[0], "title": pick[1], "first_paragraph": first_para,
                    "conflict_vector": conflict_vector}
        except Exception:
            return None

    def get_discovery_from_database(self):
        """Get the best unused discovery from database."""
        if not self.discovery_db.exists():
            self.logger.warning("Discovery database not found")
            return None
        
        conn = None
        try:
            conn = sqlite3.connect(self.discovery_db)
            cursor = conn.cursor()
            
            # Get best unused discovery from last 7 days
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("""
                SELECT id, angle, title, domain, url, content_snippet
                FROM findings
                WHERE used_for_article = 0
                AND discovered_date > ?
                AND (angle IS NOT NULL AND angle != '' AND angle NOT LIKE 'NONE%')
                ORDER BY confidence DESC
                LIMIT 1
            """, (week_ago,))

            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'angle': result[1],
                    'original_title': result[2],
                    'domain': result[3],
                    'url': result[4],
                    'summary': result[5]
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Database query failed: {e}")
            return None
        finally:
            if conn:
                conn.close()




    def _pick_register(self):
        """Weighted random tone register selection."""
        names   = [r[0] for r in _REGISTERS]
        weights = [r[1] for r in _REGISTERS]
        prompts = {r[0]: r[2] for r in _REGISTERS}
        chosen  = random.choices(names, weights=weights, k=1)[0]
        return chosen, prompts[chosen]

    def _pick_length(self):
        """Weighted random target word count."""
        lengths = [l[0] for l in _LENGTHS]
        weights = [l[1] for l in _LENGTHS]
        return random.choices(lengths, weights=weights, k=1)[0]

    def _pick_article_type(self):
        """Weighted random article form/mode selection."""
        names   = [t[0] for t in _ARTICLE_TYPES]
        weights = [t[1] for t in _ARTICLE_TYPES]
        prompts = {t[0]: t[2] for t in _ARTICLE_TYPES}
        chosen  = random.choices(names, weights=weights, k=1)[0]
        return chosen, prompts[chosen]

    def _extract_paragraphs(self, html: str) -> str:
        """Extract main article body text from arbitrary site HTML.

        Primary: trafilatura, which scores the DOM readability-style and
        strips nav/menu/footer/cookie/related-article chrome generically
        rather than per-site. Added 2026-08-10 after live-testing the old
        regex-only approach against 7 real sites (Dezeen, NPR, BBC, WIRED,
        designboom, Ars Technica, The Conversation): it led with a nav/menu
        junk paragraph on 7/7, eating 22-46% of the output budget every
        time -- not a Dezeen-specific edge case. trafilatura produced clean
        article text on all 7; readability-lxml/boilerpy3/jusText/a
        hand-rolled bs4 link-density scorer all leaked chrome or picked the
        wrong DOM container on at least one site.

        Falls back to the regex scan (now nav-guarded, see
        _extract_paragraphs_regex) when trafilatura is absent or returns
        nothing usable, so extraction never hard-depends on the library.
        Returns clean paragraph text; a short/empty return remains the
        existing signal for fetch_source_article() to fall back to the
        stored RSS summary.
        """
        text = ""
        if _trafilatura is not None:
            try:
                text = _trafilatura.extract(
                    html,
                    include_comments=False,
                    include_tables=False,
                    include_images=False,
                    favor_precision=False,  # True cut a real article to 469 chars in testing
                    no_fallback=False,
                ) or ""
            except Exception:
                text = ""
            text = re.sub(r'\n{3,}', '\n\n', text).strip()

        if len(text) < 200:
            legacy = _extract_paragraphs_regex(html)
            if len(legacy) > len(text):
                text = legacy
        return text

    def _fetch_url_html(self, url: str) -> str | None:
        """Plain urllib GET under a hard wall-clock deadline. Returns decoded HTML or
        None (bad status/content-type). Raises on timeout, like any other fetch failure.

        See ACQUISITION_HARD_BOUND_V1 above for why the deadline exists and why it is
        enforced per read rather than merely checked between reads: a check between
        reads is useless if the read it is about to make can block past the deadline
        on its own.
        """
        deadline = time.monotonic() + _SOURCE_LEG_DEADLINE
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        # A private opener, so bounding redirects does not mutate urllib's global
        # default for every other caller in the process.
        with _bounded_opener(deadline).open(req, timeout=_SOURCE_SOCKET_TIMEOUT) as resp:
            if resp.status != 200:
                return None
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None
            # This 500K cap is a memory/DoS safety bound on raw HTML scanned, NOT
            # the output size (max_chars already governs that, below). It used to
            # be 60K, which silently broke real-world pages with heavy pre-content
            # markup: confirmed live 2026-08-08 that theconversation.com's actual
            # article text (the tetraplegic-man-in-a-police-station paragraph, the
            # Oamaru flooding story) starts at character ~101,000 -- entirely past
            # the old 60K cutoff. That fetch call was silently returning None for
            # the WHOLE generation this bug shipped from, meaning the model had no
            # SOURCE MATERIAL block to draw from and invented a person and a quote
            # to fill the gap instead. Root cause of that fabrication incident, not
            # a downstream symptom of it.
            chunks, size = [], 0
            while size < 500000:
                try:
                    # read1, not read: read(n) is a BufferedReader loop that keeps
                    # calling recv until it has n bytes. Both are budgeted by
                    # _DeadlineSocket, but read1 returns control here, so the 500K cap
                    # is honoured chunk by chunk instead of in one enormous request.
                    chunk = resp.read1(min(_SOURCE_READ_CHUNK, 500000 - size))
                except (TimeoutError, socket.timeout) as e:
                    raise SourceAcquisitionTimeout(
                        "read stalled after %d bytes: %s" % (size, e)) from e
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
            return b"".join(chunks).decode("utf-8", errors="replace")

    def _fetch_url_html_impersonated(self, url: str) -> str | None:
        """curl_cffi GET impersonating a real browser's TLS fingerprint.

        Added 2026-08-10: plain urllib/curl get HTTP 403 from sites like
        Dezeen not because of UA-string sniffing but because their TLS
        ClientHello (JA3 fingerprint) doesn't match a real browser --
        confirmed live: stock curl on the trident host got a 403 on
        dezeen.com, but curl_cffi impersonating chrome124/safari17_0/
        firefox133 got a clean 200 with the full article on the same URL.
        chrome110's fingerprint specifically stays blocked -- excluded below.
        Never the sole path: falls through to fallback_text like the
        urllib attempt if this also fails or curl_cffi isn't installed."""
        if _curl_cffi_requests is None:
            return None
        r = _curl_cffi_requests.get(url, impersonate="chrome124",
                                    timeout=_SOURCE_IMPERSONATED_TIMEOUT)
        if r.status_code != 200:
            return None
        content_type = r.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return None
        return r.text[:500000]

    def fetch_source_article(self, url: str, max_chars: int = _SOURCE_TEXT_CACHE_MAX_CHARS,
                              fallback_text: str = None, underlying_url: str = None) -> str | None:
        """Fetch and extract text from source article URL. Never blocks generation.

        fallback_text, added 2026-08-10: this fetches the live rendered
        webpage directly, which some sites actively block. That's a
        different, blockable route from how the item was originally
        collected -- news_fetcher.py reads the site's own RSS feed (built
        for automated consumption, essentially never blocked), storing a
        real but short (~500 char) summary. If the caller has that summary
        in scope (news_seed["summary"] / a news_seeds row), pass it here:
        real-but-short material beats no material, and this is the exact
        gap a prior fabrication incident came from -- the model inventing
        a person/quote to fill a missing SOURCE MATERIAL block.

        self._last_fetch_origin (Phase 1.6, .claude/phase-1.6-source-
        grounding.md continuation): set as a side channel on every return
        path below to one of "fetched_article" / "fallback_summary" /
        "none" -- get_source_text caches this per-url so a fallback-to-
        summary result can later be told apart from a genuine fetch. Found
        on review: this function's plain str|None return type makes those
        two cases INDISTINGUISHABLE to any caller once returned -- and a
        caller building an evidence_packet from the result (generate.py)
        must not silently grant the same source-snapshot authority to the
        ~400-char RSS summary (real, but the exact same unvetted text
        already shown separately as plain "Summary:" context) that it
        grants to a genuinely fetched ~3000-char article. See
        get_source_origin's docstring for how a caller should act on this.

        underlying_url (V1.1 aggregator isolation, 2026-08-17): only consulted
        when `url` itself is on an aggregator domain (see _AGGREGATOR_DOMAINS).
        An aggregator permalink is NEVER fetched/extracted as a whole page for
        itself -- either the real underlying article (this parameter, when
        news_fetcher.py's feed parser managed to recover one) is fetched
        instead, or this falls back to `fallback_text` only (the single
        per-item RSS blurb the caller already has, never the aggregator page)."""
        if _url_domain(url) in _AGGREGATOR_DOMAINS:
            if underlying_url and _url_domain(underlying_url) not in _AGGREGATOR_DOMAINS:
                self.logger.info(
                    "fetch_source_article: %s is an aggregator permalink -- "
                    "fetching underlying article %s instead", url, underlying_url,
                )
                return self.fetch_source_article(
                    underlying_url, max_chars=max_chars, fallback_text=fallback_text,
                )
            self.logger.info(
                "fetch_source_article: %s is an aggregator permalink with no underlying "
                "article URL captured -- using the isolated per-item summary only, "
                "never the full aggregator page", url,
            )
            self._last_fetch_origin = "fallback_summary" if fallback_text else "none"
            self._last_fetch_original_length = len(fallback_text) if fallback_text else None
            return fallback_text[:max_chars] if fallback_text else None

        if not url or not url.startswith("http"):
            self._last_fetch_origin = "fallback_summary" if fallback_text else "none"
            self._last_fetch_original_length = len(fallback_text) if fallback_text else None
            return fallback_text[:max_chars] if fallback_text else None

        html, impersonated_tried = None, False
        try:
            html = self._fetch_url_html(url)
        except Exception as e:
            self.logger.debug("fetch_source_article: urllib attempt failed for %s: %s", url, e)

        if html is None:
            impersonated_tried = True
            try:
                html = self._fetch_url_html_impersonated(url)
                if html is not None:
                    self.logger.info("fetch_source_article: urllib blocked, curl_cffi impersonation succeeded for %s", url)
            except Exception as e:
                self.logger.debug("fetch_source_article: curl_cffi attempt failed for %s: %s", url, e)

        # REPRESENTATION_AWARE_FALLBACK_V1 (2026-08-29).
        #
        # The impersonation leg above only ran because the transport FAILED. But the
        # thing it exists to defeat does not fail the transport: a site that dislikes
        # our TLS fingerprint answers 200 with a JavaScript shell, which is a perfectly
        # successful HTTP request carrying no article. Verified live on lemonde.fr:
        # urllib got 200 and 3,036 bytes of shell, so the fallback was never reached,
        # while curl_cffi on the same URL returned the real 247KB article that
        # classifies USABLE. The fallback was gated on the wrong question and had been
        # dead code for exactly the sites it was written for.
        #
        # So ask the question that matters -- did we obtain a usable ARTICLE? -- using
        # classify_source_acquisition, the acquisition classifier that already owns
        # that definition. This is about representation only. A short, promotional or
        # roundup article is a usable representation and is never refetched: whether
        # material is any good is a different question, asked elsewhere, by something
        # else.
        text = self._extract_paragraphs(html) if html else ""
        if html is not None and not impersonated_tried and not self._is_usable_article(text):
            try:
                alt = self._fetch_url_html_impersonated(url)
            except Exception as e:
                alt = None
                self.logger.debug("fetch_source_article: curl_cffi attempt failed for %s: %s", url, e)
            if alt is not None:
                alt_text = self._extract_paragraphs(alt)
                if self._is_usable_article(alt_text):
                    self.logger.info(
                        "fetch_source_article: urllib returned a 200 with no usable "
                        "article (%d chars extracted), curl_cffi impersonation "
                        "recovered one (%d chars) for %s",
                        len(text or ""), len(alt_text), url)
                    html, text = alt, alt_text

        if html is None:
            if fallback_text:
                self.logger.info(
                    "fetch_source_article: using the RSS summary already on "
                    "file instead (%d chars) for %s", len(fallback_text), url,
                )
                self._last_fetch_origin = "fallback_summary"
                self._last_fetch_original_length = len(fallback_text)
                return fallback_text[:max_chars]
            self._last_fetch_origin = "none"
            self._last_fetch_original_length = None
            self._last_fetch_paragraph_count = 0
            return None

        if not text or len(text) < 200:
            self.logger.warning(
                "fetch_source_article: extracted %s chars (<200) from %s -- "
                "generation/repair will proceed without real source material",
                len(text) if text else 0, url
            )
            self._last_fetch_origin = "fallback_summary" if fallback_text else "none"
            self._last_fetch_original_length = len(fallback_text) if fallback_text else None
            self._last_fetch_paragraph_count = 0
            return fallback_text[:max_chars] if fallback_text else None
        self.logger.info("fetch_source_article: extracted %d chars from %s", len(text), url)
        self._last_fetch_origin = "fetched_article"
        # Side channel (SOURCE_ACQUISITION_RETRY_V1): how many real body
        # paragraphs the extractor kept. _extract_paragraphs already drops nav
        # chrome and anything under 80 chars, so this counts article body, not
        # markup. It is the structural signal that separates a JS/paywall shell
        # from a genuinely short article, which a character count alone cannot do.
        #
        # Counts NON-EMPTY LINES, not blank-line-separated blocks (regression fix,
        # 2026-08-24). The primary extractor is trafilatura, which separates
        # paragraphs with a SINGLE newline; counting "\n\n" blocks therefore
        # collapsed every real article to 1 and made the gate reject genuine
        # content -- the 2026-08-24 run refused three real articles of 6419, 5758
        # and 7713 chars. Non-empty lines is correct for BOTH extractors: single-
        # newline trafilatura output, and the "\n\n"-joined legacy regex
        # fallback, whose blank lines simply do not count.
        self._last_fetch_paragraph_count = len([ln for ln in text.splitlines() if ln.strip()])
        # Side channel (source-truncation closure, 2026-08-14 follow-up),
        # same pattern as self._last_fetch_origin: `text` here is the TRUE,
        # unsliced extraction -- the only place in this pipeline it still
        # exists, since the return value below is the (possibly capped)
        # slice actually stored/cached/hashed downstream. Recording its real
        # length is cheap and turns build_evidence_packet's own
        # source_original_length_chars field from an always-None promise
        # into a real, honest number wherever a caller threads it through
        # (see get_source_original_length below and generate.py's call site)
        # -- this is observability only, NOT full-text preservation: the
        # text itself is still discarded past max_chars, only its true
        # length survives.
        self._last_fetch_original_length = len(text)
        return text[:max_chars]

    def get_source_text(self, url: str, max_chars: int = _SOURCE_TEXT_CACHE_MAX_CHARS,
                         fallback_text: str = None, underlying_url: str = None) -> str | None:
        """Per-run memoized wrapper around fetch_source_article.

        Added 2026-08-10: generation (generate.py) and the fact-check repair
        pass (fact_check.py's _attempt_fabrication_repair) both fetch the same
        source_url, independently, within a single locked orchestrator run
        (production_orchestrator.py's fcntl lock covers generate -> review/
        fact-check -> publish in one process) -- confirmed live these are the
        same process, so an instance-level cache is sufficient and needs no
        cleanup: it lives exactly as long as the run that populates it, and
        dies with the process. Before this, the two fetches could disagree --
        a good scrape at generation time and a blocked one an hour later at
        repair time (or vice versa), handing the repair pass LESS material
        than the draft it's fixing was grounded in.

        Also caches source_origin per-url (Phase 1.6) alongside the text
        itself -- see get_source_origin's docstring. The two caches are
        initialized INDEPENDENTLY (found on review) rather than both inside
        one `if not hasattr(self, "_source_text_cache")` guard -- an
        instance that already has _source_text_cache set (e.g. test/probe
        setup predating this Phase 1.6 addition, or any future code path
        that only initializes the older cache) would otherwise skip
        creating _source_origin_cache entirely and hit an AttributeError
        the first time get_source_origin ran.

        underlying_url (V1.1 aggregator isolation): forwarded to
        fetch_source_article unchanged -- see that method's docstring.
        """
        if not hasattr(self, "_source_text_cache"):
            self._source_text_cache = {}
        if not hasattr(self, "_source_origin_cache"):
            self._source_origin_cache = {}
        if not hasattr(self, "_source_original_length_cache"):
            self._source_original_length_cache = {}
        if not hasattr(self, "_source_paragraph_count_cache"):
            self._source_paragraph_count_cache = {}
        if url not in self._source_text_cache:
            self._source_text_cache[url] = self.fetch_source_article(
                url, max_chars=_SOURCE_TEXT_CACHE_MAX_CHARS, fallback_text=fallback_text,
                underlying_url=underlying_url,
            )
            self._source_origin_cache[url] = getattr(self, "_last_fetch_origin", "none")
            self._source_original_length_cache[url] = getattr(self, "_last_fetch_original_length", None)
            self._source_paragraph_count_cache[url] = getattr(self, "_last_fetch_paragraph_count", None)
        cached = self._source_text_cache[url]
        return cached[:max_chars] if cached else cached

    def get_source_original_length(self, url: str):
        """Source-truncation closure follow-up (2026-08-14): returns the TRUE
        length of the text fetch_source_article extracted for this url
        BEFORE any max_chars slice was applied -- the one number that
        survives past the point where the fuller text itself is discarded
        (see fetch_source_article's own side-channel comment). None if
        get_source_text was never called for this url this run, or if
        nothing was ever fetched (fallback/none origin with no fallback_text).

        A caller building an evidence_packet should thread this into
        build_evidence_packet's source_original_length_chars parameter --
        turns that field from an always-None promise (see its own docstring:
        "not recoverable at this call site") into a real, honest number
        wherever this accessor's result is available, so a future truncation
        is disclosed, not silently invisible. See generate.py's call site."""
        return getattr(self, "_source_original_length_cache", {}).get(url)

    def get_source_origin(self, url: str):
        """Phase 1.6 (.claude/phase-1.6-source-grounding.md continuation):
        returns the provenance of get_source_text(url)'s cached result --
        "fetched_article" (a real HTML fetch + extraction succeeded),
        "fallback_summary" (the fetch failed/was blocked/extracted too
        little; the RSS summary fallback_text was returned instead), "none"
        (nothing was available either way), or None if get_source_text was
        never called for this url this run.

        WHY THIS EXISTS: fetch_source_article/get_source_text both return a
        plain string either way, so a fallback-to-summary result was
        previously INDISTINGUISHABLE from a genuinely fetched article once
        it became `source_text` in generate.py -- and Phase 1.6's evidence
        packet/validator machinery would have certified that short, unvetted
        RSS summary as if it were the full source snapshot, quietly
        reopening the exact short-summary-as-authority problem the rest of
        Phase 1.6 was built to close. A caller building an evidence_packet
        from get_source_text's result should check this and, on
        "fallback_summary", decline to grant it source-snapshot authority
        (pass None to build_evidence_packet instead) -- the summary is
        already shown to the planner separately as plain "Summary:" context,
        so treating it as source_text too would add no real material, only
        false authority. See generate.py's call sites."""
        return getattr(self, "_source_origin_cache", {}).get(url)

    def mark_finding_as_used(self, finding_id):
        """Mark a finding as used so it won't be picked again."""
        if not self.discovery_db.exists():
            return
        conn = None
        try:
            conn = sqlite3.connect(self.discovery_db)
            conn.execute(
                "UPDATE findings SET used_for_article = 1, processed_date = ? WHERE id = ?",
                (datetime.now().isoformat(), finding_id)
            )
            conn.commit()
            self.logger.info("Marked finding %s as used", finding_id)
        except Exception as e:
            self.logger.warning("Could not mark finding as used: %s", e)
        finally:
            if conn:
                conn.close()

    # ── news_seeds helpers ─────────────────────────────────────────────────────

    def _init_news_seeds_table(self, conn):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS news_seeds (
                id               TEXT PRIMARY KEY,
                url              TEXT NOT NULL UNIQUE,
                title            TEXT NOT NULL,
                summary          TEXT,
                source_name      TEXT NOT NULL,
                source_tier      INTEGER DEFAULT 2,
                pub_date         TEXT,
                fetched_date     TEXT NOT NULL,
                relevance_score  REAL DEFAULT 0.0,
                themes           TEXT,
                disability_angle TEXT,
                used             INTEGER DEFAULT 0,
                used_date        TEXT,
                declined         INTEGER DEFAULT 0,
                declined_date    TEXT,
                decline_json     TEXT,
                decline_schema_version TEXT,
                declined_source_hash  TEXT,
                underlying_article_url TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ns_score ON news_seeds(relevance_score)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ns_used  ON news_seeds(used)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ns_pub   ON news_seeds(pub_date)")
        conn.commit()

    def _ensure_decline_columns(self, conn):
        """Story Rejection V1/V1.1 (DSR2): additive, idempotent migration of
        the decline + source-lineage columns. Mirrors the angle_checked ALTER
        precedent in news_fetcher.init_db (try/except OperationalError) so
        pre-existing production DBs gain the columns without a destructive
        migration, and fresh DBs have them via the CREATE above. Safe to call
        repeatedly. underlying_article_url (V1.1, aggregator isolation) is not
        itself a decline field -- kept in this same idempotent-ALTER loop
        rather than a second near-identical method, since both are "extra
        additive columns on this table" migrations of the same shape -- the
        source_unusable trio (2026-08-23 source-retry) is carried here for the
        same stated reason."""
        for _col, _def in (
            ("declined", "INTEGER DEFAULT 0"),
            ("declined_date", "TEXT"),
            ("decline_json", "TEXT"),
            ("decline_schema_version", "TEXT"),
            ("declined_source_hash", "TEXT"),
            ("underlying_article_url", "TEXT"),
            # Source-retry (2026-08-23): a seed whose SOURCE could not be
            # acquired usably. Deliberately NOT the decline columns above --
            # a failed fetch is a technical failure, not an editorial
            # decline, and conflating them would corrupt story-rejection
            # evidence. Historical/diagnostic ONLY: candidate selection does
            # not treat these as an exclusion, because acquisition failure is
            # often transient. See mark_news_seed_source_unusable.
            ("source_unusable", "INTEGER DEFAULT 0"),
            ("source_unusable_reason", "TEXT"),
            ("source_unusable_date", "TEXT"),
            # CURRENT_ENGINE attempt write-back (2026-08-28). NEW_ENGINE_V1 never
            # recorded that it had tried a seed -- `used` is set only by the legacy
            # path's commit_success, which the new engine never reaches by design --
            # so the 09:00 cron re-selected the same top-scoring anchor the next day.
            # Observed live: 25+26 Aug ran one MIT Tech Review seed, 27+28 Aug one
            # Dezeen roundup. Deliberately separate from `used` and from the decline
            # and source_unusable columns: "the current engine tried this and reached
            # an outcome" is a third fact, and folding it into any of the others would
            # corrupt evidence those columns exist to carry.
            ("ce_attempted_date", "TEXT"),
            ("ce_attempt_run", "TEXT"),
            ("ce_attempt_outcome", "TEXT"),
            ("ce_attempt_terminal", "INTEGER DEFAULT 0"),
            ("ce_pack_verdict", "TEXT"),
            ("ce_pack_subject_words", "INTEGER"),
            # When this seed may be considered again. Written at attempt time from the
            # outcome's class, so selection is one timestamp comparison rather than
            # per-class logic in SQL. NULL on every historical row, and on a terminal
            # attempt, where ce_attempt_terminal is what retires the seed.
            ("ce_retry_after", "TEXT"),
            # NEWS/POOL V2 (2026-08-29): the material class this seed's feed supplies.
            # NULL means OTHER, which is the legacy news clock exactly.
            ("material_class", "TEXT"),
        ):
            try:
                conn.execute(f"ALTER TABLE news_seeds ADD COLUMN {_col} {_def}")
            except sqlite3.OperationalError:
                pass
        conn.commit()

    def get_news_seed(self, exclude_ids=None) -> dict | None:
        """Return best unused news seed from last 3 days, or None.

        exclude_ids skips seeds already attempted in the CURRENT run, so a
        retry loop cannot hand back the same candidate twice. That exclusion is
        run-local and evaporates when the run ends.

        A past `source_unusable` mark is deliberately NOT an exclusion here
        (owner correction, 2026-08-23). Acquisition failure is frequently
        transient -- a temporary anti-bot response, a rotating interstitial, a
        site outage, a one-off extractor miss -- and it is not an editorial
        judgement, so one bad fetch must not remove a source from every future
        production day. The columns remain as historical/diagnostic evidence
        only. A later natural run may consider the same source again; if it
        still cannot be acquired, it simply fails acquisition again and the
        normal bounded retry applies.
        """
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            self._init_news_seeds_table(conn)
            self._ensure_decline_columns(conn)
            # CONTEXTUAL FRESHNESS (2026-08-29). The universal `pub_date >= now-3d`
            # was the right clock for a news wire and the wrong one for everything
            # else: a paper, a report or an archival piece is not less interesting on
            # its fourth day, and under one 3-day window the low-cadence feeds in the
            # configuration could only ever be missed. Each class now carries its own
            # horizon, computed here and passed as parameters so the rule is readable
            # in one place. This answers "can this still be considered?" and nothing
            # else -- ranking below is untouched, and a 90-day-old paper does not
            # outrank today's news for being eligible.
            ce_cutoffs = MP.eligibility_cutoffs(datetime.now())
            cutoff_args = (ce_cutoffs[MP.CURRENT_NEWS], ce_cutoffs[MP.ESSAY_OPINION],
                           ce_cutoffs[MP.RESEARCH_REPORT], ce_cutoffs[MP.CULTURE],
                           ce_cutoffs[MP.EVERGREEN], ce_cutoffs[MP.OTHER])
            # CURRENT_ENGINE repeat-prevention (2026-08-28). Two clauses saying two
            # different things. `ce_attempt_terminal IS NOT 1` retires a seed whose
            # outcome cannot change on a rerun -- an accepted candidate, a research
            # HOLD, a deterministic anchor/scope failure. `ce_retry_after` covers
            # everything else: an outage rests the seed until tomorrow, a model-judgment
            # HOLD rests it for two days, and neither consumes it. `IS NOT 1` and
            # `IS NULL` rather than `= 0` on purpose -- historical rows carry NULL in
            # both columns and must behave exactly as they did before.
            ce_now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            # Parameterised NOT IN: never string-interpolate the ids themselves.
            # "" is a placeholder that matches no real seed id, so the clause is
            # a harmless no-op when nothing is excluded.
            _excl = tuple(exclude_ids or ()) or ("",)
            _excl_sql = ",".join("?" for _ in _excl)

            # Priority 1: confirmed disability angle
            # NOTE: excludes only a CURRENT-contract decline (declined=1 AND
            # decline_schema_version matches today's STORY_REJECTION_CONTRACT_VERSION).
            # A declined row stamped under a stale/older contract version is left
            # eligible here -- this is what makes _is_news_seed_declined_current's
            # "stale contract => reconsiderable" semantics actually reachable from
            # real selection, instead of only from a test calling the helper
            # directly. (Source-hash-based reconsideration is provenance-only:
            # no fresh evidence packet exists at selection time to compare against,
            # so it cannot be checked here -- see mark_news_seed_declined/
            # _is_news_seed_declined_current docstrings.)
            row = conn.execute("""
                SELECT id, url, title, summary, source_name, relevance_score,
                       themes, disability_angle, pub_date, underlying_article_url
                FROM news_seeds
                WHERE used = 0 AND disability_angle IS NOT NULL
                  AND pub_date >= CASE COALESCE(material_class, 'OTHER')
                                  WHEN 'CURRENT_NEWS' THEN ? WHEN 'ESSAY_OPINION' THEN ?
                                  WHEN 'RESEARCH_REPORT' THEN ? WHEN 'CULTURE' THEN ?
                                  WHEN 'EVERGREEN' THEN ? ELSE ? END
                  AND NOT (declined = 1 AND decline_schema_version = ?)
                  AND ce_attempt_terminal IS NOT 1
                  AND (ce_retry_after IS NULL OR ce_retry_after <= ?)
                  AND id NOT IN (%s)
                ORDER BY relevance_score DESC, pub_date DESC
                LIMIT 1
            """ % _excl_sql, (*cutoff_args, STORY_REJECTION_CONTRACT_VERSION, ce_now,
                              *_excl)).fetchone()

            # Priority 2: high relevance score, no angle yet
            if not row:
                row = conn.execute("""
                    SELECT id, url, title, summary, source_name, relevance_score,
                           themes, disability_angle, pub_date, underlying_article_url
                    FROM news_seeds
                    WHERE used = 0 AND relevance_score >= 0.4
                      AND pub_date >= CASE COALESCE(material_class, 'OTHER')
                                  WHEN 'CURRENT_NEWS' THEN ? WHEN 'ESSAY_OPINION' THEN ?
                                  WHEN 'RESEARCH_REPORT' THEN ? WHEN 'CULTURE' THEN ?
                                  WHEN 'EVERGREEN' THEN ? ELSE ? END
                      AND NOT (declined = 1 AND decline_schema_version = ?)
                      AND ce_attempt_terminal IS NOT 1
                      AND (ce_retry_after IS NULL OR ce_retry_after <= ?)
                      AND id NOT IN (%s)
                    ORDER BY relevance_score DESC, pub_date DESC
                    LIMIT 1
                """ % _excl_sql, (*cutoff_args, STORY_REJECTION_CONTRACT_VERSION, ce_now,
                                  *_excl)).fetchone()

            conn.close()
            if not row:
                return None
            return {
                "id": row[0], "url": row[1], "title": row[2],
                "summary": row[3], "source_name": row[4],
                "relevance_score": row[5],
                "themes": json.loads(row[6] or "[]"),
                "disability_angle": row[7],
                "pub_date": row[8],
                "underlying_article_url": row[9],
            }
        except Exception as e:
            self.logger.warning("get_news_seed failed: %s", e)
            return None

    def get_source_paragraph_count(self, url: str):
        """Body-paragraph count for the last fetch of this url, or None if
        unknown. Cached per-url by get_source_text, same as origin/length."""
        return getattr(self, "_source_paragraph_count_cache", {}).get(url)

    def _is_usable_article(self, text) -> bool:
        """Did this representation yield a usable ARTICLE? One definition only --
        classify_source_acquisition's -- so the fallback decision and the acquisition
        gate can never drift apart into two different ideas of the same word."""
        if not text:
            return False
        paras = len([ln for ln in text.splitlines() if ln.strip()])
        status, _reason = self.classify_source_acquisition(text, "fetched_article", paras)
        return status == "USABLE"

    @staticmethod
    def classify_source_acquisition(text, origin, paragraph_count=None):
        """(status, reason) for one acquisition attempt. Pure -- no I/O.

        status is "USABLE" or "SOURCE_ACQUISITION_FAILED". This answers ONLY
        "did we obtain a usable representation of the article?" -- never
        "is this a good story?". An editorial defer or decline is a different
        class entirely and is not produced here.

        Signals, strongest first (deliberately not a single character count --
        the 2026-08-23 shell was 286 chars, comfortably above
        fetch_source_article's own <200 check, and a bare threshold cannot
        separate a paywall shell from a genuinely short article):

          1. origin -- the fetch's own structured state. "fallback_summary"
             means every live route failed and we are holding the RSS blurb;
             "none" means nothing was obtained at all.
          2. paragraph_count -- structural absence of an article body.
             _extract_paragraphs already drops nav chrome and sub-80-char
             fragments, so a real article yields several blocks and a JS or
             access-wall shell yields ~none.
          3. failure markers -- short literal list of strings that are never
             article prose.
          4. length floor -- backstop only, for anything the above missed.
        """
        if origin in ("fallback_summary", "none"):
            return "SOURCE_ACQUISITION_FAILED", "fetch_no_live_article:origin=%s" % origin
        body = (text or "").strip()
        if not body:
            return "SOURCE_ACQUISITION_FAILED", "empty_extraction"
        if paragraph_count is not None and paragraph_count < _SOURCE_MIN_USABLE_PARAGRAPHS:
            return ("SOURCE_ACQUISITION_FAILED",
                    "no_article_body:paragraphs=%d<%d" % (paragraph_count,
                                                          _SOURCE_MIN_USABLE_PARAGRAPHS))
        low = body.lower()
        hit = next((m for m in _SOURCE_FAILURE_MARKERS if m in low), None)
        if hit:
            return "SOURCE_ACQUISITION_FAILED", "interstitial_marker:%s" % hit.replace(" ", "_")
        if len(body) < _SOURCE_MIN_USABLE_CHARS:
            return ("SOURCE_ACQUISITION_FAILED",
                    "extraction_too_short:%d<%d" % (len(body), _SOURCE_MIN_USABLE_CHARS))
        return "USABLE", "ok"

    def mark_news_seed_source_unusable(self, seed_id: str, reason: str):
        """Flag a seed whose SOURCE could not be acquired usably.

        Deliberately NOT mark_news_seed_declined: that records an editorial
        story-rejection verdict with a decline contract version, and a failed
        fetch is not an editorial verdict. Keeping them in separate columns is
        what lets story-rejection evidence stay honest -- and it means this
        mark never makes a seed look "declined" to anything that reads the
        decline lineage.

        This records EVIDENCE, not an exclusion (owner correction, 2026-08-23).
        Within the current run the candidate is skipped via the run-local
        exclusion set; nothing here bars it from a future scheduled run, because
        acquisition failure is often transient. The reason and date are kept so
        repeated failures are visible if a cooldown or retry-day policy is ever
        justified later -- that decision is explicitly not made here.
        """
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            self._init_news_seeds_table(conn)
            self._ensure_decline_columns(conn)
            conn.execute(
                "UPDATE news_seeds SET source_unusable = 1, source_unusable_reason = ?, "
                "source_unusable_date = ? WHERE id = ?",
                (reason, datetime.now().isoformat(timespec="seconds"), seed_id),
            )
            conn.commit()
            conn.close()
            self.logger.warning(
                "Source unusable — seed %s skipped for the REST OF THIS RUN (%s). "
                "Technical fetch failure, NOT an editorial decline, and NOT a "
                "permanent exclusion: a later run may try this source again.",
                seed_id, reason
            )
        except Exception as e:
            self.logger.warning("mark_news_seed_source_unusable failed for %s: %s", seed_id, e)

    def get_news_seed_with_usable_source(self, max_attempts: int = MAX_SOURCE_ACQUISITION_ATTEMPTS,
                                         exclude_ids=None):
        """SOURCE_ACQUISITION_RETRY_V1. Best seed whose source actually acquires.

        Why this exists: a source that cannot be fetched used to cost the whole
        day. On 2026-08-23 the top seed returned a 286-char JS/error shell,
        Story Rejection correctly found no story content, and the run ended with
        no article while 100+ unused seeds sat in the pool.

        Policy, frozen:
          * Only SOURCE_ACQUISITION_FAILED consumes an attempt. An editorial
            defer or decline happens LATER, downstream of this method, and can
            never re-enter it -- so a disliked story never triggers
            candidate-hunting.
          * Hard budget of MAX_SOURCE_ACQUISITION_ATTEMPTS candidates. No
            fourth attempt, ever.
          * The failed-candidate exclusion is RUN-LOCAL. It lasts only for the
            remaining attempts of this run; a past acquisition failure never
            bars a source from a future scheduled run (owner correction,
            2026-08-23). Only an editorial decline keeps its existing
            persistence semantics.
          * Each attempt is a real restart from candidate selection. Nothing is
            carried over: the rejected candidate's text/origin/packet never
            reach the returned seed's evidence, because the caller builds its
            evidence packet from the RETURNED seed's url only, and that url's
            own cache entry.
          * Runs entirely upstream of the Phase-2 capture hooks, so
            phase2-capture-v0.1's article-output contract is untouched.

        Attempts are recorded on self._source_acquisition_attempts (list of
        dicts) for observability, and self._source_acquisition_exhausted is set
        only when the budget was actually spent on failures -- an empty pool
        leaves it False so the pre-existing discovery/RSS fallback still
        applies unchanged.

        Costs at most max_attempts fetches: get_source_text memoizes per url, so
        the caller's later real acquisition of the returned seed is a cache hit.
        """
        budget = max(1, min(int(max_attempts), MAX_SOURCE_ACQUISITION_ATTEMPTS))
        self._source_acquisition_attempts = []
        self._source_acquisition_exhausted = False
        # exclude_ids (PREWRITER_CANDIDATE_LOOP_V1): candidates already tried
        # EDITORIALLY earlier in this same scheduled run. Seeded into the same
        # run-local exclusion list the acquisition retry uses, so one run never
        # re-offers a candidate it has already commissioned-and-deferred. Still
        # run-local: nothing here persists to a future day.
        attempted = list(exclude_ids or [])
        prior_editorial_exclusions = len(attempted)
        for n in range(1, budget + 1):
            # Only pass the new kwarg once there is something to exclude, so a
            # first attempt is an unchanged `get_news_seed()` call -- existing
            # callers and test stubs that replaced the old zero-arg signature
            # keep working untouched.
            seed = self.get_news_seed(exclude_ids=attempted) if attempted else self.get_news_seed()
            if not seed:
                break
            text = self.get_source_text(
                seed["url"], fallback_text=seed.get("summary"),
                underlying_url=seed.get("underlying_article_url"),
            )
            status, reason = self.classify_source_acquisition(
                text, self.get_source_origin(seed["url"]),
                self.get_source_paragraph_count(seed["url"]),
            )
            self._source_acquisition_attempts.append({
                "attempt": n, "seed_id": seed["id"], "url": seed["url"],
                "source_name": seed.get("source_name"), "result": status, "reason": reason,
                "chars": len((text or "").strip()),
                "paragraphs": self.get_source_paragraph_count(seed["url"]),
            })
            if status == "USABLE":
                if attempted:
                    self.logger.info(
                        "Source acquisition: attempt %d/%d usable — seed %s "
                        "(after %d SOURCE_ACQUISITION_FAILED candidate(s))",
                        n, budget, seed["id"], len(attempted),
                    )
                return seed
            self.mark_news_seed_source_unusable(seed["id"], reason)
            attempted.append(seed["id"])
        # only ACQUISITION failures count toward exhaustion -- editorial
        # exclusions passed in by the candidate loop must not trip it
        if len(attempted) > prior_editorial_exclusions:
            self._source_acquisition_exhausted = True
            self.logger.error(
                "NO_ARTICLE_SOURCE_ACQUISITION_EXHAUSTED: %d/%d candidate(s) failed "
                "source acquisition (%s). No further attempt.", len(attempted), budget,
                ", ".join("%s=%s" % (a["seed_id"], a["reason"])
                          for a in self._source_acquisition_attempts),
            )
        return None

    def mark_news_seed_used(self, seed_id: str):
        """Mark a news seed as used so it won't be picked again."""
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            conn.execute(
                "UPDATE news_seeds SET used = 1, used_date = ? WHERE id = ?",
                (datetime.now().strftime("%Y-%m-%d"), seed_id),
            )
            conn.commit()
            conn.close()
            self.logger.info("Marked news seed %s as used", seed_id)
        except Exception as e:
            self.logger.warning("Could not mark news seed as used: %s", e)

    # ── CURRENT_ENGINE attempt write-back ────────────────────────────────────
    # Retry cooldown for a transient failure. One natural article run happens per
    # day, so "not again today" is the whole rule: a provider or infrastructure
    # failure frees the seed for the next natural run rather than consuming it,
    # and no scheduler, backoff curve or retry queue is introduced.
    CE_RETRY_COOLDOWN_HOURS = 20          # transient/operational failure
    # A Grounding-derived or otherwise unnamed HOLD is NOT proven to be a property of
    # the seed. The authoritative whole-article grounder is measured non-deterministic
    # on byte-identical input -- a classification flipped 1 in 10 trials at the provider
    # default AND at temperature 0, findings appeared and vanished between passes, and
    # some carried reasons contradicting their own labels. Retiring a seed on one such
    # verdict would let a classifier wobble delete a story permanently. So it rests for
    # two days instead of one, and comes back if it is still otherwise eligible.
    CE_REVIEWABLE_COOLDOWN_HOURS = 48

    CE_TERMINAL = "TERMINAL"
    CE_TRANSIENT = "TRANSIENT_FAILURE"
    CE_REVIEWABLE = "NONDETERMINISTIC_OR_REVIEWABLE_HOLD"

    # Reason codes whose truth follows from the unchanged source and research material
    # rather than from a model's classification of prose. These are the only HOLDs that
    # retire a seed.
    CE_DETERMINISTIC_HOLD_CODES = (
        "HOLD_INSUFFICIENT_RESEARCH",                    # the pack looked and found nothing
        "DISCOVERY_SUBJECT_OUTSIDE_RESEARCHED_SCOPE",    # researched A, wrote about B
        "DISCOVERY_SOURCE_ANCHOR_MISSING",
        "DISCOVERY_SOURCE_ANCHOR_NOT_IN_SOURCE",
        "DISCOVERY_SOURCE_ANCHOR_TOO_SHORT",
    )

    @staticmethod
    def classify_current_engine_attempt(result: dict) -> tuple[bool, str]:
        """(terminal, outcome) for one CURRENT_ENGINE run against one seed.

        Read from the run's STRUCTURED fields -- `run_status.status`, `reason_code`,
        `decision` -- never by pattern-matching prose. Terminal means: running this
        same unchanged source again tomorrow has no principled reason to come out
        differently. Retryable means the run failed for an operational reason that
        says nothing about the material.

        Anything unrecognised is RETRYABLE. Wrongly retrying a seed costs one run;
        wrongly consuming one loses a story permanently, and the failure mode this
        method exists to fix was itself invisible for days.
        """
        status = ((result or {}).get("run_status") or {}).get("status")
        if status:
            # PROVIDER_FAILURE / CONTRACT_FAILURE: transport, truncation, or a reply
            # that did not satisfy a stage contract. Infrastructure, not evidence.
            return DiscoveryMixin.CE_TRANSIENT, "%s:%s" % (DiscoveryMixin.CE_TRANSIENT, status)
        decision = (result or {}).get("decision")
        reason = (result or {}).get("reason_code") or ""
        if decision == "ACCEPT":
            return DiscoveryMixin.CE_TERMINAL, "TERMINAL:ACCEPT"
        if decision == "HOLD":
            if reason in DiscoveryMixin.CE_DETERMINISTIC_HOLD_CODES:
                return DiscoveryMixin.CE_TERMINAL, "TERMINAL:%s" % reason
            if reason:
                # A named code we do not yet know to be deterministic. Rest it, do not
                # retire it: the conservative direction costs a day, the other costs
                # the seed.
                return (DiscoveryMixin.CE_REVIEWABLE,
                        "%s:%s" % (DiscoveryMixin.CE_REVIEWABLE, reason))
            # An unnamed HOLD is a model judgement -- the grounder's uncertainty and
            # unsupported policies both arrive here with no reason code -- and the
            # grounder is measured unstable on identical input. Reviewable, never
            # terminal.
            return DiscoveryMixin.CE_REVIEWABLE, "%s:HOLD" % DiscoveryMixin.CE_REVIEWABLE
        return (DiscoveryMixin.CE_TRANSIENT,
                "%s:UNCLASSIFIED:%s" % (DiscoveryMixin.CE_TRANSIENT, decision or "none"))

    def mark_news_seed_current_engine_attempt(self, seed_id: str, *, run: str,
                                              klass: str, outcome: str,
                                              pack_verdict: str | None = None,
                                              pack_subject_words=None) -> None:
        """Record that CURRENT_ENGINE attempted this seed, and what came of it.

        Records only what the run already produced: its own id, the classified
        outcome, and -- where the Research Pack stage was reached -- that pack's own
        verdict and subject-relevant word count. `used` is untouched: it still means
        exactly what it meant, an article was committed by the legacy path.
        """
        hours = {self.CE_TRANSIENT: self.CE_RETRY_COOLDOWN_HOURS,
                 self.CE_REVIEWABLE: self.CE_REVIEWABLE_COOLDOWN_HOURS}.get(klass)
        retry_after = ((datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
                       if hours else None)
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            self._ensure_decline_columns(conn)
            conn.execute(
                "UPDATE news_seeds SET ce_attempted_date = ?, ce_attempt_run = ?, "
                "ce_attempt_outcome = ?, ce_attempt_terminal = ?, ce_retry_after = ?, "
                "ce_pack_verdict = COALESCE(?, ce_pack_verdict), "
                "ce_pack_subject_words = COALESCE(?, ce_pack_subject_words) "
                "WHERE id = ?",
                (datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), run, outcome,
                 1 if klass == self.CE_TERMINAL else 0, retry_after,
                 pack_verdict, pack_subject_words, seed_id))
            conn.commit()
            conn.close()
            self.logger.info("CURRENT_ENGINE attempt recorded on seed %s: %s "
                             "(class=%s, retry_after=%s, pack=%s)",
                             seed_id, outcome, klass, retry_after or "never", pack_verdict)
        except Exception as e:
            self.logger.warning("Could not record CURRENT_ENGINE attempt on seed %s: %s",
                                seed_id, e)

    def mark_news_seed_declined(self, seed_id: str, decline_record: dict):
        """Story Rejection V1 (DSR2): persist an authoritative Layer-1 decline.
        Does NOT touch `used` (a decline is not a consumption — the source is
        rejected, not published). Idempotent on the row; only the latest
        decline record + its source hash are kept, but decline_json is the
        full structured record (stamps its own schema version for audit/
        reconsideration). A CURRENT-contract declined seed is excluded by
        get_news_seed's priorities and by extract_top_angles / the CJ shadow
        sampler; a seed declined under a stale/older contract version is left
        reconsiderable by all three (see _is_news_seed_declined_current)."""
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            self._ensure_decline_columns(conn)
            conn.execute(
                "UPDATE news_seeds SET declined = 1, declined_date = ?, "
                "decline_json = ?, decline_schema_version = ?, declined_source_hash = ? "
                "WHERE id = ?",
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    json.dumps(decline_record),
                    decline_record.get("contract"),
                    decline_record.get("source_hash"),
                    seed_id,
                ),
            )
            conn.commit()
            conn.close()
            self.logger.info("Marked news seed %s as DECLINED (story rejection)", seed_id)
        except Exception as e:
            self.logger.warning("Could not mark news seed as declined: %s", e)

    def get_news_seed_decline(self, seed_id: str) -> dict | None:
        """Return the persisted decline record for a seed (for tests/audit).
        Only CURRENT per the recorded schema/version — a stale contract row is
        returned here but Selection-exclusion helpers treat it as
        reconsiderable (see _is_news_seed_declined_current)."""
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            self._ensure_decline_columns(conn)
            row = conn.execute(
                "SELECT decline_json, decline_schema_version, declined_source_hash "
                "FROM news_seeds WHERE id = ?", (seed_id,),
            ).fetchone()
            conn.close()
            if not row or not row[0]:
                return None
            return {
                "record": json.loads(row[0]) if row[0] else None,
                "contract": row[1],
                "source_hash": row[2],
            }
        except Exception:
            return None

    def _is_news_seed_declined_current(self, conn, seed_id: str, packet) -> bool:
        """True iff the seed's recorded decline is still authoritative: a
        current contract version (sr1) AND the recorded source_hash matches the
        evidence_packet currently in hand. A stale/mismatched row is treated as
        RECONSIDERABLE (returns False) so a changed source or a contract bump can
        be re-judged rather than permanently silencing the seed.

        IMPORTANT SCOPE NOTE: real SELECTION (get_news_seed / extract_top_angles /
        sample_shadow_candidates) only ever checks the CONTRACT-VERSION half of
        this -- a stale-contract row is reconsidered by SQL directly, with no
        `packet` involved, because no fresh evidence exists at selection time
        for a URL that hasn't been (re)fetched yet. The source_hash comparison
        this method performs is provenance/audit machinery for a caller that
        already HAS a fresh evidence_packet (e.g. a future explicit
        revalidation pass) -- declined_source_hash is persisted so that IF such
        a revalidation ever produces a different current hash, the old decline
        can be recognized as stale. Automatic same-URL remote-change detection
        is NOT implemented: nothing in production re-fetches a declined URL to
        notice its content changed. That would require dedicated revalidation
        machinery this prototype deliberately does not add."""
        try:
            row = conn.execute(
                "SELECT declined, decline_schema_version, declined_source_hash "
                "FROM news_seeds WHERE id = ?", (seed_id,),
            ).fetchone()
        except Exception:
            return False
        if not row or row[0] == 0 or row[0] is None:
            return False
        _decline_version = row[1]
        _recorded_hash = row[2]
        if _decline_version != STORY_REJECTION_CONTRACT_VERSION:
            return False
        _current_hash = (packet or {}).get("source_hash") if packet else None
        if _current_hash and _recorded_hash and _current_hash != _recorded_hash:
            return False
        return True

    def _news_seed_to_agent(self, themes: list) -> str:
        """Map news seed themes to preferred persona.

        THIS is the live map — news_fetcher.py's module-level THEME_TO_PERSONA is
        defined but never referenced by anything (verified: no import of
        news_fetcher anywhere, no use inside news_fetcher itself). Commit 508cc86
        ("shift discovery topic weighting per explicit editorial direction") added
        the five new buckets to that dead copy only — it touched one file — so the
        persona routing that shift was supposed to ship never took effect. Every
        space_cosmos / philosophy / economy_finance / sustainability_ecology /
        indigenous_tribal seed fell through to the `return "Maya Flux"` default
        below, i.e. the cost-and-procurement policy persona got first refusal on
        exactly the astronomy/anthropology/philosophy material the shift was meant
        to steer toward Zen Circuit and Siri Sage. Assignments below are copied
        verbatim from 508cc86's rationale, not re-derived.

        "history_archive" (mythology/ritual/folklore/artifact) and
        "behavioral_science" -- added 2026-08-09 continuation, owner decision:
        history_archive -> Pixel Nova (visual/material-culture lens fits
        artifact/relic/ritual material better than any other persona's focus);
        behavioral_science -> Zen Circuit (pattern-analysis persona, natural
        fit for cognition/bias material). Both previously fell through to the
        Maya Flux default below.
        """
        _THEME_TO_PERSONA = {
            "architecture":   "Pixel Nova",
            "art_culture":    "Pixel Nova",
            "technology":     "Zen Circuit",
            "science_nature": "Zen Circuit",
            "language":       "Siri Sage",
            "education":      "Siri Sage",
            "health_systems": "Maya Flux",
            "business_labor": "Maya Flux",
            "philosophy":            "Zen Circuit",
            "space_cosmos":          "Zen Circuit",
            "economy_finance":       "Maya Flux",
            "sustainability_ecology": "Maya Flux",
            "indigenous_tribal":     "Siri Sage",
            "history_archive":       "Pixel Nova",
            "behavioral_science":    "Zen Circuit",
        }
        for theme in themes:
            if theme in _THEME_TO_PERSONA:
                return _THEME_TO_PERSONA[theme]
        return "Maya Flux"  # default
