#!/usr/bin/env python3
"""
Generate sophisticated pixel art for accessibility-themed images
Creates complex, artistic patterns suitable for professional articles
"""

import math
import random
import struct
import zlib

class AccessibilityArtGenerator:
    def __init__(self, width=600, height=400):  # Optimized for smaller file sizes
        self.width = width
        self.height = height
        self.pixel_size = 1  # No scaling - direct pixel mapping
        self.grid_width = width
        self.grid_height = height
        
        # Sophisticated color palette (RGB) for accessibility themes
        self.palette = [
            (25, 30, 40),    # Dark background slate
            (50, 60, 80),    # Medium dark steel
            (80, 95, 115),   # Muted blue-grey
            (120, 140, 160), # Light blue-grey
            (170, 190, 210), # Pale sky blue
            (220, 230, 240), # Off-white for contrast
            (0, 100, 200),   # Strong accessibility blue
            (255, 180, 0),   # Vibrant accessible yellow/orange
            (0, 200, 100),   # Clear green for success/pathways
            (255, 0, 0),     # Red for warnings/barriers
            (100, 50, 150),  # Purple accent
        ]
    
    def _create_grid(self, fill_color_idx=0):
        return [[fill_color_idx for _ in range(self.grid_width)] for _ in range(self.grid_height)]
    
    def generate_expert_street_ada_compliance(self):
        """ADA compliance in street design, showing clear pathways and ramps"""
        grid = self._create_grid()
        
        # Street background
        for y in range(self.grid_height // 2, self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 1 # Dark street color
        
        # Sidewalk
        for y in range(self.grid_height // 3, self.grid_height // 2):
            for x in range(self.grid_width):
                grid[y][x] = 2 # Sidewalk color
        
        # Buildings in background
        for i in range(5):
            bx = random.randint(0, self.grid_width - 100)
            by = random.randint(10, self.grid_height // 4)
            bw = random.randint(80, 120)
            bh = random.randint(self.grid_height // 4, self.grid_height // 3 - 20)
            for y in range(by, by + bh):
                for x in range(bx, bx + bw):
                    grid[y][x] = 3 # Building color
        
        # ADA ramp visualization
        ramp_start_x = self.grid_width // 4
        ramp_end_x = self.grid_width // 2
        ramp_y_top = self.grid_height // 2 - 20
        ramp_y_bottom = self.grid_height // 2
        
        for x in range(ramp_start_x, ramp_end_x):
            # Draw ramp surface
            ramp_gradient_y = ramp_y_top + int((x - ramp_start_x) / (ramp_end_x - ramp_start_x) * (ramp_y_bottom - ramp_y_top))
            for y in range(ramp_gradient_y, ramp_y_bottom):
                grid[y][x] = 6 # Accessibility blue
            # Highlight ramp edge
            if (x - ramp_start_x) % 10 == 0:
                for y in range(ramp_gradient_y - 5, ramp_gradient_y):
                    grid[y][x] = 7 # Yellow highlight
        
        # Pedestrian pathway
        for x in range(self.grid_width // 8, self.grid_width - self.grid_width // 8, 20):
            for y in range(self.grid_height // 2 + 10, self.grid_height // 2 + 30):
                grid[y][x] = 5 # White pathway markers
                grid[y+1][x] = 5

        # Tactile paving (dots)
        for y in range(self.grid_height // 2 - 10, self.grid_height // 2):
            for x in range(self.grid_width // 4 - 20, self.grid_width // 4 + 20, 5):
                if (x + y) % 3 == 0:
                    grid[y][x] = 7 # Yellow tactile dots
        
        return self._grid_to_png(grid, "expert_street_ada_compliance_sophisticated.png")

    def generate_expert_transit_universal_design(self):
        """Universal design in public transit, multi-level wayfinding"""
        grid = self._create_grid()
        
        # Subway platform
        for y in range(self.grid_height // 2, self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 1 # Platform color
        
        # Train tracks
        track_y = self.grid_height // 2 + 30
        for x in range(self.grid_width):
            if x % 20 < 10: # Sleepers
                for y in range(track_y, track_y + 5):
                    grid[y][x] = 0
            if x % 5 == 0: # Rails
                for y in range(track_y - 5, track_y + 10):
                    if y % 2 == 0:
                        grid[y][x] = 3
        
        # Subway train
        train_start_x = self.grid_width // 3
        train_end_x = self.grid_width - self.grid_width // 4
        train_y_top = self.grid_height // 2 - 50
        train_y_bottom = self.grid_height // 2 - 5
        for y in range(train_y_top, train_y_bottom):
            for x in range(train_start_x, train_end_x):
                grid[y][x] = 4 # Train body color
        # Train doors
        for x in range(train_start_x + 40, train_end_x - 40, 60):
            for y in range(train_y_top + 10, train_y_bottom):
                grid[y][x] = 0 # Door color
        
        # Wayfinding signs
        sign_x = self.grid_width // 4
        sign_y = self.grid_height // 4
        sign_width = 60
        sign_height = 40
        for y in range(sign_y, sign_y + sign_height):
            for x in range(sign_x, sign_x + sign_width):
                grid[y][x] = 7 # Yellow sign background
        # Icon on sign
        for y in range(sign_y + 10, sign_y + 30):
            for x in range(sign_x + 10, sign_x + 30):
                if (x - (sign_x + 20))**2 + (y - (sign_y + 20))**2 < 100: # Circle
                    grid[y][x] = 6 # Blue icon
        
        # Tactile path on platform
        for x in range(self.grid_width // 8, self.grid_width - self.grid_width // 8, 10):
            for y in range(self.grid_height // 2 + 10, self.grid_height // 2 + 15):
                if (x + y) % 3 == 0:
                    grid[y][x] = 7 # Yellow tactile bumps
        
        return self._grid_to_png(grid, "expert_transit_universal_design_sophisticated.png")

    def generate_realistic_office_acoustic_scene(self):
        """Modern office with acoustic panels and sound dampening"""
        grid = self._create_grid()
        
        # Office floor
        for y in range(self.grid_height // 2, self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 2
        
        # Walls
        for y in range(0, self.grid_height):
            grid[y][0] = 3
            grid[y][self.grid_width - 1] = 3
        for x in range(0, self.grid_width):
            grid[0][x] = 3
        
        # Desks with computers
        for desk_num in range(3):
            desk_x = random.randint(self.grid_width // 4, self.grid_width - self.grid_width // 4 - 80)
            desk_y = random.randint(self.grid_height // 2 + 20, self.grid_height - 80)
            
            for y in range(desk_y, desk_y + 10):
                for x in range(desk_x, desk_x + 40):
                    grid[y][x] = 1 # Desk color
            
            # Computer monitor
            for y in range(desk_y - 20, desk_y - 5):
                for x in range(desk_x + 10, desk_x + 30):
                    grid[y][x] = 0 # Monitor screen (dark)
                    
        # Acoustic panels (geometric patterns on walls)
        for panel_num in range(5):
            panel_x = random.randint(10, self.grid_width - 50)
            panel_y = random.randint(10, self.grid_height // 3)
            panel_width = 30
            panel_height = 20
            
            for y in range(panel_y, panel_y + panel_height):
                for x in range(panel_x, panel_x + panel_width):
                    if (x + y) % 5 < 2:
                        grid[y][x] = 8 # Green acoustic panel
                    else:
                        grid[y][x] = 2
                        
        # Diffusers (wave-like patterns)
        for diff_num in range(3):
            diff_x = random.randint(self.grid_width // 4, self.grid_width - self.grid_width // 4)
            diff_y = random.randint(self.grid_height // 2 - 50, self.grid_height // 2 - 20)
            diff_radius = random.randint(10, 20)
            
            for y in range(diff_y - diff_radius, diff_y + diff_radius):
                for x in range(diff_x - diff_radius, diff_x + diff_radius):
                    dist = math.sqrt((x - diff_x)**2 + (y - diff_y)**2)
                    if dist < diff_radius and int(dist) % 3 == 0:
                        grid[y][x] = 6 # Blue diffuser waves
        
        return self._grid_to_png(grid, "realistic_office_acoustic_scene_sophisticated.png")

    def generate_realistic_street_accessibility_scene(self):
        """Busy street with accessible crosswalks, ramps, and clear pathways"""
        grid = self._create_grid()
        
        # Road
        for y in range(self.grid_height // 2, self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 0 # Dark road
        
        # Sidewalk
        for y in range(self.grid_height // 3, self.grid_height // 2):
            for x in range(self.grid_width):
                grid[y][x] = 1 # Grey sidewalk
        
        # Buildings
        for i in range(4):
            bx = random.randint(0, self.grid_width - 150)
            by = random.randint(10, self.grid_height // 4)
            bw = random.randint(100, 150)
            bh = random.randint(self.grid_height // 4, self.grid_height // 3 - 20)
            for y in range(by, by + bh):
                for x in range(bx, bx + bw):
                    grid[y][x] = 2 # Building color
        
        # Crosswalk
        cw_y_start = self.grid_height // 2 - 10
        cw_y_end = self.grid_height // 2 + 10
        cw_x_start = self.grid_width // 3
        cw_x_end = self.grid_width - self.grid_width // 3
        for x in range(cw_x_start, cw_x_end, 15):
            for y in range(cw_y_start, cw_y_end):
                grid[y][x] = 5 # White crosswalk stripes
        
        # Curb ramp
        ramp_x = self.grid_width // 4
        ramp_y_top = self.grid_height // 2 - 30
        ramp_y_bottom = self.grid_height // 2
        for y in range(ramp_y_top, ramp_y_bottom):
            ramp_width = int(30 * (1 - (y - ramp_y_top) / (ramp_y_bottom - ramp_y_top)))
            for x in range(ramp_x - ramp_width // 2, ramp_x + ramp_width // 2):
                grid[y][x] = 6 # Blue ramp
        
        # Pedestrians/activity (simple dots/shapes)
        for _ in range(10):
            px = random.randint(50, self.grid_width - 50)
            py = random.randint(self.grid_height // 2, self.grid_height - 20)
            grid[py][px] = 9 # Red for people/activity
        
        return self._grid_to_png(grid, "realistic_street_accessibility_scene_sophisticated.png")

    def generate_realistic_subway_accessibility_scene(self):
        """Subway station with accessible platforms, elevators, and tactile guidance"""
        grid = self._create_grid()
        
        # Subway tunnel/tracks
        for y in range(self.grid_height // 2, self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = 1 # Dark tracks/tunnel
        
        # Platform edge
        for x in range(self.grid_width):
            grid[self.grid_height // 2 - 1][x] = 5 # White platform edge
            
        # Tactile paving (warning strips)
        for x in range(self.grid_width // 8, self.grid_width - self.grid_width // 8, 10):
            for y in range(self.grid_height // 2 - 10, self.grid_height // 2 - 5):
                if (x + y) % 3 == 0:
                    grid[y][x] = 7 # Yellow tactile bumps
        
        # Subway train (partially visible)
        train_start_x = self.grid_width // 4
        train_y_top = self.grid_height // 2 - 50
        train_y_bottom = self.grid_height // 2 - 5
        for y in range(train_y_top, train_y_bottom):
            for x in range(train_start_x, train_start_x + 150):
                grid[y][x] = 4 # Train body
        
        # Elevator shaft
        elevator_x = self.grid_width - 100
        elevator_y_top = self.grid_height // 4
        elevator_y_bottom = self.grid_height // 2
        for y in range(elevator_y_top, elevator_y_bottom):
            for x in range(elevator_x, elevator_x + 30):
                grid[y][x] = 3 # Elevator shaft
        # Elevator door
        for y in range(elevator_y_top + 10, elevator_y_bottom - 10):
            for x in range(elevator_x + 5, elevator_x + 25):
                grid[y][x] = 5 # Door
        
        # Directional signage
        sign_x = self.grid_width // 2
        sign_y = self.grid_height // 4
        sign_width = 60
        sign_height = 30
        for y in range(sign_y, sign_y + sign_height):
            for x in range(sign_x, sign_x + sign_width):
                grid[y][x] = 7 # Yellow sign
        
        return self._grid_to_png(grid, "realistic_subway_accessibility_scene_sophisticated.png")

    def generate_refined_accessibility_pathways(self):
        """Abstract representation of clear, inclusive accessibility pathways"""
        grid = self._create_grid()
        
        # Base layers/gradients
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                grid[y][x] = int((x / self.grid_width) * 3) + 1 # Gradient across width
        
        # Central pathway (interweaving lines)
        path_center_y = self.grid_height // 2
        for x in range(self.grid_width):
            # Main clear path
            for y_offset in range(-5, 5):
                grid[path_center_y + y_offset][x] = 6 # Accessibility blue path
            
            # Intersecting path (diagonal flow)
            diag_y_offset = int(math.sin(x * 0.05) * 15)
            for y_offset in range(-3, 3):
                if 0 <= path_center_y + diag_y_offset + y_offset < self.grid_height:
                    grid[path_center_y + diag_y_offset + y_offset][x] = 8 # Green intersecting path
        
        # Barrier visualization (disrupted sections)
        for barrier_num in range(3):
            bx = random.randint(self.grid_width // 4, self.grid_width - self.grid_width // 4)
            by = random.randint(self.grid_height // 4, self.grid_height - self.grid_height // 4)
            b_radius = random.randint(15, 30)
            
            for y in range(by - b_radius, by + b_radius):
                for x in range(bx - b_radius, bx + b_radius):
                    if math.sqrt((x - bx)**2 + (y - by)**2) < b_radius:
                        grid[y][x] = 9 # Red barrier
                        
        # Guiding elements/dots
        for _ in range(100):
            px = random.randint(0, self.grid_width - 1)
            py = random.randint(0, self.grid_height - 1)
            if grid[py][px] not in [6, 8, 9]: # Not on a path or barrier
                grid[py][px] = 5 # White guiding dots
        
        return self._grid_to_png(grid, "refined_accessibility_pathways_sophisticated.png")

    def _grid_to_png(self, grid, filename):
        """Convert color grid to PNG"""
        # Direct pixel mapping (no scaling)
        pixels = []
        for grid_y in range(self.grid_height):
            row = []
            for grid_x in range(self.grid_width):
                color_idx = grid[grid_y][grid_x]
                color = self.palette[color_idx % len(self.palette)]
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
    """Generate sophisticated pixel art for accessibility page"""
    print("🎨 GENERATING SOPHISTICATED ACCESSIBILITY PIXEL ART")
    print("=" * 50)
    
    generator = AccessibilityArtGenerator(800, 450)
    
    # Set seed for reproducibility
    random.seed(42424242)
    
    print("\n📸 Generating: Expert Street ADA Compliance")
    path1 = generator.generate_expert_street_ada_compliance()
    print(f"   ✅ Saved: {path1}")
    
    print("\n📸 Generating: Expert Transit Universal Design")
    path2 = generator.generate_expert_transit_universal_design()
    print(f"   ✅ Saved: {path2}")
    
    print("\n📸 Generating: Realistic Office Acoustic Scene")
    path3 = generator.generate_realistic_office_acoustic_scene()
    print(f"   ✅ Saved: {path3}")
    
    print("\n📸 Generating: Realistic Street Accessibility Scene")
    path4 = generator.generate_realistic_street_accessibility_scene()
    print(f"   ✅ Saved: {path4}")
    
    print("\n📸 Generating: Realistic Subway Accessibility Scene")
    path5 = generator.generate_realistic_subway_accessibility_scene()
    print(f"   ✅ Saved: {path5}")
    
    print("\n📸 Generating: Refined Accessibility Pathways")
    path6 = generator.generate_refined_accessibility_pathways()
    print(f"   ✅ Saved: {path6}")
    
    print("\n" + "=" * 50)
    print("✅ SOPHISTICATED ACCESSIBILITY PIXEL ART GENERATED!")
    print("All images are 800x450 pixels and use a sophisticated aesthetic.")

if __name__ == "__main__":
    main()