#!/usr/bin/env python3
"""
SCENE-BASED PIXEL ART IMAGE GENERATOR

Architecture:
  - Renders real-world SCENES (not abstract patterns) at pixel_size=5
  - 8 scene types: transit_hub, urban_street, office, theater, campus,
    library, open_air, data_center
  - Qwen picks scene type + mood + accessibility element from article
  - Layer rendering: sky → far buildings → midground → foreground → elements
  - Artistic DNA: seeded palette + pixel_size consistent across all 3 article images
  - Qwen vision validation with /no_think for fast feedback
"""

import logging
import math
import random
import struct
import zlib
import re
import json
import base64
import hashlib
import urllib.request
from pathlib import Path


logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Color palettes
# ─────────────────────────────────────────────────────────────────────────────

SKY_PALETTES = {
    'day':     [(135, 180, 235), (160, 200, 245), (100, 150, 210)],
    'evening': [(220, 130,  60), (180,  80,  50), (100,  60, 120)],
    'night':   [( 15,  20,  45), ( 25,  35,  70), ( 40,  55,  90)],
    'overcast':[(160, 165, 175), (180, 185, 195), (145, 150, 160)],
}

GROUND_PALETTES = {
    'concrete': [(100, 105, 110), (115, 120, 125), (90, 95, 100)],
    'grass':    [( 55, 110,  55), ( 70, 130,  65), ( 45,  90,  45)],
    'asphalt':  [( 45,  50,  55), ( 60,  65,  70), ( 35,  40,  45)],
    'indoor':   [(180, 165, 140), (165, 150, 125), (195, 180, 155)],
    'water':    [( 40,  90, 150), ( 55, 110, 170), ( 30,  70, 130)],
}

BUILDING_PALETTES = {
    'glass':     [(160, 190, 210), (140, 170, 195), (180, 205, 220)],
    'concrete':  [(140, 135, 130), (155, 150, 145), (125, 120, 115)],
    'brick':     [(160,  90,  70), (175, 105,  80), (145,  75,  60)],
    'modern':    [(200, 200, 210), (185, 185, 200), (215, 215, 225)],
    'industrial':[(100, 105,  95), (115, 120, 110), ( 90,  95,  85)],
}

ACCENT_COLORS = {
    'barrier_red':   (200,  60,  50),
    'accessible_green': (60, 170,  80),
    'warning_yellow':(240, 190,  40),
    'sign_blue':     ( 40,  90, 180),
    'highlight_cyan':( 40, 200, 210),
    'text_white':    (240, 240, 240),
    'shadow':        ( 30,  30,  35),
    'window_lit':    (255, 240, 180),
    'window_dark':   ( 60,  70,  90),
}


class SceneImageGenerator:
    def __init__(self, width=800, height=450, pixel_size=5):
        self.width = width
        self.height = height
        self.pixel_size = max(1, min(10, pixel_size))
        self.gw = width // pixel_size   # grid width  (160 @ px5)
        self.gh = height // pixel_size  # grid height  (90 @ px5)
        self.qwen_url = "http://vision-gateway:8080/v1/chat/completions"

    # ──────────────────────────────────────────────────────────────────────────
    # Qwen
    # ──────────────────────────────────────────────────────────────────────────

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
        except Exception:
            return None

    def _qwen_vision(self, png_data, prompt, timeout=90):
        b64 = base64.b64encode(png_data).decode()
        payload = json.dumps({
            "model": "qwen3.5:9b", "stream": False,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": "/no_think " + prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ]}],
        }).encode()
        try:
            req = urllib.request.Request(
                self.qwen_url, data=payload,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = json.loads(r.read())["choices"][0]["message"]["content"]
                return re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        except Exception:
            return None

    def _parse_json(self, text):
        if not text:
            return None
        text = re.sub(r'^```[a-z]*\n?', '', text.strip())
        text = re.sub(r'\n?```$', '', text.strip())
        try:
            return json.loads(text)
        except Exception:
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
        return None

    def get_scene_direction(self, content, title):
        """Ask Qwen which scene type + mood fits this article."""
        prompt = f"""Article title: {title}
Excerpt: {content[:400]}

Choose the best pixel-art scene to illustrate this disability/accessibility article.
Reply JSON only:
{{
  "scene": "transit_hub|urban_street|office_interior|theater|campus|library|open_air|data_center",
  "time": "day|evening|night|overcast",
  "ground": "concrete|grass|asphalt|indoor|water",
  "building_style": "glass|concrete|brick|modern|industrial",
  "accessibility_element": "missing_ramp|broken_elevator|no_captions|crowd_blocking|narrow_path|good_design|barrier_free",
  "captions": [
    "15-word caption for image 1 linking to article theme",
    "15-word caption for image 2",
    "15-word caption for image 3"
  ]
}}"""
        raw = self._qwen_text(prompt, timeout=60)
        return self._parse_json(raw)

    def validate_image(self, png_data, scene_type, title):
        """Qwen scores the rendered scene image."""
        prompt = f"""Rate this pixel-art scene (type: {scene_type}) for the article "{title}".
Score JSON only: {{"score": 1-10, "issue": "main problem", "fix": "one specific change"}}"""
        raw = self._qwen_vision(png_data, prompt, timeout=90)
        result = self._parse_json(raw)
        if result and isinstance(result.get('score'), (int, float)):
            return result
        return {"score": 7, "issue": "", "fix": ""}

    # ──────────────────────────────────────────────────────────────────────────
    # Artistic DNA
    # ──────────────────────────────────────────────────────────────────────────

    def _article_seed(self, slug):
        return int(hashlib.md5(slug.encode()).hexdigest()[:8], 16)

    def _tint_color(self, rgb, seed, image_index):
        """Apply article-specific tint shift for palette DNA."""
        angle = (seed + image_index * 30) % 360
        t = (math.sin(math.radians(angle)) * 12,
             math.sin(math.radians(angle + 120)) * 12,
             math.sin(math.radians(angle + 240)) * 12)
        return tuple(max(0, min(255, int(c + t[i]))) for i, c in enumerate(rgb))

    # ──────────────────────────────────────────────────────────────────────────
    # Grid helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _blank(self, fill=(0, 0, 0)):
        return [[fill for _ in range(self.gw)] for _ in range(self.gh)]

    def _set(self, grid, x, y, color):
        if 0 <= x < self.gw and 0 <= y < self.gh:
            grid[y][x] = color

    def _rect(self, grid, x1, y1, x2, y2, color, border=None):
        for y in range(max(0, y1), min(self.gh, y2)):
            for x in range(max(0, x1), min(self.gw, x2)):
                if border and (x == x1 or x == x2-1 or y == y1 or y == y2-1):
                    grid[y][x] = border
                else:
                    grid[y][x] = color

    def _hline(self, grid, y, x1, x2, color):
        for x in range(max(0, x1), min(self.gw, x2)):
            if 0 <= y < self.gh:
                grid[y][x] = color

    def _vline(self, grid, x, y1, y2, color):
        for y in range(max(0, y1), min(self.gh, y2)):
            if 0 <= x < self.gw:
                grid[y][x] = color

    def _circle(self, grid, cx, cy, r, color):
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                if dx*dx + dy*dy <= r*r:
                    self._set(grid, cx+dx, cy+dy, color)

    def _gradient_sky(self, grid, horizon_y, top_col, horizon_col):
        for y in range(min(horizon_y, self.gh)):
            t = y / max(1, horizon_y)
            color = tuple(int(top_col[i] + (horizon_col[i] - top_col[i]) * t) for i in range(3))
            for x in range(self.gw):
                grid[y][x] = color

    # ──────────────────────────────────────────────────────────────────────────
    # Scene components
    # ──────────────────────────────────────────────────────────────────────────

    def _draw_building(self, grid, x, y_base, w, h, wall_col, window_col, lit_col):
        """Draw a building from y_base upward."""
        self._rect(grid, x, y_base - h, x + w, y_base, wall_col)
        # Windows in rows/columns
        win_spacing_x = max(2, w // 4)
        win_spacing_y = max(2, 4)
        for wy in range(y_base - h + 2, y_base - 1, win_spacing_y):
            for wx in range(x + 1, x + w - 1, win_spacing_x):
                c = lit_col if random.random() > 0.3 else window_col
                self._rect(grid, wx, wy, wx+2, wy+2, c)

    def _draw_tree(self, grid, x, ground_y, trunk_col, foliage_col):
        h_trunk = random.randint(3, 6)
        self._vline(grid, x, ground_y - h_trunk, ground_y, trunk_col)
        r = random.randint(3, 5)
        self._circle(grid, x, ground_y - h_trunk - r, r, foliage_col)

    def _draw_person(self, grid, x, ground_y, color, has_cane=False, in_chair=False):
        if in_chair:
            # Wheelchair silhouette
            self._set(grid, x, ground_y - 4, color)       # head
            self._rect(grid, x-1, ground_y-3, x+2, ground_y-1, color)  # body
            self._hline(grid, ground_y, x-2, x+3, color)  # wheels base
            self._set(grid, x-2, ground_y, ACCENT_COLORS['warning_yellow'])
            self._set(grid, x+2, ground_y, ACCENT_COLORS['warning_yellow'])
        else:
            self._set(grid, x, ground_y - 5, color)       # head
            self._vline(grid, x, ground_y - 4, ground_y, color)  # body/legs
            if has_cane:
                self._vline(grid, x+1, ground_y - 3, ground_y + 1, (200, 200, 200))

    def _draw_vehicle(self, grid, x, ground_y, vtype='bus'):
        if vtype == 'bus':
            w, h = 20, 8
            body = (200, 80, 50)
            self._rect(grid, x, ground_y - h, x + w, ground_y, body,
                       border=ACCENT_COLORS['shadow'])
            # Windows
            for wx in range(x+2, x+w-1, 4):
                self._rect(grid, wx, ground_y-h+1, wx+3, ground_y-3,
                           ACCENT_COLORS['window_lit'])
            # Wheels
            self._circle(grid, x+3, ground_y, 2, (40, 40, 40))
            self._circle(grid, x+w-3, ground_y, 2, (40, 40, 40))
            # Accessibility ramp indicator
            self._set(grid, x+w//2, ground_y-1, ACCENT_COLORS['accessible_green'])

        elif vtype == 'tram':
            w, h = 28, 9
            body = (60, 120, 200)
            self._rect(grid, x, ground_y - h, x + w, ground_y - 1, body,
                       border=ACCENT_COLORS['shadow'])
            # Windshield
            self._rect(grid, x+1, ground_y-h+1, x+5, ground_y-3,
                       ACCENT_COLORS['window_lit'])
            # Windows
            for wx in range(x+6, x+w-3, 5):
                self._rect(grid, wx, ground_y-h+1, wx+4, ground_y-3,
                           ACCENT_COLORS['window_lit'])
            # Rail
            self._hline(grid, ground_y - 1, x - 3, x + w + 3, (80, 80, 80))
            # Pantograph
            self._vline(grid, x+w//2, ground_y-h-3, ground_y-h, (160, 160, 160))

        elif vtype == 'car':
            w, h = 12, 5
            body_col = (random.randint(100, 220), random.randint(80, 200), random.randint(80, 200))
            self._rect(grid, x, ground_y - h, x + w, ground_y, body_col)
            self._rect(grid, x+2, ground_y-h-2, x+w-2, ground_y-h, body_col)
            self._rect(grid, x+3, ground_y-h-1, x+w-3, ground_y-h,
                       ACCENT_COLORS['window_lit'])
            self._circle(grid, x+2, ground_y, 2, (30, 30, 30))
            self._circle(grid, x+w-2, ground_y, 2, (30, 30, 30))

    def _draw_sign(self, grid, x, y, text_col, bg_col, has_braille=False):
        self._rect(grid, x, y, x+8, y+4, bg_col, border=text_col)
        if has_braille:
            for bx in range(x+1, x+7, 2):
                self._set(grid, bx, y+2, ACCENT_COLORS['text_white'])

    def _draw_stairs_vs_ramp(self, grid, x, ground_y, accessible=True, w=15):
        if accessible:
            # Ramp — gentle slope
            for dx in range(w):
                ry = ground_y - (dx * 4 // w)
                self._set(grid, x + dx, ry, ACCENT_COLORS['accessible_green'])
                self._set(grid, x + dx, ry + 1, ACCENT_COLORS['concrete'][0]
                          if False else (120, 125, 130))
        else:
            # Stairs — blocky
            step_w = max(1, w // 5)
            for step in range(5):
                sx = x + step * step_w
                sy = ground_y - step
                self._rect(grid, sx, sy, sx + step_w, sy + 1,
                           ACCENT_COLORS['barrier_red'])

    def _draw_info_board(self, grid, x, y, has_visual=True, has_audio=True):
        """Digital information board — shows whether visual/audio access exists."""
        self._rect(grid, x, y, x+12, y+7, (20, 20, 30), border=(60, 60, 80))
        if has_visual:
            self._rect(grid, x+1, y+1, x+11, y+5, (40, 100, 180))
            # Text lines
            for ly in range(y+2, y+5, 1):
                self._hline(grid, ly, x+2, x+10, ACCENT_COLORS['text_white'])
        else:
            # X mark — no visual info
            self._set(grid, x+3, y+2, ACCENT_COLORS['barrier_red'])
            self._set(grid, x+8, y+5, ACCENT_COLORS['barrier_red'])
        if not has_audio:
            # Red indicator at bottom
            self._hline(grid, y+6, x+1, x+11, ACCENT_COLORS['barrier_red'])

    def _draw_acoustic_panels(self, grid, x, y, w, h, color=(140, 130, 120)):
        """Acoustic treatment panels on wall."""
        for py in range(y, y + h, 3):
            self._rect(grid, x, py, x + w, py + 2, color,
                       border=tuple(max(0, c - 20) for c in color))

    def _add_clouds(self, grid, horizon_y):
        for _ in range(random.randint(2, 5)):
            cx = random.randint(5, self.gw - 10)
            cy = random.randint(2, max(3, horizon_y // 3))
            cw = random.randint(8, 18)
            for bx in range(cx, cx + cw, 6):
                r = random.randint(2, 4)
                self._circle(grid, bx, cy, r, (240, 242, 245))

    # ──────────────────────────────────────────────────────────────────────────
    # Scene renderers
    # ──────────────────────────────────────────────────────────────────────────

    def _scene_transit_hub(self, grid, params, a11y):
        """Train/bus station — platform, vehicles, information boards."""
        sky_cols = SKY_PALETTES[params['time']]
        horizon_y = int(self.gh * 0.55)
        self._gradient_sky(grid, horizon_y, sky_cols[0], sky_cols[1])

        # Platform / ceiling structure
        ceil_col = (110, 105, 100)
        self._rect(grid, 0, 0, self.gw, 8, ceil_col)
        # Ceiling beams
        for bx in range(0, self.gw, 20):
            self._vline(grid, bx, 0, horizon_y - 5, (90, 85, 80))

        # Platform ground
        ground_col = (140, 138, 135)
        self._rect(grid, 0, horizon_y - 5, self.gw, self.gh, ground_col)
        # Platform edge stripe
        self._hline(grid, horizon_y - 5, 0, self.gw, ACCENT_COLORS['warning_yellow'])

        # Train/tram
        tx = random.randint(5, 25)
        self._draw_vehicle(grid, tx, horizon_y - 6, 'tram')

        # Bus in background
        if random.random() > 0.5:
            self._draw_vehicle(grid, self.gw - 35, horizon_y - 5, 'bus')

        # Information boards
        for bx in [self.gw // 4, self.gw // 2, 3 * self.gw // 4]:
            has_v = a11y != 'no_captions'
            has_a = a11y != 'no_audio'
            self._draw_info_board(grid, bx - 6, 9, has_visual=has_v, has_audio=has_a)

        # Accessibility element
        if a11y == 'missing_ramp':
            self._draw_stairs_vs_ramp(grid, tx + 30, horizon_y - 5, accessible=False)
        elif a11y == 'barrier_free':
            self._draw_stairs_vs_ramp(grid, tx + 30, horizon_y - 5, accessible=True)

        # People
        for _ in range(random.randint(3, 7)):
            px = random.randint(5, self.gw - 5)
            in_chair = random.random() < 0.2
            has_cane = random.random() < 0.15
            self._draw_person(grid, px, horizon_y - 6,
                              (random.randint(50, 200),) * 3, has_cane, in_chair)

        # Signs
        for sx in range(15, self.gw - 10, 30):
            self._draw_sign(grid, sx, 10, ACCENT_COLORS['text_white'],
                            ACCENT_COLORS['sign_blue'], has_braille=(a11y == 'barrier_free'))

    def _scene_urban_street(self, grid, params, a11y):
        """City street — buildings, road, vehicles, pedestrians."""
        sky_cols = SKY_PALETTES[params['time']]
        horizon_y = int(self.gh * 0.45)
        self._gradient_sky(grid, horizon_y, sky_cols[0], sky_cols[1])
        if params['time'] == 'day':
            self._add_clouds(grid, horizon_y)

        # Road
        road_col = (55, 58, 62)
        self._rect(grid, 0, horizon_y, self.gw, self.gh, road_col)
        # Road markings
        for mx in range(5, self.gw - 5, 12):
            self._rect(grid, mx, int(self.gh * 0.7), mx + 6, int(self.gh * 0.7) + 2,
                       (220, 220, 180))

        # Sidewalks
        sw_col = (120, 118, 115)
        self._rect(grid, 0, horizon_y, self.gw, horizon_y + 4, sw_col)
        self._rect(grid, 0, self.gh - 6, self.gw, self.gh, sw_col)

        # Buildings (background)
        b_styles = BUILDING_PALETTES[params['building_style']]
        x = 0
        while x < self.gw:
            bw = random.randint(12, 22)
            bh = random.randint(int(self.gh * 0.25), int(self.gh * 0.6))
            wall = self._tinted(b_styles[0], random.randint(-10, 10))
            win = ACCENT_COLORS['window_dark'] if params['time'] == 'night' else (180, 200, 220)
            lit = ACCENT_COLORS['window_lit']
            self._draw_building(grid, x, horizon_y, bw, bh, wall, win, lit)
            x += bw + random.randint(0, 3)

        # Vehicles on road
        for _ in range(random.randint(1, 3)):
            vx = random.randint(0, self.gw - 25)
            vy = random.randint(horizon_y + 8, self.gh - 8)
            vt = random.choice(['car', 'bus'])
            self._draw_vehicle(grid, vx, vy, vt)

        # Accessibility: kerb cut / no kerb cut
        for cx in range(10, self.gw - 10, 30):
            if a11y in ('missing_ramp', 'narrow_path'):
                self._rect(grid, cx, horizon_y + 2, cx + 4, horizon_y + 4,
                           ACCENT_COLORS['barrier_red'])
            else:
                self._draw_stairs_vs_ramp(grid, cx, horizon_y + 4, accessible=True, w=5)

        # Trees
        trunk = (90, 60, 40)
        foliage = (55, 130, 55) if params['time'] != 'evening' else (40, 100, 40)
        for tx in range(8, self.gw - 8, 18):
            self._draw_tree(grid, tx, horizon_y + 4, trunk, foliage)

        # People
        for _ in range(random.randint(2, 5)):
            px = random.randint(2, self.gw - 2)
            in_chair = random.random() < 0.2
            col = (random.randint(60, 200),) * 3
            self._draw_person(grid, px, horizon_y + 3, col,
                              has_cane=random.random() < 0.1, in_chair=in_chair)

    def _scene_office_interior(self, grid, params, a11y):
        """Open-plan office — desks, windows, acoustic panels."""
        # Floor
        floor_col = (165, 152, 138)
        self._rect(grid, 0, 0, self.gw, self.gh, floor_col)

        # Ceiling
        ceil = (200, 198, 196)
        self._rect(grid, 0, 0, self.gw, 6, ceil)
        # Ceiling grid
        for gx in range(0, self.gw, 8):
            self._vline(grid, gx, 0, 6, (160, 158, 156))
        for gy in range(0, 6, 4):
            self._hline(grid, gy, 0, self.gw, (160, 158, 156))

        # Back wall with windows
        wall = (180, 175, 170)
        self._rect(grid, 0, 6, self.gw, int(self.gh * 0.45), wall)
        win_col = (160, 200, 230) if params['time'] == 'day' else (60, 70, 90)
        for wx in range(5, self.gw - 10, 18):
            self._rect(grid, wx, 8, wx + 12, int(self.gh * 0.42), win_col,
                       border=(140, 138, 135))

        # Acoustic panels
        if a11y == 'no_captions':
            # No acoustic treatment → echo hell
            pass
        else:
            for ax in range(0, self.gw, 20):
                self._draw_acoustic_panels(grid, ax, 6, 4, int(self.gh * 0.3))

        # Desks
        desk_y = int(self.gh * 0.55)
        desk_col = (210, 200, 185)
        for dx in range(0, self.gw - 15, 20):
            self._rect(grid, dx + 2, desk_y, dx + 14, desk_y + 3, desk_col,
                       border=(170, 160, 145))
            # Monitor
            self._rect(grid, dx + 4, desk_y - 5, dx + 9, desk_y, (30, 30, 35),
                       border=(50, 50, 55))
            self._rect(grid, dx + 5, desk_y - 4, dx + 8, desk_y - 1, (80, 130, 200))
            # Person
            if random.random() > 0.3:
                in_chair = random.random() < 0.15
                self._draw_person(grid, dx + 6, desk_y - 1, (120, 110, 100),
                                  in_chair=in_chair)

        # Floor detail
        for fy in range(int(self.gh * 0.85), self.gh, 4):
            self._hline(grid, fy, 0, self.gw, tuple(max(0, c - 15) for c in floor_col))

    def _scene_theater(self, grid, params, a11y):
        """Theater/cinema — screen, seats, caption overlay, stage."""
        # Dark interior
        bg = (25, 20, 30)
        self._rect(grid, 0, 0, self.gw, self.gh, bg)

        # Stage/screen
        screen_col = (200, 200, 195) if params['time'] in ('day', 'overcast') else (40, 60, 100)
        screen_x1, screen_y1 = int(self.gw * 0.1), int(self.gh * 0.05)
        screen_x2, screen_y2 = int(self.gw * 0.9), int(self.gh * 0.5)
        self._rect(grid, screen_x1, screen_y1, screen_x2, screen_y2, screen_col,
                   border=(100, 90, 80))
        # Screen content suggestion
        for sx in range(screen_x1 + 3, screen_x2 - 3, 8):
            sy = random.randint(screen_y1 + 3, screen_y2 - 6)
            self._circle(grid, sx, sy, random.randint(2, 4), (180, 160, 200))

        # Caption bar at bottom of screen
        if a11y == 'no_captions':
            # Black bar — no captions
            self._rect(grid, screen_x1, screen_y2 - 6, screen_x2, screen_y2,
                       (10, 10, 10))
        else:
            # Caption bar with text indication
            self._rect(grid, screen_x1, screen_y2 - 6, screen_x2, screen_y2,
                       (20, 20, 20))
            for tx in range(screen_x1 + 4, screen_x2 - 4, 6):
                self._hline(grid, screen_y2 - 3, tx, tx + 4,
                            ACCENT_COLORS['text_white'])

        # Seating rows
        seat_start = screen_y2 + 3
        row_h = 5
        for row in range((self.gh - seat_start) // row_h):
            ry = seat_start + row * row_h
            indent = row * 2  # perspective
            seat_col = (80, 40, 60)
            for sx in range(indent, self.gw - indent, 4):
                self._rect(grid, sx, ry, sx + 3, ry + 3, seat_col)

        # Wheelchair spaces at ends of rows
        if a11y in ('barrier_free', 'good_design'):
            for row in range((self.gh - seat_start) // row_h):
                ry = seat_start + row * row_h
                self._draw_person(grid, 2, ry + 2, (150, 150, 150), in_chair=True)

        # Side aisle lighting
        for ay in range(seat_start, self.gh, 3):
            self._set(grid, 1, ay, ACCENT_COLORS['warning_yellow'])
            self._set(grid, self.gw - 2, ay, ACCENT_COLORS['warning_yellow'])

    def _scene_campus(self, grid, params, a11y):
        """Campus / outdoor plaza — buildings, paths, greenery."""
        sky_cols = SKY_PALETTES[params['time']]
        horizon_y = int(self.gh * 0.4)
        self._gradient_sky(grid, horizon_y, sky_cols[0], sky_cols[1])
        if params['time'] == 'day':
            self._add_clouds(grid, horizon_y)

        # Ground
        ground = GROUND_PALETTES[params.get('ground', 'grass')]
        self._rect(grid, 0, horizon_y, self.gw, self.gh, ground[0])

        # Path
        path_col = (170, 162, 150)
        path_y = int(self.gh * 0.65)
        self._rect(grid, 0, path_y, self.gw, path_y + 8, path_col)

        # Buildings
        b_col = BUILDING_PALETTES[params['building_style']][0]
        for bx in [5, self.gw // 2 - 15, self.gw - 30]:
            bw = random.randint(20, 28)
            bh = random.randint(int(self.gh * 0.3), int(self.gh * 0.55))
            win = (160, 190, 210)
            lit = ACCENT_COLORS['window_lit']
            self._draw_building(grid, bx, horizon_y + 2, bw, bh, b_col, win, lit)

        # Trees (campus has lots of trees)
        trunk = (90, 65, 40)
        foliage = (55, 130, 55) if params['time'] != 'evening' else (40, 95, 40)
        for tx in range(0, self.gw, 12):
            if random.random() > 0.4:
                self._draw_tree(grid, tx, horizon_y + 2, trunk, foliage)

        # Accessibility: ramps / steps to buildings
        for bx in [5, self.gw // 2 - 15, self.gw - 30]:
            self._draw_stairs_vs_ramp(grid, bx + 5, path_y,
                                      accessible=(a11y != 'missing_ramp'))

        # People on path
        for _ in range(random.randint(3, 6)):
            px = random.randint(5, self.gw - 5)
            in_chair = random.random() < 0.18
            col = tuple(random.randint(60, 200) for _ in range(3))
            self._draw_person(grid, px, path_y + 7, col,
                              has_cane=random.random() < 0.1, in_chair=in_chair)

    def _scene_library(self, grid, params, a11y):
        """Library interior — shelves, reading area, natural light."""
        # Floor and walls
        floor = (180, 162, 140)
        self._rect(grid, 0, 0, self.gw, self.gh, floor)
        wall = (210, 195, 175)
        self._rect(grid, 0, 0, self.gw, int(self.gh * 0.45), wall)

        # Windows (natural light)
        win_col = (180, 215, 240) if params['time'] == 'day' else (30, 40, 60)
        for wx in range(8, self.gw - 8, 25):
            self._rect(grid, wx, 2, wx + 14, int(self.gh * 0.42), win_col,
                       border=(140, 130, 118))
            if params['time'] == 'day':
                # Light cast on floor
                for lx in range(wx, wx + 14):
                    ly = int(self.gh * 0.45)
                    while ly < self.gh - 2 and random.random() > 0.1:
                        c = grid[ly][lx]
                        grid[ly][lx] = tuple(min(255, int(cv * 1.08)) for cv in c)
                        ly += 1

        # Bookshelves
        shelf_col = (110, 85, 60)
        book_colors = [(180, 60, 60), (60, 100, 180), (60, 150, 80),
                       (200, 160, 40), (140, 60, 160)]
        for sx in range(0, self.gw, 20):
            shelf_top = int(self.gh * 0.48)
            self._rect(grid, sx, shelf_top, sx + 18, self.gh - 12, shelf_col)
            for by in range(shelf_top + 1, self.gh - 13, 7):
                for bx in range(sx + 1, sx + 18, 2):
                    bc = random.choice(book_colors)
                    self._vline(grid, bx, by, by + 6, bc)

        # Reading tables
        table_y = int(self.gh * 0.7)
        for tx in range(5, self.gw - 15, 22):
            self._rect(grid, tx, table_y, tx + 16, table_y + 3, (195, 175, 150))
            if random.random() > 0.4:
                in_chair = random.random() < 0.1
                self._draw_person(grid, tx + 6, table_y, (120, 110, 100),
                                  in_chair=in_chair)

    def _scene_open_air(self, grid, params, a11y):
        """Outdoor open space — sky, landscape, accessible path."""
        sky_cols = SKY_PALETTES[params['time']]
        horizon_y = int(self.gh * 0.5)
        self._gradient_sky(grid, horizon_y, sky_cols[0], sky_cols[1])
        if params['time'] == 'day':
            # Sun
            self._circle(grid, int(self.gw * 0.8), int(self.gh * 0.1), 4,
                         (255, 240, 100))
            self._add_clouds(grid, horizon_y)

        # Ground
        ground = GROUND_PALETTES[params.get('ground', 'grass')]
        self._rect(grid, 0, horizon_y, self.gw, self.gh, ground[0])
        # Ground texture
        for gy in range(horizon_y, self.gh, 3):
            for gx in range(0, self.gw, 4):
                if random.random() > 0.7:
                    self._set(grid, gx, gy, ground[1])

        # Path
        path_y = int(self.gh * 0.75)
        path_col = (160, 155, 148) if a11y != 'narrow_path' else (100, 100, 100)
        path_w = 20 if a11y != 'narrow_path' else 6
        self._rect(grid, self.gw // 2 - path_w // 2, path_y,
                   self.gw // 2 + path_w // 2, self.gh, path_col)

        # Trees
        trunk = (90, 65, 40)
        foliage = (55, 130, 55)
        for _ in range(random.randint(4, 8)):
            tx = random.randint(5, self.gw - 5)
            ty = random.randint(horizon_y - 5, horizon_y + 5)
            self._draw_tree(grid, tx, ty, trunk, foliage)

        # Background hills
        for hx in range(0, self.gw, 2):
            hy = int(horizon_y - 8 * math.sin(hx * 0.05) - 5)
            self._set(grid, hx, max(0, hy),
                      (75, 135, 75) if params['time'] != 'evening' else (55, 95, 55))

        # People
        for _ in range(random.randint(1, 4)):
            px = random.randint(5, self.gw - 5)
            in_chair = random.random() < 0.25
            col = tuple(random.randint(60, 200) for _ in range(3))
            self._draw_person(grid, px, path_y + 6, col, in_chair=in_chair)

    def _scene_data_center(self, grid, params, a11y):
        """Abstract tech / data center — dark, glowing panels, data flows."""
        bg = (12, 15, 22)
        self._rect(grid, 0, 0, self.gw, self.gh, bg)

        # Server rack rows
        rack_col = (40, 45, 55)
        for rx in range(0, self.gw, 18):
            rh = random.randint(int(self.gh * 0.4), int(self.gh * 0.8))
            self._rect(grid, rx + 1, self.gh - rh, rx + 15, self.gh, rack_col,
                       border=(60, 65, 80))
            # LED indicators
            for ly in range(self.gh - rh + 2, self.gh - 2, 4):
                led = random.choice([
                    (60, 220, 80), (220, 60, 60), (60, 120, 220), (220, 180, 40)])
                self._set(grid, rx + 2, ly, led)
                self._set(grid, rx + 3, ly, led)

        # Data flow lines
        flow_col = ACCENT_COLORS['highlight_cyan']
        for _ in range(random.randint(5, 12)):
            fy = random.randint(5, self.gh - 10)
            fx_start = random.randint(0, self.gw // 2)
            fx_end = random.randint(self.gw // 2, self.gw)
            self._hline(grid, fy, fx_start, fx_end, flow_col)
            # Pulse dots
            for fx in range(fx_start, fx_end, random.randint(4, 10)):
                self._circle(grid, fx, fy, 1, (180, 240, 255))

        # Accessibility: screen reader overlay
        if a11y in ('no_captions', 'missing_ramp'):
            # Screen with X - inaccessible interface
            sx, sy = int(self.gw * 0.6), int(self.gh * 0.1)
            self._rect(grid, sx, sy, sx + 20, sy + 14, (30, 30, 40),
                       border=ACCENT_COLORS['barrier_red'])
        else:
            sx, sy = int(self.gw * 0.6), int(self.gh * 0.1)
            self._rect(grid, sx, sy, sx + 20, sy + 14, (30, 30, 40),
                       border=ACCENT_COLORS['accessible_green'])
            for ty in range(sy + 2, sy + 12, 3):
                self._hline(grid, ty, sx + 2, sx + 18,
                            ACCENT_COLORS['text_white'])

    # ──────────────────────────────────────────────────────────────────────────
    # Scene dispatcher
    # ──────────────────────────────────────────────────────────────────────────

    SCENE_MAP = {
        'transit_hub':    '_scene_transit_hub',
        'urban_street':   '_scene_urban_street',
        'office_interior':'_scene_office_interior',
        'theater':        '_scene_theater',
        'campus':         '_scene_campus',
        'library':        '_scene_library',
        'open_air':       '_scene_open_air',
        'data_center':    '_scene_data_center',
    }

    def _render_scene(self, scene_type, params, a11y, image_index, slug):
        """Render scene with per-image variation."""
        seed = self._article_seed(slug) + image_index * 1000
        random.seed(seed + hash(scene_type) + (id(params) % 10000))

        params = dict(params)
        params.setdefault('time', 'day')
        params.setdefault('ground', 'concrete')
        params.setdefault('building_style', 'modern')

        # image_index=0: primary view, 1: different angle/time, 2: solution view
        if image_index == 1:
            params['time'] = {'day': 'evening', 'evening': 'night',
                              'night': 'day', 'overcast': 'day'}.get(
                params['time'], 'day')
        elif image_index == 2:
            a11y = 'barrier_free' if a11y in ('missing_ramp', 'broken_elevator',
                                              'no_captions', 'narrow_path') else a11y

        grid = self._blank()
        renderer_name = self.SCENE_MAP.get(scene_type, '_scene_urban_street')
        renderer = getattr(self, renderer_name)
        try:
            renderer(grid, params, a11y)
        except Exception as exc:
            logger.warning("Scene %s failed (%s), falling back to urban_street", scene_type, exc)
            grid = self._blank()
            try:
                self._scene_urban_street(grid, params, a11y)
            except Exception as exc2:
                logger.warning("Fallback urban_street also failed (%s), using blank grid", exc2)

        # Apply article tint DNA to whole image
        art_seed = self._article_seed(slug)
        for y in range(self.gh):
            for x in range(self.gw):
                grid[y][x] = self._tint_color(grid[y][x], art_seed, image_index)

        return self._grid_to_png(grid)

    def _tinted(self, color, offset):
        return tuple(max(0, min(255, c + offset)) for c in color)

    # ──────────────────────────────────────────────────────────────────────────
    # Main entry point
    # ──────────────────────────────────────────────────────────────────────────

    def generate_content_aware_images(self, content, title, slug, num_images=3, validate=True):
        """Generate num_images scene-based PNG images. Always returns a list; never raises.

        Args:
            validate: When True, Qwen vision-scores each image and re-renders if score<6.
                      Set False for automated cron runs to skip the 20-90s validation overhead.
        """
        _fallback_params = {'time': 'day', 'ground': 'concrete', 'building_style': 'modern'}
        _fallback_scene = 'urban_street'

        try:
            direction = self.get_scene_direction(content, title)

            if direction:
                scene_type = direction.get('scene', _fallback_scene)
                params = {
                    'time': direction.get('time', 'day'),
                    'ground': direction.get('ground', 'concrete'),
                    'building_style': direction.get('building_style', 'modern'),
                }
                a11y = direction.get('accessibility_element', 'missing_ramp')
                captions = direction.get('captions', [])
            else:
                scene_type = self._infer_scene(content + ' ' + title)
                params = dict(_fallback_params)
                a11y = 'missing_ramp'
                captions = []

            images = []
            for i in range(min(num_images, 3)):
                try:
                    png_data = self._render_scene(scene_type, params, a11y, i, slug)

                    if validate:
                        eval_r = self.validate_image(png_data, scene_type, title)
                        if eval_r.get('score', 7) < 6:
                            random.seed(self._article_seed(slug) + i * 1000 + 9999)
                            png_data = self._render_scene(scene_type, params, a11y, i, slug + '_v2')
                    else:
                        eval_r = {'score': 7, 'issue': '', 'fix': ''}

                    caption = captions[i] if i < len(captions) else \
                        f"{'Concept' if i==0 else 'Context' if i==1 else 'Solution'}: " \
                        f"{scene_type.replace('_', ' ')} — disability accessibility perspective"

                    suffix = ['concept', 'context', 'solution'][i]
                    images.append({
                        'data': png_data,
                        'filename': f"{slug}_{suffix}_{i+1}.png",
                        'description': caption,
                        'score': eval_r.get('score', 7),
                        'scene': scene_type,
                    })
                except Exception as exc:
                    logger.warning("Image %d generation failed (%s), using emergency render", i, exc)
                    try:
                        png_data = self._render_scene(_fallback_scene, _fallback_params,
                                                      'missing_ramp', i, slug + f'_emer{i}')
                    except Exception:
                        png_data = self._emergency_png()
                    suffix = ['concept', 'context', 'solution'][i]
                    images.append({
                        'data': png_data,
                        'filename': f"{slug}_{suffix}_{i+1}.png",
                        'description': f"Scene {i+1} — {title}",
                        'score': 5,
                        'scene': _fallback_scene,
                    })

            # Pad to requested count if any images are still missing
            while len(images) < min(num_images, 3):
                i = len(images)
                try:
                    png_data = self._render_scene(_fallback_scene, _fallback_params,
                                                  'missing_ramp', i, slug + f'_pad{i}')
                except Exception:
                    png_data = self._emergency_png()
                suffix = ['concept', 'context', 'solution'][i]
                images.append({
                    'data': png_data,
                    'filename': f"{slug}_{suffix}_{i+1}.png",
                    'description': f"Scene {i+1} — {title}",
                    'score': 5,
                    'scene': _fallback_scene,
                })

            return images

        except Exception as exc:
            logger.error("generate_content_aware_images catastrophic failure (%s)", exc)
            images = []
            for i in range(min(num_images, 3)):
                suffix = ['concept', 'context', 'solution'][i]
                images.append({
                    'data': self._emergency_png(),
                    'filename': f"{slug}_{suffix}_{i+1}.png",
                    'description': f"Scene {i+1} — {title}",
                    'score': 5,
                    'scene': 'urban_street',
                })
            return images

    def _infer_scene(self, text):
        text = text.lower()
        if any(w in text for w in ['station', 'train', 'tram', 'bus', 'transit', 'transport']):
            return 'transit_hub'
        if any(w in text for w in ['street', 'road', 'sidewalk', 'curb', 'urban']):
            return 'urban_street'
        if any(w in text for w in ['office', 'workplace', 'desk', 'meeting', 'corporate']):
            return 'office_interior'
        if any(w in text for w in ['theater', 'cinema', 'film', 'movie', 'stage', 'oscar']):
            return 'theater'
        if any(w in text for w in ['campus', 'university', 'school', 'college']):
            return 'campus'
        if any(w in text for w in ['library', 'book', 'reading', 'archive']):
            return 'library'
        if any(w in text for w in ['tech', 'data', 'digital', 'interface', 'app', 'software']):
            return 'data_center'
        return 'open_air'

    # ──────────────────────────────────────────────────────────────────────────
    # PNG encoding
    # ──────────────────────────────────────────────────────────────────────────

    def _emergency_png(self):
        """Minimal valid 1x1 black PNG for catastrophic fallback."""
        grid = self._blank((0, 0, 0))
        return self._grid_to_png(grid)

    def _grid_to_png(self, grid):
        """Scale grid cells to pixel_size and encode as PNG."""
        raw = b''
        for gy in range(self.gh):
            for _ in range(self.pixel_size):  # repeat each row pixel_size times
                raw += b'\x00'  # filter byte
                for gx in range(self.gw):
                    cell = grid[gy][gx]
                    if not isinstance(cell, (tuple, list)) or len(cell) < 3:
                        cell = (0, 0, 0)
                    r = max(0, min(255, int(cell[0])))
                    g = max(0, min(255, int(cell[1])))
                    b = max(0, min(255, int(cell[2])))
                    raw += bytes([r, g, b]) * self.pixel_size  # repeat each column
        compressed = zlib.compress(raw)

        width = self.gw * self.pixel_size
        height = self.gh * self.pixel_size

        png = b'\x89PNG\r\n\x1a\n'

        ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
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
    import sys
    content = "I'm standing at Union Station. The departure board flickers. I'm deaf and this hub ignores deaf users. No visual alerts, no captions on the screens, no tactile indicators at the platform edge."
    title = "The Station That Forgot Deaf Users"
    gen = SceneImageGenerator()
    logger.info("Querying Qwen for scene direction...")
    direction = gen.get_scene_direction(content, title)
    logger.info("Direction: %s", direction)
    logger.info("Rendering scenes...")
    imgs = gen.generate_content_aware_images(content, title, "test-station", 3)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    for img in imgs:
        p = Path(f"/tmp/{img['filename']}")
        p.write_bytes(img['data'])
        valid = img['data'][:4] == b'\x89PNG'
        logger.info("  %s  %d bytes  PNG:%s  scene:%s  score:%s",
                    img['filename'], len(img['data']), valid, img['scene'], img.get('score','?'))
        logger.info("  Caption: %s", img['description'])
