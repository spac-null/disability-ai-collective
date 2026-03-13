#!/usr/bin/env python3
"""
REGENERATE ALL ARTICLE IMAGES
Complete regeneration of high-quality images for all articles
"""

import os
import re
from pathlib import Path
from generate_sophisticated_art_simple import SophisticatedArtGenerator

class ArticleImageRegeneration:
    def __init__(self):
        self.generator = SophisticatedArtGenerator(width=800, height=450)
        self.posts_dir = Path('_posts')
        self.assets_dir = Path('assets')
        
        # Available sophisticated image types
        self.image_types = [
            ('concept', 'generate_acoustic_chaos', 'Primary concept visualization'),
            ('context', 'generate_acoustic_harmony', 'Real-world context illustration'),
            ('solution', 'generate_sensory_expertise', 'Accessible solution design')
        ]

    def extract_slug_from_filename(self, filename):
        """Extract slug from article filename."""
        # Remove date prefix and .md suffix
        slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', filename)
        slug = re.sub(r'\.md$', '', slug)
        return slug

    def extract_title_from_content(self, content):
        """Extract title from article frontmatter."""
        match = re.search(r'title:\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        
        match = re.search(r'title:\s*([^\n]+)', content)
        if match:
            return match.group(1).strip()
        
        return "Article"

    def generate_images_for_article(self, article_file):
        """Generate 3 sophisticated images for an article."""
        print(f"\n🎨 Processing: {article_file}")
        
        # Read article content
        with open(self.posts_dir / article_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata
        slug = self.extract_slug_from_filename(article_file)
        title = self.extract_title_from_content(content)
        
        print(f"   Title: {title}")
        print(f"   Slug: {slug}")
        
        # Generate images
        generated_images = []
        
        for i, (img_type, method_name, description) in enumerate(self.image_types):
            method = getattr(self.generator, method_name)
            png_data = method()
            
            filename = f"{slug}_{img_type}_{i+1}.png"
            filepath = self.assets_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(png_data)
            
            file_size = os.path.getsize(filepath)
            generated_images.append({
                'filename': filename,
                'type': img_type,
                'description': description,
                'size': file_size
            })
            
            print(f"   ✅ {filename} - {file_size/1024:.1f}KB - {description}")
        
        return generated_images

    def update_article_image_references(self, article_file, generated_images):
        """Update article to reference new images."""
        print(f"   🔄 Updating image references in {article_file}")
        
        with open(self.posts_dir / article_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        slug = self.extract_slug_from_filename(article_file)
        
        # Update frontmatter image (use first image)
        main_image = generated_images[0]['filename']
        content = re.sub(
            r'image:\s*/assets/[^\n]+',
            f'image: /assets/{main_image}',
            content
        )
        
        # Update image references in content
        # Replace any existing image references with new ones
        
        # Find existing image patterns and replace them
        existing_images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        
        if len(existing_images) >= len(generated_images):
            # Replace existing images with new ones
            new_content = content
            for i, (alt_text, old_url) in enumerate(existing_images[:len(generated_images)]):
                if i < len(generated_images):
                    new_filename = generated_images[i]['filename']
                    new_alt = f"{generated_images[i]['description']} for {slug.replace('-', ' ')}"
                    new_url = f"{{{{ site.baseurl }}}}/assets/{new_filename}"
                    
                    # Replace the specific image
                    old_pattern = re.escape(f"![{alt_text}]({old_url})")
                    new_image = f"![{new_alt}]({new_url})"
                    new_content = new_content.replace(f"![{alt_text}]({old_url})", new_image)
            
            content = new_content
        
        # Write updated content
        with open(self.posts_dir / article_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Updated image references")

    def cleanup_old_images(self, article_file):
        """Remove old images for this article."""
        slug = self.extract_slug_from_filename(article_file)
        
        # Find and remove old image files
        old_patterns = [
            f"{slug}_pixel_art_*.png",
            f"{slug}_sophisticated_*.png", 
            f"*{slug}*.png"
        ]
        
        removed_count = 0
        for asset_file in self.assets_dir.glob("*.png"):
            asset_name = asset_file.name
            
            # Check if this is an old image for this article
            if (slug in asset_name and 
                not any(f"_{img_type}_" in asset_name for img_type, _, _ in self.image_types)):
                
                try:
                    asset_file.unlink()
                    print(f"   🗑️ Removed old image: {asset_name}")
                    removed_count += 1
                except Exception as e:
                    print(f"   ⚠️ Could not remove {asset_name}: {e}")
        
        if removed_count == 0:
            print(f"   ℹ️ No old images found to clean up")

    def regenerate_all_articles(self):
        """Regenerate images for all articles."""
        print("🚀 REGENERATING ALL ARTICLE IMAGES")
        print("=" * 60)
        
        article_files = sorted([f for f in os.listdir(self.posts_dir) if f.startswith('2026-03-') and f.endswith('.md')])
        
        total_generated = 0
        total_size = 0
        
        for article_file in article_files:
            try:
                # Clean up old images first
                self.cleanup_old_images(article_file)
                
                # Generate new images
                generated_images = self.generate_images_for_article(article_file)
                
                # Update article references
                self.update_article_image_references(article_file, generated_images)
                
                # Track totals
                total_generated += len(generated_images)
                total_size += sum(img['size'] for img in generated_images)
                
            except Exception as e:
                print(f"   ❌ Error processing {article_file}: {e}")
                continue
        
        print(f"\n✅ REGENERATION COMPLETE!")
        print(f"   Articles processed: {len(article_files)}")
        print(f"   Images generated: {total_generated}")
        print(f"   Total size: {total_size/1024/1024:.1f}MB")
        print(f"   Average per image: {(total_size/total_generated)/1024:.1f}KB")


if __name__ == "__main__":
    regenerator = ArticleImageRegeneration()
    regenerator.regenerate_all_articles()