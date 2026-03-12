#!/usr/bin/env python3
"""
Regenerate sophisticated images for today's article
The SophisticatedArtGenerator already saves images to assets/ directory
"""

from generate_sophisticated_art_simple import SophisticatedArtGenerator
import os
import re

def regenerate_todays_images():
    """Regenerate images for March 12 article with sophisticated generator"""
    
    # Today's date (fixed to 2026-03-12 for this specific article)
    today_date_str = "2026-03-12"
    article_slug = "beethoven-s-disability-score-how-mathematical-order-and-lived-experience-create-true-accessibility"
    
    print("Creating SophisticatedArtGenerator...")
    generator = SophisticatedArtGenerator(width=800, height=450)
    
    print("Generating sophisticated images...")
    
    # The generator methods already save the images to assets/ directory
    # They return the file path as a string
    image1_path = generator.generate_acoustic_harmony()
    image2_path = generator.generate_sensory_expertise()
    
    print(f"✓ Generated image 1: {image1_path}")
    print(f"✓ Generated image 2: {image2_path}")
    
    # Now rename them to match the article slug
    assets_dir = "assets"
    
    # The generated files have default names like "acoustic_harmony_sophisticated.png"
    # We need to rename them to match the article
    old_name1 = "acoustic_harmony_sophisticated.png"
    old_name2 = "sensory_expertise_sophisticated.png"
    
    new_name1 = f"{today_date_str}-{article_slug}_sophisticated_1.png"
    new_name2 = f"{today_date_str}-{article_slug}_sophisticated_2.png"
    
    old_path1 = os.path.join(assets_dir, old_name1)
    new_path1 = os.path.join(assets_dir, new_name1)
    
    old_path2 = os.path.join(assets_dir, old_name2)
    new_path2 = os.path.join(assets_dir, new_name2)
    
    # Rename the files
    if os.path.exists(old_path1):
        os.rename(old_path1, new_path1)
        print(f"✓ Renamed: {old_name1} → {new_name1}")
    
    if os.path.exists(old_path2):
        os.rename(old_path2, new_path2)
        print(f"✓ Renamed: {old_name2} → {new_name2}")
    
    # Update article markdown with new image references
    posts_dir = "_posts"
    article_file = os.path.join(posts_dir, f"{today_date_str}-{article_slug}.md")
    
    if os.path.exists(article_file):
        print(f"\nUpdating {article_file} with new image references...")
        
        with open(article_file, 'r') as f:
            content = f.read()
        
        # Replace old image references with new sophisticated ones
        old_image1_ref = "{{ site.baseurl }}/assets/2026-03-12-beethoven-s-disability-score-how-mathematical-order-and-lived-experience-create-true-accessibility_pixel_art_1.png"
        new_image1_ref = "{{ site.baseurl }}/assets/2026-03-12-beethoven-s-disability-score-how-mathematical-order-and-lived-experience-create-true-accessibility_sophisticated_1.png"
        
        old_image2_ref = "{{ site.baseurl }}/assets/2026-03-12-beethoven-s-disability-score-how-mathematical-order-and-lived-experience-create-true-accessibility_pixel_art_2.png"
        new_image2_ref = "{{ site.baseurl }}/assets/2026-03-12-beethoven-s-disability-score-how-mathematical-order-and-lived-experience-create-true-accessibility_sophisticated_2.png"
        
        content = content.replace(old_image1_ref, new_image1_ref)
        content = content.replace(old_image2_ref, new_image2_ref)
        
        with open(article_file, 'w') as f:
            f.write(content)
        
        print("✓ Article markdown updated with new image references")
    else:
        print(f"✗ Article file not found: {article_file}")
        return False
    
    print(f"\n✓ Successfully regenerated sophisticated images for today's article")
    return True

if __name__ == '__main__':
    # Ensure we are in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    success = regenerate_todays_images()
    exit(0 if success else 1)
