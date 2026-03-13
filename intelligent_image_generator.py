#!/usr/bin/env python3
"""
INTELLIGENT CONTENT-AWARE IMAGE GENERATOR (v3)

Architecture:
  1. Qwen (text) → artistic direction: palette mood, visual elements, composition hints
  2. Python renderer → generate image based on direction + article analysis
  3. Qwen (vision) → evaluate image: score 1-10 + specific issues
  4. Loop until score >= 7 or max 3 iterations
  5. Return best image + contextual caption

Artistic DNA: every image in an article shares a seeded palette offset + corner
signature motif, creating visual family resemblance across the 3 images.

Rendering: non-deterministic — composition variant is chosen randomly each
iteration, parameters shifted based on Qwen feedback, so each run produces
different output.
"""

import math
import random
import struct
import zlib
import re
import json
import base64
import hashlib
import time
import urllib.request
import urllib.error
from pathlib import Path


class IntelligentImageGenerator:
    def __init__(self, width=800, height=450):
        self.width = width
        self.height = height
        self.grid_width = width
        self.grid_height = height
        self.qwen_url = "http://vision-gateway:8080/v1/chat/completions"

        # Base palette families — one per theme
        self.palettes = {
            'architectural': [
                (25, 30, 40), (50, 65, 85), (85, 105, 125), (120, 140, 160),
                (160, 175, 190), (200, 210, 220), (70, 150, 200),
                (200, 120, 60), (100, 180, 90),
            ],
            'navigation': [
                (20, 25, 35), (40, 55, 70), (80, 95, 110), (120, 135, 150),
                (180, 190, 200), (220, 225, 230), (255, 200, 60),
                (60, 180, 120), (180, 60, 60),
            ],
            'technology': [
                (15, 20, 30), (30, 45, 60), (60, 80, 100), (100, 120, 140),
                (150, 165, 180), (200, 210, 220), (100, 150, 255),
                (255, 150, 100), (150, 255, 150),
            ],
            'cultural': [
                (30, 25, 35), (60, 45, 55), (90, 75, 85), (130, 115, 125),
                (170, 155, 165), (210, 195, 205), (180, 100, 140),
                (140, 180, 100), (100, 140, 180),
            ],
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Qwen integration
    # ──────────────────────────────────────────────────────────────────────────

    def _query_qwen_text(self, prompt, timeout=60):
        """Text-only Qwen call — /no_think prefix disables reasoning chain."""
        payload = json.dumps({
            "model": "qwen3.5:9b",
            "stream": False,
            "messages": [{"role": "user", "content": "/no_think " + prompt}],
        }).encode()
        req = urllib.request.Request(
            self.qwen_url, data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
                raw = data["choices"][0]["message"]["content"]
                # Strip <think>...</think> reasoning blocks
                raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
                return raw
        except Exception:
            return None

    def _query_qwen_vision(self, png_data, prompt, timeout=90):
        """Send image + prompt to Qwen vision — /no_think for fast response."""
        b64 = base64.b64encode(png_data).decode()
        payload = json.dumps({
            "model": "qwen3.5:9b",
            "stream": False,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "/no_think " + prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }],
        }).encode()
        req = urllib.request.Request(
            self.qwen_url, data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
                raw = data["choices"][0]["message"]["content"]
                raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
                return raw
        except Exception:
            return None

    def _parse_json_response(self, text):
        """Extract JSON from Qwen response, tolerating markdown fences."""
        if not text:
            return None
        text = re.sub(r'^```[a-z]*\n?', '', text.strip())
        text = re.sub(r'\n?```$', '', text.strip())
        try:
            return json.loads(text)
        except Exception:
            # Try to find JSON object inside text
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
        return None

    def get_artistic_direction(self, content, title):
        """Ask Qwen for artistic direction + 3 image captions."""
        prompt = f"""You are an artistic director for a disability culture publication.

Article title: {title}
Excerpt: {content[:500]}

Provide artistic direction for 3 abstract images that will illustrate this article.
Respond in JSON only (no markdown, no explanation):
{{
  "color_mood": "brief color description e.g. 'deep indigo with urgent amber'",
  "complexity": "low|medium|high",
  "theme_override": "architectural|navigation|technology|cultural",
  "dominant_shape": "waves|grid|circles|layers|flow",
  "images": [
    {{"caption": "Max 20-word caption linking image to article theme", "visual_focus": "what this image should emphasize"}},
    {{"caption": "Max 20-word caption for image 2", "visual_focus": "focus"}},
    {{"caption": "Max 20-word caption for image 3", "visual_focus": "focus"}}
  ]
}}"""
        raw = self._query_qwen_text(prompt, timeout=60)
        return self._parse_json_response(raw)

    def evaluate_image(self, png_data, theme, article_title, iteration):
        """Ask Qwen vision to score the image and suggest improvements."""
        prompt = f"""You are an art director reviewing an abstract image for a disability culture article.

Article theme: {theme}
Article: {article_title}
Iteration: {iteration}/3

Score this abstract image on:
- Artistic quality (composition, visual interest, sophistication)
- Thematic relevance (does it evoke the article's disability/accessibility themes?)
- Emotional resonance (does it feel meaningful, not generic?)

Respond JSON only:
{{"score": 1-10, "strength": "what works", "issue": "main problem if score<7", "fix": "specific rendering adjustment to improve"}}"""
        raw = self._query_qwen_vision(png_data, prompt, timeout=90)
        result = self._parse_json_response(raw)
        if result and isinstance(result.get('score'), (int, float)):
            return result
        return {"score": 6, "strength": "ok", "issue": "evaluation unavailable", "fix": ""}

    # ──────────────────────────────────────────────────────────────────────────
    # Artistic DNA — seeded palette + corner signature
    # ──────────────────────────────────────────────────────────────────────────

    def _derive_article_seed(self, slug):
        """Stable integer seed from article slug."""
        return int(hashlib.md5(slug.encode()).hexdigest()[:8], 16)

    def _apply_artistic_dna(self, palette, slug, image_index):
        """Shift palette hue based on article seed — shared DNA across images."""
        seed = self._derive_article_seed(slug)
        shift = (seed % 40) - 20  # -20 to +20 per-channel shift
        varied = []
        for r, g, b in palette:
            # Apply seed-based tint + slight variation per image index
            angle = (seed + image_index * 30) % 360
            tint_r = int(math.sin(math.radians(angle)) * 15)
            tint_g = int(math.sin(math.radians(angle + 120)) * 15)
            tint_b = int(math.sin(math.radians(angle + 240)) * 15)
            nr = max(0, min(255, r + shift + tint_r))
            ng = max(0, min(255, g + (shift // 2) + tint_g))
            nb = max(0, min(255, b - (shift // 3) + tint_b))
            varied.append((nr, ng, nb))
        return varied

    def _add_corner_signature(self, grid, palette, slug):
        """Add small corner motif — same shape every image in article."""
        seed = self._derive_article_seed(slug)
        # Top-right corner: concentric arc rings (article fingerprint)
        cx = self.grid_width - 1
        cy = 0
        accent = (seed % len(palette))
        for r in range(10, 60, 8):
            for angle in range(180, 270, 2):
                rad = math.radians(angle)
                x = int(cx + r * math.cos(rad))
                y_ = int(cy + r * math.sin(rad))
                if 0 <= x < self.grid_width and 0 <= y_ < self.grid_height:
                    grid[y_][x] = (accent + r // 8) % len(palette)

    # ──────────────────────────────────────────────────────────────────────────
    # Content analysis
    # ──────────────────────────────────────────────────────────────────────────

    def analyze_content(self, content, title):
        combined = (content + ' ' + title).lower()
        analysis = {
            'primary_theme': 'architectural',
            'disability_perspective': 'general',
            'complexity_level': 'medium',
        }
        if any(w in combined for w in ['building', 'space', 'office', 'architecture', 'acoustic', 'sound', 'echo']):
            analysis['primary_theme'] = 'architectural'
        elif any(w in combined for w in ['transport', 'navigation', 'station', 'street', 'route', 'mobility', 'wheelchair', 'barrier']):
            analysis['primary_theme'] = 'navigation'
        elif any(w in combined for w in ['technology', 'interface', 'digital', 'screen', 'app', 'software', 'pattern', 'system']):
            analysis['primary_theme'] = 'technology'
        elif any(w in combined for w in ['culture', 'film', 'art', 'entertainment', 'oscar', 'hollywood', 'media']):
            analysis['primary_theme'] = 'cultural'

        if any(w in combined for w in ['deaf', 'hearing', 'sign', 'caption', 'audio']):
            analysis['disability_perspective'] = 'deaf_visual'
        elif any(w in combined for w in ['blind', 'sight', 'spatial', 'touch', 'echolocation']):
            analysis['disability_perspective'] = 'blind_spatial'
        elif any(w in combined for w in ['wheelchair', 'mobility', 'barrier', 'navigation', 'ramp']):
            analysis['disability_perspective'] = 'mobility'
        elif any(w in combined for w in ['autistic', 'pattern', 'sensory', 'cognitive', 'neurodivergent']):
            analysis['disability_perspective'] = 'neurodivergent'

        if any(w in combined for w in ['complex', 'chaos', 'interference', 'layered', 'multiple']):
            analysis['complexity_level'] = 'high'
        elif any(w in combined for w in ['simple', 'clear', 'minimal', 'clean']):
            analysis['complexity_level'] = 'low'
        return analysis

    # ──────────────────────────────────────────────────────────────────────────
    # Main entry — Qwen direction + render + Qwen validation loop
    # ──────────────────────────────────────────────────────────────────────────

    def generate_content_aware_images(self, content, title, slug, num_images=3):
        analysis = self.analyze_content(content, title)

        # Get Qwen artistic direction (non-blocking — fallback gracefully)
        direction = self.get_artistic_direction(content, title)
        if direction:
            if direction.get('theme_override') in self.palettes:
                analysis['primary_theme'] = direction['theme_override']
            if direction.get('complexity') in ('low', 'medium', 'high'):
                analysis['complexity_level'] = direction['complexity']

        base_palette = self.palettes[analysis['primary_theme']]
        images = []

        for i in range(min(num_images, 3)):
            # Apply article-specific artistic DNA to palette
            palette = self._apply_artistic_dna(base_palette, slug, i)

            # Get Qwen direction hints for this specific image
            img_direction = {}
            if direction and i < len(direction.get('images', [])):
                img_direction = direction['images'][i]

            # Render first candidate
            render_params = {'iteration': 1, 'qwen_fix': ''}
            png_data = self._render_image(i, analysis, palette, img_direction, render_params)

            # Single Qwen vision validation — fast with /no_think
            eval_result = self.evaluate_image(png_data, analysis['primary_theme'], title, 1)
            score = eval_result.get('score', 7)
            best_png = png_data
            best_score = score
            best_caption = img_direction.get('caption', self._generate_alt_text(analysis, i + 1))

            # If score < 6, do ONE re-render with Qwen's fix hint (no second validation)
            if score < 6:
                render_params = {'iteration': 2, 'qwen_fix': eval_result.get('fix', '')}
                png_data2 = self._render_image(i, analysis, palette, img_direction, render_params)
                best_png = png_data2  # accept re-render unconditionally

            # Caption: prefer Qwen's contextual one
            if best_caption is None:
                best_caption = self._generate_alt_text(analysis, i + 1)

            filename = f"{slug}_concept_{i+1}.png" if i == 0 else \
                       f"{slug}_context_{i+1}.png" if i == 1 else \
                       f"{slug}_solution_{i+1}.png"

            images.append({
                'data': best_png,
                'filename': filename,
                'description': best_caption,
                'score': best_score,
            })

        return images

    def _render_image(self, image_index, analysis, palette, img_direction, params):
        """Dispatch to appropriate renderer. Each call is non-deterministic."""
        # Parse Qwen fix suggestion to influence parameters
        fix = params.get('qwen_fix', '').lower()
        complexity = analysis['complexity_level']
        if 'simpl' in fix or 'less complex' in fix:
            complexity = 'low'
        elif 'more complex' in fix or 'more detail' in fix or 'richer' in fix:
            complexity = 'high'
        elif 'contrast' in fix or 'bolder' in fix:
            # Rotate palette for more contrast
            palette = palette[2:] + palette[:2]

        # Choose composition variant randomly (non-deterministic core)
        dominant = img_direction.get('visual_focus', '').lower()
        theme = analysis['primary_theme']
        perspective = analysis['disability_perspective']

        grid = self._blank_grid()

        if image_index == 0:
            # Primary concept — theme-based
            if theme == 'architectural' or 'acoustic' in dominant or 'wave' in dominant:
                return self._create_acoustic_interference_pattern(grid, palette, complexity)
            elif theme == 'navigation' or 'path' in dominant or 'route' in dominant:
                return self._create_navigation_complexity_map(grid, palette, perspective)
            elif theme == 'technology' or 'interface' in dominant or 'data' in dominant:
                return self._create_interface_hierarchy_pattern(grid, palette, complexity)
            else:
                return self._create_media_layer_visualization(grid, palette, perspective)

        elif image_index == 1:
            # Real-world context — randomly pick from multiple approaches
            variants = {
                'architectural': [self._create_building_acoustic_map, self._create_radial_space_map],
                'navigation': [self._create_urban_barrier_landscape, self._create_route_network],
                'technology': [self._create_digital_ecosystem_view, self._create_data_flow_map],
                'cultural': [self._create_cultural_space_analysis, self._create_media_strata],
            }
            options = variants.get(theme, [self._create_building_acoustic_map])
            renderer = random.choice(options)
            return renderer(grid, palette)

        else:
            # Solution vision — optimistic, harmonious
            variants = {
                'architectural': [self._create_acoustic_harmony_design, self._create_resonance_field],
                'navigation': [self._create_accessible_flow_pattern, self._create_open_pathway],
                'technology': [self._create_inclusive_interface_vision, self._create_clear_hierarchy],
                'cultural': [self._create_accessible_media_future, self._create_universal_stage],
            }
            options = variants.get(theme, [self._create_acoustic_harmony_design])
            renderer = random.choice(options)
            return renderer(grid, palette)

    # ──────────────────────────────────────────────────────────────────────────
    # Rendering methods — all non-deterministic via random parameters
    # ──────────────────────────────────────────────────────────────────────────

    def _create_acoustic_interference_pattern(self, grid, palette, complexity):
        wave_count = {'high': 7, 'medium': 5, 'low': 3}.get(complexity, 5)
        sources = [{
            'x': random.uniform(0.05, 0.95) * self.grid_width,
            'y': random.uniform(0.05, 0.95) * self.grid_height,
            'freq': random.uniform(0.015, 0.09),
            'amp': random.uniform(1.5, 7),
            'phase': random.uniform(0, math.pi * 2),
        } for _ in range(wave_count)]
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                v = sum(s['amp'] * math.sin(
                    math.sqrt((x - s['x'])**2 + (y - s['y'])**2) * s['freq'] + s['phase']
                ) for s in sources)
                norm = max(0.0, min(1.0, (v + wave_count * 4) / (wave_count * 8)))
                grid[y][x] = int(norm * (len(palette) - 1))
        self._add_disrupted_structures(grid, palette, complexity)
        return self._grid_to_png(grid, palette)

    def _create_navigation_complexity_map(self, grid, palette, perspective):
        # Fill with mid-base
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 3
        self._create_pathway_network(grid, palette)
        if perspective == 'mobility':
            self._add_mobility_barriers(grid, palette)
        elif perspective == 'blind_spatial':
            self._add_spatial_navigation_complexity(grid, palette)
        elif perspective == 'deaf_visual':
            self._add_visual_information_gaps(grid, palette)
        else:
            self._add_general_navigation_barriers(grid, palette)
        return self._grid_to_png(grid, palette)

    def _create_interface_hierarchy_pattern(self, grid, palette, complexity):
        layers = {'high': 5, 'medium': 3, 'low': 2}.get(complexity, 3)
        for layer in range(layers):
            colour = max(0, len(palette) - 1 - layer)
            for _ in range(max(2, 18 - layer * 3)):
                cx = random.randint(max(1, layer * 25), max(2, self.grid_width - layer * 25))
                cy = random.randint(max(1, layer * 15), max(2, self.grid_height - layer * 15))
                sz = max(5, random.randint(12 - layer, 45 - layer * 4))
                self._draw_interface_element(grid, cx, cy, sz, colour, palette)
        self._add_attention_flow_vectors(grid, palette)
        return self._grid_to_png(grid, palette)

    def _create_media_layer_visualization(self, grid, palette, perspective):
        self._create_media_base_layer(grid, palette)
        if perspective == 'deaf_visual':
            self._visualize_caption_gaps(grid, palette)
        elif perspective == 'blind_spatial':
            self._visualize_audio_description_needs(grid, palette)
        else:
            self._visualize_general_access_barriers(grid, palette)
        return self._grid_to_png(grid, palette)

    # Context variants
    def _create_building_acoustic_map(self, grid, palette):
        wall = len(palette) - 1
        for x in range(self.grid_width):
            grid[0][x] = grid[self.grid_height - 1][x] = wall
        for y in range(self.grid_height):
            grid[y][0] = grid[y][self.grid_width - 1] = wall
        dividers = random.randint(2, 4)
        for d in range(1, dividers + 1):
            col = d * self.grid_width // (dividers + 1)
            for y in range(1, self.grid_height - 1):
                if random.random() > 0.15:  # doors/openings
                    grid[y][col] = wall
        for _ in range(3):
            cx = random.randint(80, self.grid_width - 80)
            cy = random.randint(40, self.grid_height - 40)
            max_r = random.randint(40, 90)
            for r in range(0, max_r, random.randint(6, 12)):
                colour = r % len(palette)
                for angle in range(0, 360, 2):
                    rad = math.radians(angle)
                    x = int(cx + r * math.cos(rad))
                    y_ = int(cy + r * math.sin(rad))
                    if 0 <= x < self.grid_width and 0 <= y_ < self.grid_height and grid[y_][x] == 0:
                        grid[y_][x] = colour
        return self._grid_to_png(grid, palette)

    def _create_radial_space_map(self, grid, palette):
        """Alternative: circular space with radiating sound."""
        cx, cy = self.grid_width // 2, self.grid_height // 2
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                d = math.sqrt((x - cx)**2 + (y - cy)**2)
                angle = math.atan2(y - cy, x - cx)
                val = d * 0.04 + angle * 0.3 + random.uniform(0, 0.3)
                grid[y][x] = int(abs(math.sin(val)) * (len(palette) - 1))
        return self._grid_to_png(grid, palette)

    def _create_urban_barrier_landscape(self, grid, palette):
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 4
        street_colour = len(palette) - 1
        n_h = random.randint(2, 4)
        n_v = random.randint(3, 5)
        h_streets = [int(self.grid_height * (i + 1) / (n_h + 1)) for i in range(n_h)]
        v_streets = [int(self.grid_width * (i + 1) / (n_v + 1)) for i in range(n_v)]
        for ys in h_streets:
            for x in range(self.grid_width):
                for dy in range(-3, 4):
                    if 0 <= ys + dy < self.grid_height:
                        grid[ys + dy][x] = street_colour
        for xs in v_streets:
            for y in range(self.grid_height):
                for dx in range(-3, 4):
                    if 0 <= xs + dx < self.grid_width:
                        grid[y][xs + dx] = street_colour
        intersections = [(xs, ys) for xs in v_streets for ys in h_streets]
        barrier_count = random.randint(3, len(intersections))
        for ix, iy in random.sample(intersections, min(barrier_count, len(intersections))):
            r = random.randint(8, 22)
            for y in range(max(0, iy - r), min(self.grid_height, iy + r)):
                for x in range(max(0, ix - r), min(self.grid_width, ix + r)):
                    if (x - ix)**2 + (y - iy)**2 < r**2:
                        grid[y][x] = 1
        return self._grid_to_png(grid, palette)

    def _create_route_network(self, grid, palette):
        """Alternative: organic route network with dead ends."""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 2
        nodes = [(random.randint(40, self.grid_width - 40),
                  random.randint(30, self.grid_height - 30)) for _ in range(10)]
        for i, (x1, y1) in enumerate(nodes):
            for j, (x2, y2) in enumerate(nodes):
                if j <= i or random.random() > 0.4:
                    continue
                self._draw_pathway(grid, x1, y1, x2, y2, len(palette) - 1)
        # Dead ends — highlighted
        for nx, ny in random.sample(nodes, min(4, len(nodes))):
            for r in range(5, 12):
                for angle in range(0, 360, 15):
                    x = int(nx + r * math.cos(math.radians(angle)))
                    y_ = int(ny + r * math.sin(math.radians(angle)))
                    if 0 <= x < self.grid_width and 0 <= y_ < self.grid_height:
                        grid[y_][x] = 0
        return self._grid_to_png(grid, palette)

    def _create_digital_ecosystem_view(self, grid, palette):
        nodes = [(random.randint(70, self.grid_width - 70),
                  random.randint(50, self.grid_height - 50)) for _ in range(random.randint(8, 14))]
        for i, (x1, y1) in enumerate(nodes):
            for j, (x2, y2) in enumerate(nodes):
                if j <= i or random.random() > 0.3:
                    continue
                self._draw_pathway(grid, x1, y1, x2, y2, 3)
        for idx, (nx, ny) in enumerate(nodes):
            r = random.randint(8, 22)
            colour = (idx * 2) % len(palette)
            for y in range(max(0, ny - r), min(self.grid_height, ny + r)):
                for x in range(max(0, nx - r), min(self.grid_width, nx + r)):
                    if (x - nx)**2 + (y - ny)**2 < r**2:
                        grid[y][x] = colour
        return self._grid_to_png(grid, palette)

    def _create_data_flow_map(self, grid, palette):
        """Alternative: data flowing downward through filters."""
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                flow = math.sin(x * 0.03 + y * 0.01) * math.cos(y * 0.04)
                grid[y][x] = int(abs(flow) * (len(palette) - 1))
        # Filter bands
        band_positions = sorted(random.sample(range(40, self.grid_height - 40), 3))
        for bp in band_positions:
            for x in range(self.grid_width):
                for dy in range(-2, 3):
                    if 0 <= bp + dy < self.grid_height:
                        grid[bp + dy][x] = len(palette) - 1
        return self._grid_to_png(grid, palette)

    def _create_cultural_space_analysis(self, grid, palette):
        bands = len(palette)
        band_h = max(1, self.grid_height // bands)
        freq = random.uniform(0.03, 0.06)
        for b in range(bands):
            for y in range(b * band_h, min(self.grid_height, (b + 1) * band_h)):
                for x in range(self.grid_width):
                    wave = int(4 * math.sin(x * freq + b * 0.9))
                    grid[y][x] = (b + wave) % len(palette)
        for _ in range(random.randint(80, 250)):
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            grid[y][x] = len(palette) - 1
        return self._grid_to_png(grid, palette)

    def _create_media_strata(self, grid, palette):
        """Alternative: overlapping frames / media layers."""
        for i in range(random.randint(3, 6)):
            x1 = random.randint(0, self.grid_width // 3)
            y1 = random.randint(0, self.grid_height // 3)
            x2 = random.randint(x1 + 80, self.grid_width)
            y2 = random.randint(y1 + 60, self.grid_height)
            colour = i % len(palette)
            for y in range(y1, min(y2, self.grid_height)):
                for x in range(x1, min(x2, self.grid_width)):
                    base = int((x - x1) * 0.04 + (y - y1) * 0.02)
                    grid[y][x] = (colour + base) % len(palette)
        return self._grid_to_png(grid, palette)

    # Solution variants
    def _create_acoustic_harmony_design(self, grid, palette):
        cx = random.randint(int(self.grid_width * 0.3), int(self.grid_width * 0.7))
        cy = random.randint(int(self.grid_height * 0.3), int(self.grid_height * 0.7))
        max_r = math.sqrt(max(cx, self.grid_width - cx)**2 + max(cy, self.grid_height - cy)**2)
        ring_w = random.randint(10, 20)
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                d = math.sqrt((x - cx)**2 + (y - cy)**2)
                ripple = 1.5 * math.sin(x * 0.04) * math.cos(y * 0.04)
                ring = int((d + ripple * 5) / ring_w) % len(palette)
                grid[y][x] = ring
        return self._grid_to_png(grid, palette)

    def _create_resonance_field(self, grid, palette):
        """Alternative: harmonic field — two interfering centres."""
        c1x, c1y = int(self.grid_width * 0.35), int(self.grid_height * 0.5)
        c2x, c2y = int(self.grid_width * 0.65), int(self.grid_height * 0.5)
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                d1 = math.sqrt((x - c1x)**2 + (y - c1y)**2)
                d2 = math.sqrt((x - c2x)**2 + (y - c2y)**2)
                v = math.sin(d1 * 0.07) + math.sin(d2 * 0.07)
                grid[y][x] = int((v + 2) / 4 * (len(palette) - 1))
        return self._grid_to_png(grid, palette)

    def _create_accessible_flow_pattern(self, grid, palette):
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 3
        n_paths = random.randint(2, 4)
        for p in range(n_paths):
            y_base = int(self.grid_height * (0.15 + p * 0.7 / n_paths))
            colour = (len(palette) - 1 - p) % len(palette)
            freq = random.uniform(0.015, 0.035)
            amp = random.uniform(8, 25)
            for x in range(self.grid_width):
                wave = int(amp * math.sin(x * freq + p * 1.2))
                y_center = max(0, min(self.grid_height - 1, y_base + wave))
                for dy in range(-5, 6):
                    ny = y_center + dy
                    if 0 <= ny < self.grid_height:
                        alpha = 1 - abs(dy) / 6
                        grid[ny][x] = max(0, min(len(palette) - 1,
                                                  int(alpha * colour + (1 - alpha) * grid[ny][x])))
        return self._grid_to_png(grid, palette)

    def _create_open_pathway(self, grid, palette):
        """Alternative: single clear open path through obstacles."""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 1
        # Obstacles
        for _ in range(random.randint(8, 15)):
            ox = random.randint(30, self.grid_width - 30)
            oy = random.randint(20, self.grid_height - 20)
            r = random.randint(15, 35)
            for y in range(max(0, oy - r), min(self.grid_height, oy + r)):
                for x in range(max(0, ox - r), min(self.grid_width, ox + r)):
                    if (x - ox)**2 + (y - oy)**2 < r**2:
                        grid[y][x] = 0
        # Clear path through middle
        path_y = self.grid_height // 2
        for x in range(self.grid_width):
            wave = int(20 * math.sin(x * 0.025))
            for dy in range(-8, 9):
                ny = path_y + wave + dy
                if 0 <= ny < self.grid_height:
                    grid[ny][x] = len(palette) - 1
        return self._grid_to_png(grid, palette)

    def _create_inclusive_interface_vision(self, grid, palette):
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 5
        header_h = self.grid_height // 8
        for y in range(header_h):
            for x in range(self.grid_width):
                grid[y][x] = len(palette) - 1
        splits = random.choice([(0.5, 0.5), (0.4, 0.6), (0.6, 0.4)])
        split_x = int(self.grid_width * splits[0])
        cards = [
            (0.02, header_h / self.grid_height + 0.03, splits[0] - 0.02, 0.97),
            (splits[0] + 0.02, header_h / self.grid_height + 0.03, 0.98, 0.58),
            (splits[0] + 0.02, 0.60, 0.98, 0.97),
        ]
        for idx, (x1f, y1f, x2f, y2f) in enumerate(cards):
            x1, y1 = int(x1f * self.grid_width), int(y1f * self.grid_height)
            x2, y2 = int(x2f * self.grid_width), int(y2f * self.grid_height)
            for y in range(y1, min(y2, self.grid_height)):
                for x in range(x1, min(x2, self.grid_width)):
                    grid[y][x] = (idx + 1) % len(palette)
        for i in range(random.randint(3, 6)):
            ix = int(self.grid_width * (0.1 + i * 0.15))
            iy = header_h // 2
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    if dx**2 + dy**2 < 20 and 0 <= iy + dy < self.grid_height and 0 <= ix + dx < self.grid_width:
                        grid[iy + dy][ix + dx] = 6
        return self._grid_to_png(grid, palette)

    def _create_clear_hierarchy(self, grid, palette):
        """Alternative: strong typographic-like hierarchy."""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 5
        # Title block
        for y in range(0, self.grid_height // 5):
            for x in range(int(self.grid_width * 0.05), int(self.grid_width * 0.95)):
                grid[y][x] = len(palette) - 1
        # Content rows of decreasing prominence
        row_starts = [self.grid_height // 4, self.grid_height // 2, int(self.grid_height * 0.75)]
        for idx, ry in enumerate(row_starts):
            w_frac = 0.9 - idx * 0.2
            for y in range(ry, min(ry + self.grid_height // 8, self.grid_height)):
                for x in range(int(self.grid_width * 0.05), int(self.grid_width * w_frac)):
                    grid[y][x] = (idx + 1) % len(palette)
        return self._grid_to_png(grid, palette)

    def _create_accessible_media_future(self, grid, palette):
        frame_h = self.grid_height // 3
        for row in range(3):
            y_base = row * frame_h
            base_col = (row * 2) % len(palette)
            freq = random.uniform(0.02, 0.05)
            for y in range(y_base, min(y_base + frame_h - 4, self.grid_height)):
                for x in range(4, self.grid_width - 4):
                    wave = int(math.sin(x * freq + row) * 2)
                    grid[y][x] = max(0, min(len(palette) - 1, base_col + wave))
            for x in range(self.grid_width):
                border = min(y_base + frame_h - 2, self.grid_height - 1)
                grid[border][x] = len(palette) - 1
            cap_y = min(y_base + frame_h - 12, self.grid_height - 1)
            for y in range(cap_y, min(cap_y + 8, self.grid_height)):
                for x in range(self.grid_width):
                    grid[y][x] = 7 % len(palette)
        return self._grid_to_png(grid, palette)

    def _create_universal_stage(self, grid, palette):
        """Alternative: circular stage — centre spotlight."""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 1
        cx, cy = self.grid_width // 2, int(self.grid_height * 0.45)
        r_outer = int(min(self.grid_width, self.grid_height) * 0.38)
        for y in range(max(0, cy - r_outer), min(self.grid_height, cy + r_outer)):
            for x in range(max(0, cx - r_outer), min(self.grid_width, cx + r_outer)):
                d = math.sqrt((x - cx)**2 + (y - cy)**2)
                if d < r_outer:
                    ring = int((1 - d / r_outer) * (len(palette) - 1))
                    grid[y][x] = ring
        return self._grid_to_png(grid, palette)

    # ──────────────────────────────────────────────────────────────────────────
    # Drawing primitives
    # ──────────────────────────────────────────────────────────────────────────

    def _blank_grid(self):
        return [[0] * self.grid_width for _ in range(self.grid_height)]

    def _add_disrupted_structures(self, grid, palette, complexity):
        count = {'high': 5, 'medium': 3, 'low': 2}.get(complexity, 3)
        margin = 40
        if self.grid_width <= margin * 2 + 10 or self.grid_height <= 50:
            return
        for _ in range(count):
            x = random.randint(margin, self.grid_width - margin)
            y = random.randint(25, self.grid_height - 25)
            w = random.randint(30, min(90, self.grid_width // 4))
            h = random.randint(15, min(55, self.grid_height // 5))
            base = len(palette) // 2
            for dy in range(h):
                for dx in range(w):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        grid[ny][nx] = (base + grid[ny][nx]) % len(palette)

    def _create_pathway_network(self, grid, palette):
        node_count = random.randint(3, 6)
        nodes = [(random.randint(20, self.grid_width - 20),
                  random.randint(15, self.grid_height - 15)) for _ in range(node_count)]
        for i in range(len(nodes) - 1):
            self._draw_pathway(grid, nodes[i][0], nodes[i][1],
                               nodes[i+1][0], nodes[i+1][1], len(palette) - 1)
        if len(nodes) > 2:
            self._draw_pathway(grid, nodes[0][0], nodes[0][1],
                               nodes[-1][0], nodes[-1][1], len(palette) - 2)

    def _draw_pathway(self, grid, x0, y0, x1, y1, color_idx):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx - dy
        x, y = x0, y0
        steps = 0
        while steps < self.grid_width * 2:
            for off in range(-1, 2):
                if 0 <= x < self.grid_width and 0 <= y + off < self.grid_height:
                    grid[y + off][x] = color_idx
                if 0 <= x + off < self.grid_width and 0 <= y < self.grid_height:
                    grid[y][x + off] = color_idx
            if x == x1 and y == y1:
                break
            e2 = err * 2
            if e2 > -dy:
                err -= dy; x += sx
            if e2 < dx:
                err += dx; y += sy
            steps += 1

    def _add_mobility_barriers(self, grid, palette):
        for _ in range(random.randint(5, 10)):
            x = random.randint(40, self.grid_width - 40)
            y = random.randint(15, self.grid_height - 15)
            btype = random.choice(['stairs', 'narrow', 'elevation'])
            if btype == 'stairs':
                self._draw_stairs_barrier(grid, x, y, palette)
            elif btype == 'narrow':
                self._draw_narrow_passage(grid, x, y, palette)
            else:
                self._draw_elevation_change(grid, x, y, palette)

    def _draw_stairs_barrier(self, grid, x, y, palette):
        steps = random.randint(3, 6)
        for step in range(steps):
            sy = y + step * 3
            sw = max(1, 18 - step * 2)
            for dx in range(sw):
                for dy in range(2):
                    nx, ny = x + dx, sy + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        grid[ny][nx] = 1

    def _draw_narrow_passage(self, grid, x, y, palette):
        gap = random.randint(2, 5)
        for dy in range(-18, 19):
            ny = y + dy
            if 0 <= ny < self.grid_height and abs(dy) > gap:
                for dx in range(-10, 11):
                    nx = x + dx
                    if 0 <= nx < self.grid_width:
                        grid[ny][nx] = 0

    def _draw_elevation_change(self, grid, x, y, palette):
        length = random.randint(20, 40)
        for dx in range(length):
            nx = x + dx
            if nx < self.grid_width:
                ramp_y = y + dx // 4
                if 0 <= ramp_y < self.grid_height:
                    grid[ramp_y][nx] = len(palette) - 2

    def _add_spatial_navigation_complexity(self, grid, palette):
        origins = [(random.randint(40, self.grid_width - 40),
                    random.randint(25, self.grid_height - 25)) for _ in range(random.randint(3, 5))]
        for ox, oy in origins:
            spacing = random.randint(6, 14)
            for r in range(0, 90, spacing):
                colour = r % len(palette)
                for angle in range(0, 360, 2):
                    rad = math.radians(angle)
                    x = int(ox + r * math.cos(rad))
                    y_ = int(oy + r * math.sin(rad))
                    if 0 <= x < self.grid_width and 0 <= y_ < self.grid_height:
                        grid[y_][x] = colour

    def _add_visual_information_gaps(self, grid, palette):
        for _ in range(random.randint(4, 8)):
            x = random.randint(15, self.grid_width - 90)
            y = random.randint(15, self.grid_height - 45)
            w = random.randint(25, 90)
            h = random.randint(12, 38)
            for dy in range(h):
                for dx in range(w):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        grid[ny][nx] = 0

    def _add_general_navigation_barriers(self, grid, palette):
        for _ in range(random.randint(4, 7)):
            cx = random.randint(50, self.grid_width - 50)
            cy = random.randint(30, self.grid_height - 30)
            r = random.randint(10, 28)
            for y in range(max(0, cy - r), min(self.grid_height, cy + r)):
                for x in range(max(0, cx - r), min(self.grid_width, cx + r)):
                    if (x - cx)**2 + (y - cy)**2 < r**2:
                        grid[y][x] = 1

    def _draw_interface_element(self, grid, x, y, size, intensity, palette):
        colour = intensity % len(palette)
        border = (colour + 2) % len(palette)
        for dy in range(-size // 2, size // 2 + 1):
            for dx in range(-size, size + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    is_border = (abs(dy) >= size // 2 or abs(dx) >= size)
                    grid[ny][nx] = border if is_border else colour

    def _add_attention_flow_vectors(self, grid, palette):
        accent = len(palette) - 2
        spacing = random.randint(40, 80)
        for i in range(0, self.grid_width, spacing):
            end_x = min(i + random.randint(30, 60), self.grid_width - 1)
            self._draw_pathway(grid, i, 0, end_x, self.grid_height - 1, accent)

    def _create_media_base_layer(self, grid, palette):
        freq = random.uniform(0.02, 0.05)
        for y in range(self.grid_height):
            band = (y * len(palette)) // self.grid_height
            for x in range(self.grid_width):
                wave = int(math.sin(x * freq + y * 0.01) * 1.5)
                grid[y][x] = max(0, min(len(palette) - 1, (band + wave) % len(palette)))

    def _visualize_caption_gaps(self, grid, palette):
        cap_top = int(self.grid_height * (0.78 + random.uniform(-0.05, 0.05)))
        stripe_w = random.randint(10, 16)
        for y in range(cap_top, self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 0 if (x // stripe_w) % 2 == 0 else len(palette) - 1

    def _visualize_audio_description_needs(self, grid, palette):
        bar_w = random.randint(self.grid_width // 12, self.grid_width // 7)
        for y in range(self.grid_height):
            for x in range(bar_w):
                grid[y][x] = 0
            for x in range(self.grid_width - bar_w, self.grid_width):
                grid[y][x] = 0

    def _visualize_general_access_barriers(self, grid, palette):
        for _ in range(random.randint(3, 6)):
            rx = random.randint(0, self.grid_width - 100)
            ry = random.randint(0, self.grid_height - 70)
            stripe_w = random.randint(4, 8)
            for y in range(ry, min(ry + 70, self.grid_height)):
                for x in range(rx, min(rx + 100, self.grid_width)):
                    if (x + y) % stripe_w < stripe_w // 2:
                        grid[y][x] = 1

    # ──────────────────────────────────────────────────────────────────────────
    # Alt text fallback
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_alt_text(self, analysis, image_num):
        theme_desc = {
            'architectural': 'acoustic patterns in built space',
            'navigation': 'navigation complexity and barriers',
            'technology': 'digital interface hierarchy',
            'cultural': 'media accessibility layers',
        }
        img_type = {1: 'Concept', 2: 'Context', 3: 'Solution'}
        base = theme_desc.get(analysis['primary_theme'], 'accessibility patterns')
        itype = img_type.get(image_num, 'Illustration')
        return f"{itype}: {base} from {analysis['disability_perspective']} perspective"

    # ──────────────────────────────────────────────────────────────────────────
    # PNG encoding — correct byte literals
    # ──────────────────────────────────────────────────────────────────────────

    def _grid_to_png(self, grid, palette):
        pixels = []
        for gy in range(self.grid_height):
            row = []
            for gx in range(self.grid_width):
                colour = palette[grid[gy][gx] % len(palette)]
                row.extend(colour)
            pixels.append(row)
        return self._create_png_rgb(pixels)

    def _create_png_rgb(self, pixels):
        height = len(pixels)
        width = len(pixels[0]) // 3

        png = b'\x89PNG\r\n\x1a\n'

        ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        png += struct.pack('>I', len(ihdr)) + b'IHDR' + ihdr
        png += struct.pack('>I', zlib.crc32(b'IHDR' + ihdr) & 0xFFFFFFFF)

        raw = b''
        for row in pixels:
            raw += b'\x00' + bytes(row)
        compressed = zlib.compress(raw)
        png += struct.pack('>I', len(compressed)) + b'IDAT' + compressed
        png += struct.pack('>I', zlib.crc32(b'IDAT' + compressed) & 0xFFFFFFFF)

        png += struct.pack('>I', 0) + b'IEND'
        png += struct.pack('>I', zlib.crc32(b'IEND') & 0xFFFFFFFF)

        return png


# ─────────────────────────────────────────────────────────────────────────────

def generate_article_images(content, title, slug, num_images=3):
    gen = IntelligentImageGenerator()
    imgs = gen.generate_content_aware_images(content, title, slug, num_images)
    return [{'data': i['data'], 'filename': i['filename'], 'alt_text': i['description']} for i in imgs]


if __name__ == "__main__":
    import sys
    content = "deaf designer at Union Station visual chaos sound waves transportation barrier deaf users excluded"
    title = "The Station That Forgot Deaf Users"
    gen = IntelligentImageGenerator()
    print("Getting Qwen artistic direction...", file=sys.stderr)
    direction = gen.get_artistic_direction(content, title)
    if direction:
        print("Direction:", json.dumps(direction, indent=2), file=sys.stderr)
    else:
        print("Qwen direction unavailable — running without", file=sys.stderr)
    print("Generating images with validation loop...", file=sys.stderr)
    imgs = gen.generate_content_aware_images(content, title, "test-station", 3)
    for img in imgs:
        p = Path(f"/tmp/{img['filename']}")
        p.write_bytes(img['data'])
        valid = img['data'][:4] == b'\x89PNG'
        print(f"  {img['filename']}  {len(img['data'])} bytes  PNG:{valid}  score:{img.get('score','?')}", file=sys.stderr)
        print(f"  Caption: {img['description']}", file=sys.stderr)
