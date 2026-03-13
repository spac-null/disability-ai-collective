#!/usr/bin/env python3
"""
Generate pixel art from image prompts.
"""

import json
import sys
import os
from datetime import datetime
import math
import random
import struct
import zlib
from pathlib import Path

class SophisticatedArtGenerator:
    def __init__(self, width=800, height=450):
        self.width = width
        self.height = height
        self.pixel_size = 1
        self.grid_width = width
        self.grid_height = height
        
        # Sophisticated color palette (RGB)
        self.palette = [
            (20, 25, 35),    # Deep slate
            (40, 50, 70),    # Dark steel
            (70, 85, 105),   # Medium steel
            (100, 115, 135), # Light steel
            (140, 155, 175), # Pale steel
            (180, 195, 210), # Off-white
            (60, 140, 190),  # Cool blue
            (190, 90, 40),   # Warm copper
            (140, 190, 80),  # Cool green
            (220, 180, 100), # Warm gold
        ]
    
    def generate_visual_chaos_transportation(self):
        """Generate visual chaos in transportation hub"""
        grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Create flickering departure boards (rectangular areas)
        board_positions = [
            (100, 50, 200, 80),   # Top left board
            (350, 50, 200, 80),   # Top right board
            (500, 150, 150, 60),  # Side board
        ]
        
        for bx, by, bw, bh in board_positions:
            for y in range(by, min(by + bh, self.grid_height)):
                for x in range(bx, min(bx + bw, self.grid_width)):
                    # Flickering effect
                    flicker = random.random() > 0.7
                    if flicker:
                        grid[y][x] = 5  # Off-white for text
                    else:
                        grid[y][x] = 0  # Deep slate for background
        
        # Create overlapping wayfinding signs (arrows and text)
        for _ in range(8):
            sign_x = random.randint(50, self.grid_width - 100)
            sign_y = random.randint(100, self.grid_height - 100)
            sign_w = random.randint(60, 120)
            sign_h = random.randint(30, 50)
            
            # Draw sign background
            for y in range(sign_y, min(sign_y + sign_h, self.grid_height)):
                for x in range(sign_x, min(sign_x + sign_w, self.grid_width)):
                    if random.random() > 0.3:  # Some transparency
                        grid[y][x] = 3  # Light steel
        
        # Create confusing color-coded lines
        line_colors = [6, 7, 8, 9]  # Blue, copper, green, gold
        for i, color_idx in enumerate(line_colors):
            # Create wavy, overlapping lines
            base_y = 200 + i * 40
            for x in range(self.grid_width):
                y = int(base_y + 20 * math.sin(x * 0.02 + i * 1.5))
                if 0 <= y < self.grid_height:
                    # Make lines overlap by drawing thicker
                    for dy in range(-1, 2):
                        ny = y + dy
                        if 0 <= ny < self.grid_height:
                            grid[ny][x] = color_idx
        
        return grid
    
    def generate_information_hierarchy(self):
        """Generate information hierarchy failures visualization"""
        grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Create grid of information blocks
        block_size = 60
        for grid_y in range(0, self.grid_height, block_size):
            for grid_x in range(0, self.grid_width, block_size):
                # Randomly assign importance
                importance = random.random()
                
                if importance > 0.8:  # Critical information (emergency exits)
                    color_idx = 7  # Warm copper (should stand out)
                    size_factor = 1.0
                elif importance > 0.5:  # Important information
                    color_idx = 6  # Cool blue
                    size_factor = 0.8
                else:  # Trivial details
                    color_idx = 3  # Light steel
                    size_factor = 1.2  # Trivial details are larger!
                
                # Draw block
                block_w = int(block_size * size_factor)
                block_h = int(block_size * size_factor)
                x = grid_x + (block_size - block_w) // 2
                y = grid_y + (block_size - block_h) // 2
                
                for by in range(y, min(y + block_h, self.grid_height)):
                    for bx in range(x, min(x + block_w, self.grid_width)):
                        grid[by][bx] = color_idx
        
        # Add cognitive load indicators (overlapping elements)
        for _ in range(15):
            x = random.randint(0, self.grid_width - 40)
            y = random.randint(0, self.grid_height - 40)
            w = random.randint(20, 60)
            h = random.randint(20, 60)
            
            # Semi-transparent overlay
            for by in range(y, min(y + h, self.grid_height)):
                for bx in range(x, min(x + w, self.grid_width)):
                    if random.random() > 0.5:
                        # Blend with existing color
                        current = grid[by][bx]
                        if current < 5:
                            grid[by][bx] = current + 1
        
        return grid
    
    def generate_co_design_process(self):
        """Generate disability co-design process visualization"""
        grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Create foundation (building blocks from the beginning)
        foundation_colors = [6, 7, 8]  # Blue, copper, green
        block_size = 40
        
        for i, color_idx in enumerate(foundation_colors):
            for x in range(i * block_size, self.grid_width, block_size * 3):
                for y in range(self.grid_height - 100, self.grid_height, block_size):
                    # Draw foundation block
                    for by in range(y, min(y + block_size, self.grid_height)):
                        for bx in range(x, min(x + block_size, self.grid_width)):
                            if (bx - x) > 5 and (by - y) > 5:  # Leave border
                                grid[by][bx] = color_idx
        
        # Create collaborative circles (people working together)
        circle_centers = [
            (200, 150),  # Disabled consultant
            (400, 150),  # Architect
            (600, 150),  # Designer
        ]
        
        circle_colors = [7, 6, 8]  # Different colors for different roles
        
        for (cx, cy), color_idx in zip(circle_centers, circle_colors):
            radius = 40
            for y in range(cy - radius, cy + radius):
                for x in range(cx - radius, cx + radius):
                    if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                        dx = x - cx
                        dy = y - cy
                        if dx*dx + dy*dy <= radius*radius:
                            grid[y][x] = color_idx
        
        # Create connecting lines (collaboration)
        for i in range(len(circle_centers) - 1):
            x1, y1 = circle_centers[i]
            x2, y2 = circle_centers[i + 1]
            
            # Draw line
            steps = 100
            for t in range(steps + 1):
                x = int(x1 + (x2 - x1) * t / steps)
                y = int(y1 + (y2 - y1) * t / steps)
                
                # Draw thick line
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                            if dx*dx + dy*dy <= 4:  # Circular brush
                                grid[ny][nx] = 5  # Off-white for connections
        
        return grid
    
    def grid_to_png_bytes(self, grid):
        """Convert grid to PNG bytes"""
        # Create raw pixel data
        pixels = bytearray()
        for y in range(self.height):
            for x in range(self.width):
                color_idx = grid[y][x] if y < len(grid) and x < len(grid[y]) else 0
                color_idx = min(color_idx, len(self.palette) - 1)
                r, g, b = self.palette[color_idx]
                pixels.extend([r, g, b, 255])  # RGBA
        
        # PNG header
        png = bytearray()
        
        # PNG signature
        png.extend(b'\x89PNG\r\n\x1a\n')
        
        # IHDR chunk
        ihdr = struct.pack('>I4sIIBBBBB', 13, b'IHDR', self.width, self.height, 
                          8, 2, 0, 0, 0)
        png.extend(ihdr)
        png.extend(struct.pack('>I', zlib.crc32(ihdr[4:])))
        
        # IDAT chunk (compressed image data)
        # Simple filter: each scanline starts with filter type 0 (none)
        scanline_length = self.width * 4 + 1
        raw_data = bytearray()
        for y in range(self.height):
            raw_data.append(0)  # Filter type 0
            offset = y * self.width * 4
            raw_data.extend(pixels[offset:offset + self.width * 4])
        
        compressed = zlib.compress(raw_data)
        idat = struct.pack('>I4s', len(compressed), b'IDAT') + compressed
        png.extend(idat)
        png.extend(struct.pack('>I', zlib.crc32(idat[4:])))
        
        # IEND chunk
        iend = struct.pack('>I4s', 0, b'IEND')
        png.extend(iend)
        png.extend(struct.pack('>I', zlib.crc32(iend[4:])))
        
        return bytes(png)
    
    def save_grid_as_png(self, grid, filename):
        """Save grid as PNG file"""
        png_bytes = self.grid_to_png_bytes(grid)
        with open(filename, 'wb') as f:
            f.write(png_bytes)
        return filename

def generate_art_for_prompts(image_prompts, slug, output_dir):
    """Generate art for image prompts."""
    
    generator = SophisticatedArtGenerator()
    image_filenames = []
    
    # Map prompt types to generation methods
    prompt_to_method = {
        'visual chaos': generator.generate_visual_chaos_transportation,
        'information hierarchy': generator.generate_information_hierarchy,
        'co-design': generator.generate_co_design_process
    }
    
    for i, prompt in enumerate(image_prompts):
        # Determine which generation method to use based on prompt content
        prompt_lower = prompt.lower()
        method = None
        
        if 'visual chaos' in prompt_lower or 'transportation hub' in prompt_lower:
            method = generator.generate_visual_chaos_transportation
        elif 'information hierarchy' in prompt_lower or 'cognitive load' in prompt_lower:
            method = generator.generate_information_hierarchy
        elif 'co-design' in prompt_lower or 'collaborative' in prompt_lower:
            method = generator.generate_co_design_process
        else:
            # Default to visual chaos
            method = generator.generate_visual_chaos_transportation
        
        # Generate the art
        grid = method()
        
        # Save the image
        filename = f"{slug}_pixel_art_{i+1}.png"
        filepath = os.path.join(output_dir, filename)
        
        generator.save_grid_as_png(grid, filepath)
        image_filenames.append(filename)
        
        print(f"[INFO] Generated image {i+1}: {filename}")
    
    return image_filenames

def main():
    # Read input
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    
    if data.get("status") != "success":
        print(json.dumps({"status": "error", "error": "Input data has error status"}))
        sys.exit(1)
    
    image_prompts = data.get("image_prompts", [])
    metadata = data.get("metadata", {})
    
    if not image_prompts:
        print(json.dumps({"status": "error", "error": "No image prompts provided"}))
        sys.exit(1)
    
    # Create assets directory if it doesn't exist
    repo_root = Path(__file__).parent
    assets_dir = repo_root / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    # Generate art
    slug = metadata.get("slug", "article")
    image_filenames = generate_art_for_prompts(image_prompts, slug, str(assets_dir))
    
    print(json.dumps({
        "status": "success",
        "image_filenames": image_filenames,
        "assets_dir": str(assets_dir),
        "slug": slug,
        "metadata": metadata
    }))

if __name__ == "__main__":
    main()