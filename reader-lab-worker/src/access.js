/**
 * Crip Minds Reader Lab — Cloudflare Access verification for /admin*.
 *
 * As of this pass, Cloudflare Access is NOT enabled on the account this
 * Worker deploys to (`GET .../access/apps` returns
 * "access.api.error.not_enabled" — confirmed directly against the API,
 * not assumed). This file is written to fail CLOSED until it is: every
 * admin browser route requires both env.ACCESS_TEAM_DOMAIN and
 * env.ACCESS_AUD to be set, and returns 503 if either is missing. That
 * means the /admin routes can be safely deployed today — they are
 * structurally unusable by anyone, including an attacker, until the
 * manual one-time Cloudflare Zero Trust setup described in
 * README.md's "Admin control plane" section is completed and those two
 * values are set as Worker vars/secrets.
 *
 * Design constraint (see the design doc's admin-control-plane section,
 * ## Security): ADMIN_TOKEN must never reach a browser. This file is the
 * alternative — real Access-issued, short-lived, per-request JWTs,
 * verified here rather than trusted blindly (Cloudflare's edge already
 * checks the Access policy before proxying the request through, but this
 * Worker re-verifies independently rather than trusting a header that
 * could in principle be forged if the Worker were ever reachable by a
 * path that bypasses Access — defense in depth, not redundant caution).
 */

const JWKS_CACHE = { teamDomain: null, keys: null, fetchedAt: 0 };
const JWKS_CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour — Access rotates signing keys infrequently

function base64UrlDecode(input) {
  const padded = input.replace(/-/g, "+").replace(/_/g, "/").padEnd(input.length + ((4 - (input.length % 4)) % 4), "=");
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function base64UrlDecodeToString(input) {
  return new TextDecoder().decode(base64UrlDecode(input));
}

async function fetchJwks(teamDomain) {
  const now = Date.now();
  if (JWKS_CACHE.keys && JWKS_CACHE.teamDomain === teamDomain && now - JWKS_CACHE.fetchedAt < JWKS_CACHE_TTL_MS) {
    return JWKS_CACHE.keys;
  }
  const resp = await fetch(`https://${teamDomain}.cloudflareaccess.com/cdn-cgi/access/certs`);
  if (!resp.ok) throw new Error(`access_certs_fetch_failed: ${resp.status}`);
  const body = await resp.json();
  JWKS_CACHE.teamDomain = teamDomain;
  JWKS_CACHE.keys = body.keys || [];
  JWKS_CACHE.fetchedAt = now;
  return JWKS_CACHE.keys;
}

async function importJwk(jwk) {
  return crypto.subtle.importKey(
    "jwk",
    jwk,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["verify"]
  );
}

// Returns the verified payload ({email, sub, aud, exp, iss, ...}) or null.
// Never throws for an invalid/expired/wrong-audience token — a null
// return is the only signal callers need (see requireAccessAuth).
export async function verifyAccessJwt(env, jwt) {
  if (!jwt || typeof jwt !== "string") return null;
  const parts = jwt.split(".");
  if (parts.length !== 3) return null;
  const [headerB64, payloadB64, signatureB64] = parts;

  let header, payload;
  try {
    header = JSON.parse(base64UrlDecodeToString(headerB64));
    payload = JSON.parse(base64UrlDecodeToString(payloadB64));
  } catch {
    return null;
  }
  if (header.alg !== "RS256") return null;

  const now = Math.floor(Date.now() / 1000);
  if (typeof payload.exp !== "number" || payload.exp < now) return null;

  const expectedIssuer = `https://${env.ACCESS_TEAM_DOMAIN}.cloudflareaccess.com`;
  if (payload.iss !== expectedIssuer) return null;

  const aud = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
  if (!aud.includes(env.ACCESS_AUD)) return null;

  let keys;
  try {
    keys = await fetchJwks(env.ACCESS_TEAM_DOMAIN);
  } catch {
    return null;
  }
  const jwk = keys.find((k) => k.kid === header.kid);
  if (!jwk) return null;

  let key;
  try {
    key = await importJwk(jwk);
  } catch {
    return null;
  }

  const signedData = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
  const signature = base64UrlDecode(signatureB64);
  const ok = await crypto.subtle.verify({ name: "RSASSA-PKCS1-v1_5" }, key, signature, signedData);
  if (!ok) return null;

  return payload;
}

function extractJwt(request) {
  const headerJwt = request.headers.get("cf-access-jwt-assertion");
  if (headerJwt) return headerJwt;
  const cookieHeader = request.headers.get("cookie") || "";
  for (const part of cookieHeader.split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (k === "CF_Authorization") return rest.join("=");
  }
  return null;
}

// Gate for every /admin (browser-facing) route. Fails closed (503) if
// Access hasn't been configured for this Worker yet — see file header.
// On success, calls handler(request, env, identity) where identity is
// { email, sub }; identity.email is used only for audit-log attribution,
// never for anything security-load-bearing beyond what Access itself
// already enforced via its policy.
export async function requireAccessAuth(request, env, handler) {
  // Local-dev-only bypass: ACCESS_DEV_BYPASS must never be set anywhere
  // except a gitignored .dev.vars file (see README.md) — it is never
  // read from wrangler.toml or a deployed secret in this project's own
  // deploy process, so it cannot silently ship to production.
  if (env.ACCESS_DEV_BYPASS === "1") {
    return handler(request, env, { email: "dev-bypass@local", sub: "dev-bypass" });
  }

  if (!env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD) {
    return new Response(
      JSON.stringify({
        error: "admin_access_not_configured",
        detail:
          "Cloudflare Access is not yet set up for this Worker. See README.md 'Admin control plane' for the exact remaining manual step.",
      }),
      { status: 503, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } }
    );
  }

  const jwt = extractJwt(request);
  const payload = await verifyAccessJwt(env, jwt);
  if (!payload || !payload.email) {
    return new Response(JSON.stringify({ error: "unauthorized" }), {
      status: 401,
      headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
    });
  }

  const allowlist = (env.ACCESS_ALLOWED_EMAILS || "")
    .split(",")
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean);
  if (allowlist.length > 0 && !allowlist.includes(payload.email.toLowerCase())) {
    return new Response(JSON.stringify({ error: "unauthorized" }), {
      status: 401,
      headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
    });
  }

  return handler(request, env, { email: payload.email, sub: payload.sub });
}
