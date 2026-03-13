#!/usr/bin/env python3
"""
Generate static HTML for a Jekyll post markdown file.
"""

import os
import re
import sys
from pathlib import Path

def extract_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    frontmatter = {}
    if content.startswith('---\n'):
        parts = content.split('---\n', 2)
        if len(parts) >= 3:
            yaml_content = parts[1]
            for line in yaml_content.strip().split('\n'):
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    # Clean up values
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith('[') and value.endswith(']'):
                        # Handle arrays
                        value = [v.strip().strip('"') for v in value[1:-1].split(',')]
                    frontmatter[key] = value
    return frontmatter

def markdown_to_html(markdown):
    """Simple markdown to HTML conversion for basic elements."""
    # Convert headers
    markdown = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', markdown, flags=re.MULTILINE)
    markdown = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', markdown, flags=re.MULTILINE)
    markdown = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', markdown, flags=re.MULTILINE)
    
    # Convert bold
    markdown = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', markdown)
    
    # Convert italic
    markdown = re.sub(r'\*(.*?)\*', r'<em>\1</em>', markdown)
    
    # Convert paragraphs
    lines = markdown.split('\n')
    html_lines = []
    in_paragraph = False
    current_paragraph = []
    
    for line in lines:
        if line.strip() == '':
            if current_paragraph:
                html_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
                in_paragraph = False
            continue
        
        # Skip headers (already converted)
        if line.startswith('<h'):
            if current_paragraph:
                html_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            html_lines.append(line)
            continue
        
        # Add to current paragraph
        current_paragraph.append(line.strip())
        in_paragraph = True
    
    # Add final paragraph if exists
    if current_paragraph:
        html_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
    
    return '\n'.join(html_lines)

def generate_article_html(markdown_path, output_dir):
    """Generate HTML for a single article."""
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract frontmatter
    frontmatter = extract_frontmatter(content)
    
    # Remove frontmatter from content
    if content.startswith('---\n'):
        parts = content.split('---\n', 2)
        if len(parts) >= 3:
            markdown_content = parts[2]
    
    # Convert markdown to HTML
    html_content = markdown_to_html(markdown_content)
    
    # Read template
    template_path = Path('_layouts/post.html')
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    else:
        # Fallback template
        template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <link rel="stylesheet" href="/disability-ai-collective/main.css">
</head>
<body>
    <header>
        <h1><a href="/disability-ai-collective/">Crip Minds Meet AI Minds</a></h1>
    </header>
    <main>
        <article>
            <h1>{{title}}</h1>
            <div class="meta">
                <span class="author">By {{author}}</span>
                <span class="date">{{date}}</span>
            </div>
            <div class="content">
                {{content}}
            </div>
        </article>
    </main>
    <footer>
        <p>Disability-Led AI Arts Journal</p>
    </footer>
</body>
</html>"""
    
    # Replace template variables
    html = template
    html = html.replace('{{title}}', frontmatter.get('title', 'Untitled'))
    html = html.replace('{{author}}', frontmatter.get('author', 'Unknown'))
    html = html.replace('{{date}}', frontmatter.get('date', ''))
    html = html.replace('{{content}}', html_content)
    
    # Create output directory
    date_parts = frontmatter.get('date', '').split('-')
    if len(date_parts) >= 3:
        year, month, day = date_parts[:3]
        article_slug = Path(markdown_path).stem.replace(f'{year}-{month}-{day}-', '')
        output_path = Path(output_dir) / year / month / day / f'{article_slug}.html'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Generated: {output_path}")
        return str(output_path)
    
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_article_html.py <markdown_file> [output_dir]")
        sys.exit(1)
    
    markdown_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    
    if not os.path.exists(markdown_file):
        print(f"Error: File not found: {markdown_file}")
        sys.exit(1)
    
    generate_article_html(markdown_file, output_dir)

if __name__ == '__main__':
    main()