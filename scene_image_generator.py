#!/usr/bin/env python3
"""
DYNAMIC AI IMAGE GENERATOR

Architecture:
  1. Qwen extracts 3 distinct visual concepts from article (setting, moment, symbol)
  2. Builds rich pixel-art prompts with disability-culture framing
  3. Pollinations.ai FLUX generates actual AI images (non-deterministic, seed=-1)
  4. Gradient PNG fallback if network unavailable

No hardcoded scene types. Fully context-aware.
Requires: POLLINATIONS_API_KEY env var (sk_... from https://enter.pollinations.ai)
"""

import json
import logging
import os
import re
import struct
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

logger = logging.getLogger(__name__)


class SceneImageGenerator:
    def __init__(self, width=800, height=450, pixel_size=5):
        self.width = width
        self.height = height
        self.pixel_size = max(1, min(10, pixel_size))
        self.gw = width // pixel_size
        self.gh = height // pixel_size
        self.qwen_url = "http://vision-gateway:8080/v1/chat/completions"
        self.pollinations_key = os.environ.get("POLLINATIONS_API_KEY", "")
        self.pollinations_base = "https://gen.pollinations.ai"

    # ── Qwen ──────────────────────────────────────────────────────────────────

    def _qwen_text(self, prompt, timeout=60):
        payload = json.dumps({
            "model": "qwen3.5:9b", "stream": False,
            "messages": [{"role": "user", "content": "/no_think " + prompt}],
        }).encode()
        try:
            req = urllib.request.Request(
                self.qwen_url, data=payload,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = json.loads(r.read())["choices"][0]["message"]["content"]
                return re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        except Exception as e:
            logger.warning("Qwen call failed: %s", e)
            return None

    # ── Prompt generation ─────────────────────────────────────────────────────

    def _generate_prompts(self, content, title):
        """Ask Qwen to produce 3 distinct image prompts from article content."""
        excerpt = content[:400]
        prompt = f"""You are visual director for a disability rights art publication.

Article title: {title}
Article excerpt: {excerpt}

Generate 3 VISUALLY DISTINCT pixel art image prompts for this article:
1. SETTING - the physical environment/place the article is about
2. MOMENT - a specific human action or interaction from the article
3. SYMBOL - a close-up detail, metaphor, or symbolic element from the article

Rules: start with "16-bit pixel art," | disabled protagonists | vivid colors | no tragedy | concrete

Return ONLY valid JSON:
{{"setting": "16-bit pixel art, ...", "moment": "16-bit pixel art, ...", "symbol": "16-bit pixel art, ..."}}"""

        for attempt in range(2):
            raw = self._qwen_text(prompt, timeout=90)
            if not raw:
                logger.warning("Qwen attempt %d: no response", attempt + 1)
                continue
            m = re.search(r'\{[^{}]*"setting"[^{}]*\}', raw, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group())
                    setting = data.get('setting', '')
                    moment = data.get('moment', '')
                    symbol = data.get('symbol', '')
                    if setting and moment and symbol:
                        logger.info("Qwen prompts OK (attempt %d)", attempt + 1)
                        return [setting, moment, symbol]
                except json.JSONDecodeError:
                    pass
            logger.warning("Qwen attempt %d: bad JSON", attempt + 1)

        logger.warning("All Qwen attempts failed, using keyword fallback")
        return self._fallback_prompts(title)

    def _fallback_prompts(self, title):
        """Keyword-derived fallback prompts when Qwen unavailable."""
        t = title.lower()
        base = "16-bit pixel art,"
        if any(w in t for w in ['deaf', 'hearing', 'asl', 'sign language']):
            return [
                f"{base} deaf community center with sign language class in session, vivid colors, isometric view",
                f"{base} person at video relay service terminal signing expressively, warm lighting",
                f"{base} two hands forming ASL sign close-up, pixel art, jewel tones",
            ]
        if any(w in t for w in ['wheelchair', 'mobility', 'ramp', 'accessible']):
            return [
                f"{base} accessible urban street with curb cuts and tactile paving, sunny day, city skyline",
                f"{base} wheelchair user navigating accessible building entrance with confidence, vivid colors",
                f"{base} accessibility ramp close-up with crip pride sticker, bright colors, pixel art",
            ]
        if any(w in t for w in ['blind', 'vision', 'braille', 'screen reader']):
            return [
                f"{base} inclusive tech workspace with braille displays and adaptive monitors, modern office",
                f"{base} blind programmer at ergonomic desk using screen reader, focused expression, pixel art",
                f"{base} braille cell close-up with glowing blue dots, dark background, pixel art",
            ]
        if any(w in t for w in ['ai', 'tech', 'digital', 'algorithm', 'software']):
            return [
                f"{base} inclusive tech lab with diverse disabled engineers, accessible workstations, pixel art",
                f"{base} disabled AI researcher presenting at conference, sign language interpreter visible",
                f"{base} neural network diagram with accessibility nodes highlighted, blue and purple palette",
            ]
        if any(w in t for w in ['art', 'film', 'culture', 'crip', 'disability justice']):
            return [
                f"{base} disability arts festival outdoor stage with diverse crip crowd, golden hour light",
                f"{base} disabled artist performing with AAC device, spotlight, pixel art audience",
                f"{base} crip pride banner in rainbow colors over city skyline, pixel art",
            ]
        # generic
        return [
            f"{base} accessible urban plaza with diverse disabled community gathering, vivid colors, isometric",
            f"{base} disabled activist speaking at open microphone, diverse crowd, warm evening light",
            f"{base} accessibility symbol redesigned as community mural on city wall, bright pixel art",
        ]

    # ── Pollinations.ai ───────────────────────────────────────────────────────

    def _fetch_pollinations(self, prompt, timeout=60):
        """Fetch image from pollinations.ai. Returns JPEG bytes.
        Uses POLLINATIONS_API_KEY env var for auth.
        seed=-1 → non-deterministic (different image each call).
        model=zimage → Z-Image Turbo (fast, 2x upscaling, free tier).
        """
        encoded = urllib.parse.quote(prompt, safe='')
        params = (
            f"?width={self.width}&height={self.height}"
            f"&model=zimage&seed=-1&enhance=true&nologo=true"
        )
        if self.pollinations_key:
            params += f"&key={urllib.parse.quote(self.pollinations_key, safe='')}"
        url = f"{self.pollinations_base}/image/{encoded}{params}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "disability-ai-collective/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        if len(data) < 1000:
            raise ValueError(f"Suspicious response: {len(data)} bytes — check API key or model")
        return data

    # ── Main generation ───────────────────────────────────────────────────────

    def generate_content_aware_images(self, content, title, slug, num_images=3, validate=False):
        """Generate num_images context-aware images via pollinations.ai FLUX."""
        images = []
        labels = ['setting', 'moment', 'symbol']

        try:
            logger.info("Generating prompts for: %s", title)
            prompts = self._generate_prompts(content, title)
            while len(prompts) < num_images:
                prompts.append(prompts[-1])
            prompts = prompts[:num_images]

            for i, prompt in enumerate(prompts):
                label = labels[i] if i < len(labels) else f"scene{i+1}"
                logger.info("Image %d/%d [%s]: %s...", i+1, num_images, label, prompt[:80])
                try:
                    img_data = self._fetch_pollinations(prompt)
                    filename = f"{slug}_{label}_{i+1}.jpg"
                    images.append({
                        'data': img_data,
                        'filename': filename,
                        'description': f"{label.title()} — {title}",
                        'score': 8,
                        'scene': label,
                        'prompt': prompt,
                    })
                    logger.info("  OK %s (%d bytes)", filename, len(img_data))
                except Exception as e:
                    logger.warning("  Pollinations failed (%s) — pixel fallback", e)
                    img_data = self._pixel_fallback(i)
                    images.append({
                        'data': img_data,
                        'filename': f"{slug}_{label}_{i+1}.png",
                        'description': f"{label.title()} — {title}",
                        'score': 3,
                        'scene': label,
                    })

        except Exception as e:
            logger.error("generate_content_aware_images failed: %s", e)
            for i in range(num_images):
                label = labels[i] if i < len(labels) else f"scene{i+1}"
                images.append({
                    'data': self._emergency_png(),
                    'filename': f"{slug}_{label}_{i+1}.png",
                    'description': f"{label.title()} — {title}",
                    'score': 1,
                    'scene': label,
                })

        return images

    # ── Pixel fallback ────────────────────────────────────────────────────────

    def _pixel_fallback(self, index=0):
        """Gradient fallback when pollinations.ai is unavailable."""
        palettes = [
            [(30, 50, 110), (70, 110, 190), (150, 190, 230)],
            [(50, 90, 50),  (90, 150, 70),  (170, 210, 130)],
            [(90, 40, 110), (150, 70, 170), (210, 150, 230)],
        ]
        colors = palettes[index % len(palettes)]
        grid = [[(0, 0, 0)] * self.gw for _ in range(self.gh)]
        for y in range(self.gh):
            t = y / max(1, self.gh - 1)
            if t < 0.5:
                c = tuple(int(colors[0][k] + (colors[1][k] - colors[0][k]) * t * 2) for k in range(3))
            else:
                c = tuple(int(colors[1][k] + (colors[2][k] - colors[1][k]) * (t - 0.5) * 2) for k in range(3))
            for x in range(self.gw):
                grid[y][x] = c
        return self._grid_to_png(grid)

    def _emergency_png(self):
        grid = [[(20, 20, 40)] * self.gw for _ in range(self.gh)]
        return self._grid_to_png(grid)

    def _grid_to_png(self, grid):
        raw = b''
        for gy in range(self.gh):
            for _ in range(self.pixel_size):
                raw += b'\x00'
                for gx in range(self.gw):
                    cell = grid[gy][gx]
                    if not isinstance(cell, (tuple, list)) or len(cell) < 3:
                        cell = (0, 0, 0)
                    r = max(0, min(255, int(cell[0])))
                    g = max(0, min(255, int(cell[1])))
                    b = max(0, min(255, int(cell[2])))
                    raw += bytes([r, g, b]) * self.pixel_size
        compressed = zlib.compress(raw)
        w = self.gw * self.pixel_size
        h = self.gh * self.pixel_size
        png = b'\x89PNG\r\n\x1a\n'
        ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
        png += struct.pack('>I', len(ihdr)) + b'IHDR' + ihdr
        png += struct.pack('>I', zlib.crc32(b'IHDR' + ihdr) & 0xFFFFFFFF)
        png += struct.pack('>I', len(compressed)) + b'IDAT' + compressed
        png += struct.pack('>I', zlib.crc32(b'IDAT' + compressed) & 0xFFFFFFFF)
        png += struct.pack('>I', 0) + b'IEND'
        png += struct.pack('>I', zlib.crc32(b'IEND') & 0xFFFFFFFF)
        return png


# ─────────────────────────────────────────────────────────────────────────────

def generate_article_images(content, title, slug, num_images=3):
    gen = SceneImageGenerator()
    imgs = gen.generate_content_aware_images(content, title, slug, num_images)
    return [{'data': i['data'], 'filename': i['filename'], 'alt_text': i['description']} for i in imgs]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    content = "I'm standing at Union Station. The departure board flickers. I'm deaf and this hub ignores deaf users. No visual alerts, no captions on the screens, no tactile indicators at the platform edge."
    title = "The Station That Forgot Deaf Users"
    gen = SceneImageGenerator()
    imgs = gen.generate_content_aware_images(content, title, "test-station", 3)
    for img in imgs:
        p = Path(f"/tmp/{img['filename']}")
        p.write_bytes(img['data'])
        logger.info("  %s  %d bytes  scene:%s  score:%s", img['filename'], len(img['data']), img.get('scene'), img.get('score'))
