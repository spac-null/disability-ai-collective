#!/usr/bin/env python3
"""
Generate sophisticated agent avatars and icons using new rendering technique
Creates professional, artistic pixel art for Disability-AI Collective agents
"""

import math
import random
import struct
import zlib

class AgentAvatarGenerator:
    def __init__(self, width=400, height=400):
        # Square avatars for agent icons
        self.width = width
        self.height = height
        self.pixel_size = 1
        
        # Sophisticated color palette for agent identities
        self.palettes = {
            "siri_sage": [  # Acoustic/auditory focus
                (15, 20, 30),    # Deep night blue
                (40, 60, 90),    # Midnight blue
                (80, 110, 150),  # Ocean blue
                (120, 160, 200), # Sky blue
                (180, 220, 255), # Light blue
                (255, 200, 100), # Golden accent
                (200, 100, 50),  # Copper accent
                (255, 255, 255), # White highlights
            ],
            "pixel_nova": [  # Visual/spatial focus
                (30, 20, 40),    # Deep purple
                (60, 40, 80),    # Royal purple
                (100, 80, 140),  # Lavender
                (150, 120, 200), # Light purple
                (200, 180, 255), # Pale lavender
                (100, 255, 200), # Mint green accent
                (255, 100, 150), # Pink accent
                (255, 255, 220), # Cream highlights
            ],
            "maya_flux": [  # Mobility/accessibility focus
                (20, 30, 20),    # Forest green
                (40, 60, 40),    # Deep green
                (80, 120, 80),   # Emerald green
                (120, 180, 120), # Light green
                (180, 220, 180), # Pale green
                (255, 150, 50),  # Orange accent
                (200, 100, 200), # Purple accent
                (240, 240, 240), # Off-white highlights
            ],
            "zen_circuit": [  # Neurodivergent/systemic focus
                (40, 30, 20),    # Deep brown
                (80, 60, 40),    # Chocolate brown
                (120, 90, 60),   # Tan brown
                (160, 120, 80),  # Light brown
                (200, 180, 160), # Beige
                (50, 150, 255),  # Blue accent
                (255, 100, 100), # Red accent
                (255, 255, 255), # White highlights
            ]
        }
    
    def _create_grid(self, fill_color_idx=0):
        return [[fill_color_idx for _ in range(self.width)] for _ in range(self.height)]
    
    def generate_siri_sage_avatar(self):
        """Siri Sage - Acoustic architecture, sound waves, auditory patterns"""
        palette = self.palettes["siri_sage"]
        grid = self._create_grid()
        
        # Circular sound wave patterns
        center_x, center_y = self.width // 2, self.height // 2
        max_radius = min(center_x, center_y) - 20
        
        for y in range(self.height):
            for x in range(self.width):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < max_radius:
                    # Concentric sound waves
                    wave_value = math.sin(distance * 0.1) * 0.5 + 0.5
                    color_idx = int(wave_value * 3) + 1
                    
                    # Add interference patterns
                    angle = math.atan2(dy, dx)
                    interference = math.sin(angle * 8 + distance * 0.2) * 0.3 + 0.7
                    
                    # Final color with interference
                    final_idx = min(len(palette) - 1, int(color_idx * interference))
                    grid[y][x] = final_idx
        
        # Add acoustic diffusion elements (geometric patterns)
        for i in range(8):
            angle = i * math.pi / 4
            radius = max_radius * 0.7
            px = int(center_x + math.cos(angle) * radius)
            py = int(center_y + math.sin(angle) * radius)
            
            # Draw acoustic diffuser shape
            for dy in range(-8, 9):
                for dx in range(-8, 9):
                    if dx*dx + dy*dy < 64:  # Circle
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if (dx + dy) % 3 == 0:
                                grid[ny][nx] = 5  # Golden accent
        
        return self._grid_to_png(grid, palette, "siri_sage_sophisticated.png")
    
    def generate_pixel_nova_avatar(self):
        """Pixel Nova - Visual patterns, spatial cognition, grid systems"""
        palette = self.palettes["pixel_nova"]
        grid = self._create_grid()
        
        # Grid-based visual patterns
        grid_size = 20
        for y in range(self.height):
            for x in range(self.width):
                # Create moiré pattern
                pattern1 = math.sin(x * 0.05) * math.cos(y * 0.05)
                pattern2 = math.sin((x + y) * 0.03) * math.cos((x - y) * 0.03)
                
                combined = (pattern1 + pattern2) * 0.5 + 0.5
                color_idx = int(combined * 3) + 2
                
                # Add grid overlay
                if x % grid_size < 2 or y % grid_size < 2:
                    color_idx = 6  # Pink grid lines
                
                grid[y][x] = color_idx
        
        # Central visual focus (eye/camera motif)
        center_x, center_y = self.width // 2, self.height // 2
        iris_radius = 40
        
        for y in range(self.height):
            for x in range(self.width):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < iris_radius:
                    # Iris pattern
                    angle = math.atan2(dy, dx)
                    radial = math.sin(distance * 0.2 + angle * 3) * 0.5 + 0.5
                    grid[y][x] = int(radial * 2) + 4  # Light purple shades
                    
                    # Pupil
                    if distance < iris_radius * 0.3:
                        grid[y][x] = 0  # Deep purple
        
        # Visual hierarchy elements
        for i in range(4):
            angle = i * math.pi / 2
            radius = 120
            px = int(center_x + math.cos(angle) * radius)
            py = int(center_y + math.sin(angle) * radius)
            
            # Directional arrows/indicators
            for dy in range(-10, 11):
                for dx in range(-10, 11):
                    if abs(dx) + abs(dy) < 15:  # Diamond shape
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if (dx * dy) > 0:  # Quadrants
                                grid[ny][nx] = 5  # Mint green
        
        return self._grid_to_png(grid, palette, "pixel_nova_sophisticated.png")
    
    def generate_maya_flux_avatar(self):
        """Maya Flux - Mobility pathways, accessibility routes, movement flow"""
        palette = self.palettes["maya_flux"]
        grid = self._create_grid()
        
        # Pathway network
        center_x, center_y = self.width // 2, self.height // 2
        
        # Create flowing pathway patterns
        for y in range(self.height):
            for x in range(self.width):
                # River-like flow pattern
                flow_x = math.sin(y * 0.03) * 30
                flow_y = math.cos(x * 0.02) * 20
                
                distance_to_flow = abs(x - (center_x + flow_x)) + abs(y - (center_y + flow_y))
                
                if distance_to_flow < 40:
                    # Pathway surface
                    texture = math.sin(x * 0.1) * math.cos(y * 0.1) * 0.5 + 0.5
                    grid[y][x] = int(texture * 2) + 2  # Green pathway
                else:
                    # Background terrain
                    terrain = math.sin(x * 0.02 + y * 0.03) * 0.3 + 0.7
                    grid[y][x] = int(terrain * 1.5)  # Darker green background
        
        # Accessibility nodes/intersections
        for node_num in range(6):
            angle = node_num * math.pi / 3
            radius = 100
            px = int(center_x + math.cos(angle) * radius)
            py = int(center_y + math.sin(angle) * radius)
            
            # Node circle
            for dy in range(-15, 16):
                for dx in range(-15, 16):
                    if dx*dx + dy*dy < 225:  # Circle radius 15
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            # Checkerboard pattern for node
                            if (dx + dy) % 4 < 2:
                                grid[ny][nx] = 5  # Orange node
                            else:
                                grid[ny][nx] = 6  # Purple node
        
        # Directional flow arrows
        for i in range(8):
            angle = i * math.pi / 4
            inner_radius = 60
            outer_radius = 140
            
            # Arrow line
            steps = 20
            for step in range(steps):
                t = step / steps
                radius = inner_radius + (outer_radius - inner_radius) * t
                px = int(center_x + math.cos(angle) * radius)
                py = int(center_y + math.sin(angle) * radius)
                
                # Draw arrow shaft
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        if abs(dx) + abs(dy) < 4:
                            nx, ny = px + dx, py + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                grid[ny][nx] = 7  # Off-white arrow
        
        return self._grid_to_png(grid, palette, "maya_flux_sophisticated.png")
    
    def generate_zen_circuit_avatar(self):
        """Zen Circuit - Neural networks, systemic connections, circuit patterns"""
        palette = self.palettes["zen_circuit"]
        grid = self._create_grid()
        
        # Neural network/circuit board pattern
        center_x, center_y = self.width // 2, self.height // 2
        
        # Create circuit grid
        cell_size = 30
        for y in range(0, self.height, cell_size):
            for x in range(0, self.width, cell_size):
                # Circuit node
                for dy in range(-3, 4):
                    for dx in range(-3, 4):
                        if dx*dx + dy*dy < 10:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                grid[ny][nx] = 5  # Blue circuit node
        
        # Connect nodes with circuit traces
        for y in range(0, self.height, cell_size):
            for x in range(0, self.width, cell_size):
                # Horizontal connections
                if x + cell_size < self.width:
                    for offset in range(cell_size + 1):
                        nx = x + offset
                        if 0 <= nx < self.width and 0 <= y < self.height:
                            if offset % 5 == 0:  # Dotted line
                                grid[y][nx] = 4  # Light brown trace
                
                # Vertical connections  
                if y + cell_size < self.height:
                    for offset in range(cell_size + 1):
                        ny = y + offset
                        if 0 <= x < self.width and 0 <= ny < self.height:
                            if offset % 5 == 0:  # Dotted line
                                grid[ny][x] = 4  # Light brown trace
        
        # Central processing unit/core
        cpu_radius = 50
        for y in range(self.height):
            for x in range(self.width):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < cpu_radius:
                    # CPU core pattern
                    angle = math.atan2(dy, dx)
                    radial_pattern = math.sin(distance * 0.3) * math.cos(angle * 6) * 0.5 + 0.5
                    grid[y][x] = int(radial_pattern * 3) + 1
                    
                    # Central core
                    if distance < cpu_radius * 0.4:
                        # Binary/data pattern
                        if (x + y) % 8 < 4:
                            grid[y][x] = 6  # Red core elements
                        else:
                            grid[y][x] = 7  # White core elements
        
        # Data flow arrows
        for i in range(12):
            angle = i * math.pi / 6
            radius = 120
            px = int(center_x + math.cos(angle) * radius)
            py = int(center_y + math.sin(angle) * radius)
            
            # Data packet/arrowhead
            for dy in range(-6, 7):
                for dx in range(-6, 7):
                    if abs(dx) + abs(dy) < 8:
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            # Directional chevron
                            if (dx * math.cos(angle) + dy * math.sin(angle)) > 0:
                                grid[ny][nx] = 5  # Blue data packet
        
        return self._grid_to_png(grid, palette, "zen_circuit_sophisticated.png")
    
    def _grid_to_png(self, grid, palette, filename):
        """Convert color grid to PNG"""
        pixels = []
        for grid_y in range(self.height):
            row = []
            for grid_x in range(self.width):
                color_idx = grid[grid_y][grid_x]
                color = palette[color_idx % len(palette)]
                row.extend(color)  # RGB values
            pixels.append(row)
        
        # Create PNG
        png_data = self._create_png_rgb(pixels)
        
        path = f"/home/node/.openclaw/workspaces/ops/disability-ai-collective/assets/{filename}"
        with open(path, 'wb') as f:
            f.write(png_data)
        
        return path
    
    def _create_png_rgb(self, pixels):
        """Create RGB PNG file"""
        height = len(pixels)
        width = len(pixels[0]) // 3  # Each pixel has 3 values (RGB)
        
        # PNG signature
        png_data = b'\x89PNG\r\n\x1a\n'
        
        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)  # RGB color
        png_data += struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data
        png_data += struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff)
        
        # IDAT chunk
        image_data = b''
        for row in pixels:
            image_data += b'\x00'  # Filter type (None)
            image_data += bytes(row)
        
        compressed_data = zlib.compress(image_data)
        png_data += struct.pack('>I', len(compressed_data)) + b'IDAT' + compressed_data
        png_data += struct.pack('>I', zlib.crc32(b'IDAT' + compressed_data) & 0xffffffff)
        
        # IEND chunk
        png_data += struct.pack('>I', 0) + b'IEND'
        png_data += struct.pack('>I', zlib.crc32(b'IEND') & 0xffffffff)
        
        return png_data

def main():
    """Generate sophisticated agent avatars"""
    print("🎨 GENERATING SOPHISTICATED AGENT AVATARS")
    print("=" * 50)
    
    generator = AgentAvatarGenerator(400, 400)
    
    # Set seed for reproducibility
    random.seed(42424242)
    
    print("\n👤 Generating: Siri Sage Avatar (Acoustic Architecture)")
    path1 = generator.generate_siri_sage_avatar()
    print(f"   ✅ Saved: {path1}")
    
    print("\n👤 Generating: Pixel Nova Avatar (Visual Spatial Cognition)")
    path2 = generator.generate_pixel_nova_avatar()
    print(f"   ✅ Saved: {path2}")
    
    print("\n👤 Generating: Maya Flux Avatar (Accessibility Pathways)")
    path3 = generator.generate_maya_flux_avatar()
    print(f"   ✅ Saved: {path3}")
    
    print("\n👤 Generating: Zen Circuit Avatar (Neurodivergent Systems)")
    path4 = generator.generate_zen_circuit_avatar()
    print(f"   ✅ Saved: {path4}")
    
    print("\n" + "=" * 50)
    print("✅ SOPHISTICATED AGENT AVATARS GENERATED!")
    print("All avatars are 400x400 pixels with unique color palettes.")
    print("\nAgents and their themes:")
    print("  • Siri Sage: Acoustic waves, sound patterns, auditory architecture")
    print("  • Pixel Nova: Visual grids, spatial cognition, pattern recognition")
    print("  • Maya Flux: Mobility pathways, accessibility routes, movement flow")
    print("  • Zen Circuit: Neural networks, systemic connections, circuit patterns")

if __name__ == "__main__":
    main()