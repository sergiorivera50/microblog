import markdown
import re
from pathlib import Path
from datetime import datetime
import os
import subprocess
import platform
from urllib.parse import quote

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'^\-|\-$', '', text)
    return text

def render_markdown(text):
    """
    Render markdown text to HTML with custom handling for:
    1. LaTeX blocks (preserved for later JS rendering)
    2. Custom image syntax with size specifications: ![alt|width](src)
    """

    # Store LaTeX parts
    placeholders = {}
    count = 0

    # Handle block LaTeX ($$...$$)
    def replace_block(match):
        nonlocal count
        placeholder = f"LATEX_BLOCK_{count}_"
        placeholders[placeholder] = match.group(0)
        count += 1
        return placeholder

    text = re.sub(r'(?<!\\)\$\$(.*?)(?<!\\)\$\$', replace_block, text, flags=re.DOTALL)

    # Handle inline LaTeX ($...$)
    def replace_inline(match):
        nonlocal count
        placeholder = f"LATEX_INLINE_{count}_"
        placeholders[placeholder] = match.group(0)
        count += 1
        return placeholder

    text = re.sub(r'(?<!\\)\$(.*?)(?<!\\)\$', replace_inline, text)

    # Process custom image syntax: ![alt|width](src)
    def process_images(match):
        alt_width = match.group(1)
        src = match.group(2)

        # Check if there's a width specification
        if '|' in alt_width:
            alt, width = alt_width.rsplit('|', 1)
            # Try to parse width as number (strip 'px' if present)
            width = width.strip()
            if width.endswith('px'):
                width = width[:-2]

            # If width is a valid number, add the width attribute
            if width.isdigit():
                return f'![{alt}]({src})<!-- img-width:{width} -->'

        # If no width specification or invalid format, return unchanged
        return f'![{alt_width}]({src})'

    # Process images with custom syntax
    text = re.sub(r'!\[(.*?)\]\((.*?)\)', process_images, text)

    # Process with markdown
    html = markdown.markdown(text, extensions=['fenced_code', 'codehilite', 'tables', 'md_in_html'])

    # Post-process HTML to add width attributes to images
    def add_image_width(match):
        img_tag = match.group(1)
        width = match.group(2)

        # If img tag already has a width attribute, don't modify
        if 'width=' in img_tag:
            return f'<img {img_tag}>'

        # Add width attribute
        return f'<img {img_tag} width="{width}">'

    # Add width attributes to images with comments
    html = re.sub(r'<img (.*?)><!-- img-width:(\d+) -->', add_image_width, html)

    # Restore LaTeX parts
    for placeholder, latex in placeholders.items():
        html = html.replace(placeholder, latex)

    return html

def open_in_obsidian(file_path):
    """Open a file in Obsidian using the obsidian:// protocol"""
    # Get the absolute path for the file and the content/blog directory
    abs_file_path = os.path.abspath(file_path)
    abs_blog_dir = os.path.abspath("content/blog")

    # (!) Vault name is assumed to always be "blog"
    vault_name = "blog"

    # Make the file path relative to the content/blog directory
    rel_path = os.path.relpath(abs_file_path, abs_blog_dir)

    # URL encode the paths for the URI
    vault_name_encoded = quote(vault_name)
    file_path_encoded = quote(rel_path)
    obsidian_url = f"obsidian://open?vault={vault_name_encoded}&file={file_path_encoded}"

    # Open the URL with the default system handler
    system = platform.system()

    try:
        if system == 'Darwin':  # macOS
            subprocess.run(['open', obsidian_url])
        elif system == 'Windows':
            subprocess.run(['start', obsidian_url], shell=True)
        elif system == 'Linux':
            subprocess.run(['xdg-open', obsidian_url])

        return True
    except Exception as e:
        print(f"Failed to open in Obsidian: {e}")
        return False

def create_new_post():
    """Create a new blog post with user-provided title"""
    # Ask the user for the post title
    title = input("Enter the title for your new blog post: ").strip()

    if not title:
        print("Error: Title cannot be empty")
        return

    # Create slug from title
    slug = slugify(title)

    # Define paths
    blog_dir = Path("content/blog")
    post_dir = blog_dir / slug

    # Ensure blog directory exists
    if not blog_dir.exists():
        print(f"Creating blog directory at {blog_dir}")
        blog_dir.mkdir(parents=True, exist_ok=True)

    # Check if post directory already exists
    if post_dir.exists():
        print(f"Error: A post with the slug '{slug}' already exists at {post_dir}")
        return

    # Create post directory
    post_dir.mkdir(parents=True, exist_ok=True)

    # Get today's date in YYYY-MM-DD format
    today = datetime.now().strftime("%Y-%m-%d")

    # Create frontmatter content
    frontmatter = f"""---
title: {title}
date: {today}
tags: []
math: false
---

Write your post content here...
"""

    # Create the index.md file
    index_file = post_dir / "index.md"
    with open(index_file, "w") as f:
        f.write(frontmatter)

    print(f"Created new blog post at {index_file}")
    print(f"Post URL will be: /blog/{slug}/")

    open_in_obsidian(index_file)
