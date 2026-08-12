/**
 * Crip Minds Reader Lab — shared low-level helpers.
 *
 * Extracted out of index.js when the admin control plane was added, so
 * the reviewer routes (index.js), the admin API (adminApi.js), and the
 * shared publication service (publish.js) all use the exact same
 * crypto/response/rate-limit primitives instead of three copies drifting
 * apart. Nothing here is reviewer- or admin-specific.
 */

// ---------------------------------------------------------------------
// response helpers — every response goes through one of these so the
// security headers can't be forgotten on a new route
// ---------------------------------------------------------------------

export const BASE_SECURITY_HEADERS = {
  "x-robots-tag": "noindex, nofollow, noarchive",
  "referrer-policy": "same-origin",
  "x-content-type-options": "nosniff",
  "cache-control": "no-store",
  "x-frame-options": "DENY",
};

export function secureJson(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...BASE_SECURITY_HEADERS,
      ...extraHeaders,
    },
  });
}

export function notFound() {
  return new Response("Not found.", { status: 404, headers: BASE_SECURITY_HEADERS });
}

export function secureHtml(body, status = 200, { nonce, csp, extraHeaders = {} } = {}) {
  const headers = {
    "content-type": "text/html; charset=utf-8",
    ...BASE_SECURITY_HEADERS,
    ...extraHeaders,
  };
  if (csp) headers["content-security-policy"] = csp;
  return new Response(body, { status, headers });
}

export function redirect(location, extraHeaders = {}) {
  return new Response(null, {
    status: 302,
    headers: { location, ...BASE_SECURITY_HEADERS, ...extraHeaders },
  });
}

// ---------------------------------------------------------------------
// crypto / id helpers
// ---------------------------------------------------------------------

export async function sha256Hex(text) {
  const data = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export function randomHex(byteLength) {
  const bytes = crypto.getRandomValues(new Uint8Array(byteLength));
  return [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export function newNonce() {
  // base64 of 16 random bytes — used for CSP script/style nonces only,
  // not a security credential in its own right (it's public in the HTML).
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return btoa(String.fromCharCode(...bytes));
}

export function newId(prefix) {
  return `${prefix}_${crypto.randomUUID()}`;
}

export function nowIso() {
  return new Date().toISOString();
}

export function timingSafeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  const enc = new TextEncoder();
  const aBytes = enc.encode(a);
  const bBytes = enc.encode(b);
  // A length mismatch is checked directly (leaking length alone is a far
  // smaller signal than leaking a byte-by-byte early-exit compare would
  // be, and matches the behavior of e.g. Node's own
  // crypto.timingSafeEqual, which requires equal-length buffers).
  if (aBytes.length !== bBytes.length) return false;
  let diff = 0;
  for (let i = 0; i < aBytes.length; i++) diff |= aBytes[i] ^ bBytes[i];
  return diff === 0;
}

export function clientIp(request) {
  return request.headers.get("cf-connecting-ip") || "unknown";
}

// ---------------------------------------------------------------------
// cookie helpers
// ---------------------------------------------------------------------

export function parseCookie(request, name) {
  const header = request.headers.get("cookie") || "";
  for (const part of header.split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (k === name) return rest.join("=");
  }
  return null;
}

// ---------------------------------------------------------------------
// rate limiting (D1-backed, generous, IP-keyed)
// ---------------------------------------------------------------------

// Counts every call in the bucket (used for endpoints where legitimate
// traffic is inherently low-volume, e.g. one-time invite links) — pass
// or fail, each attempt consumes one unit of budget.
export async function checkRateLimit(env, bucket, key, { max, windowSeconds }) {
  const windowStart = Math.floor(Date.now() / 1000 / windowSeconds) * windowSeconds;
  const bucketKey = `${bucket}:${key}`;
  const row = await env.DB.prepare(
    "SELECT count FROM rate_limit_events WHERE bucket_key = ? AND window_start = ?"
  )
    .bind(bucketKey, windowStart)
    .first();
  const current = row ? row.count : 0;
  if (current >= max) return false;
  await env.DB.prepare(
    `INSERT INTO rate_limit_events (bucket_key, window_start, count) VALUES (?, ?, 1)
     ON CONFLICT (bucket_key, window_start) DO UPDATE SET count = count + 1`
  )
    .bind(bucketKey, windowStart)
    .run();
  return true;
}

// Peek-only: reports whether a bucket is already saturated, without
// consuming budget. Used where only FAILURES should count against the
// limit (e.g. admin auth) — a burst of legitimate correct-credential
// calls must never lock the caller out.
export async function isRateLimited(env, bucket, key, { max, windowSeconds }) {
  const windowStart = Math.floor(Date.now() / 1000 / windowSeconds) * windowSeconds;
  const bucketKey = `${bucket}:${key}`;
  const row = await env.DB.prepare(
    "SELECT count FROM rate_limit_events WHERE bucket_key = ? AND window_start = ?"
  )
    .bind(bucketKey, windowStart)
    .first();
  return (row ? row.count : 0) >= max;
}

export async function recordRateLimitAttempt(env, bucket, key, { windowSeconds }) {
  const windowStart = Math.floor(Date.now() / 1000 / windowSeconds) * windowSeconds;
  const bucketKey = `${bucket}:${key}`;
  await env.DB.prepare(
    `INSERT INTO rate_limit_events (bucket_key, window_start, count) VALUES (?, ?, 1)
     ON CONFLICT (bucket_key, window_start) DO UPDATE SET count = count + 1`
  )
    .bind(bucketKey, windowStart)
    .run();
}
