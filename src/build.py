#!/usr/bin/env python3
"""
build.py - Minimal static site generator that reads Markdown files and converts them to HTML
"""

import os
import tomli
import shutil
import frontmatter
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from src.utils import render_markdown, slugify

# Configuration
CONTENT_DIR = "content"
PUBLIC_DIR = "public"
TEMPLATES_DIR = "templates"
CONFIG_FILE = "site.toml"
DEFAULT_LAYOUT = "page.html"
POST_LAYOUT = "post.html"
LIST_LAYOUT = "list.html"
HOME_LAYOUT = "home.html"

def load_config():
    """Load configuration from a TOML file"""
    try:
        with open(CONFIG_FILE, "rb") as f:
            return tomli.load(f)
    except FileNotFoundError:
        raise Exception(f"Config file '{CONFIG_FILE}' not found")

def ensure_dir(directory):
    """Ensure directory exists"""
    Path(directory).mkdir(parents=True, exist_ok=True)

def copy_static_files():
    """Copy static files to public directory"""
    static_dir = Path("static")
    if static_dir.exists():
        for item in static_dir.glob("**/*"):
            if item.is_file():
                dest = Path(PUBLIC_DIR) / item.relative_to(static_dir)
                ensure_dir(dest.parent)
                shutil.copy2(item, dest)

def copy_content_assets():
    """Copy non-markdown files from content folders to public output"""
    content_path = Path(CONTENT_DIR)

    # Find all non-markdown files in content directory
    for asset in content_path.glob("**/*"):
        # Skip directories and markdown files
        if asset.is_dir() or asset.suffix in ['.md', '.markdown']:
            continue

        # Skip files in hidden folders (paths containing a folder starting with '.')
        if any(part.startswith('.') for part in asset.parts):
            continue

        # Determine destination path
        rel_path = asset.relative_to(content_path)
        dest_path = Path(PUBLIC_DIR) / rel_path

        # Create parent directories if they don't exist
        ensure_dir(dest_path.parent)

        # Copy the file
        shutil.copy2(asset, dest_path)

    print(f"Content assets copied.")

def get_nav_pages(pages):
    """Get pages to show in navigation"""
    nav_pages = []

    # Add Home
    nav_pages.append({
        'title': 'Home',
        'url': '/',
        'weight': 0
    })

    # Add top-level pages (directly in content dir, not index.md)
    for page in pages:
        if not page['is_post'] and not page['is_index'] and page['level'] == 0:
            nav_pages.append({
                'title': page['title'],
                'url': page['url'],
                'weight': page.get('metadata', {}).get('weight', 50)
            })

    # Add Blog link if the blog section exists
    blog_dir = Path(CONTENT_DIR) / "blog"
    if blog_dir.exists() and blog_dir.is_dir():
        nav_pages.append({
            'title': 'Blog',
            'url': '/blog/',
            'weight': 100
        })

    # Sort by weight
    nav_pages.sort(key=lambda x: x['weight'])
    return nav_pages

def process_content():
    """Process all markdown files in content directory"""
    pages = []
    posts = []
    sections = {}
    tags = {}

    content_path = Path(CONTENT_DIR)

    # Find all markdown files
    for md_file in content_path.glob("**/*.md"):
        # Skip files in hidden folders
        if any(part.startswith('.') for part in md_file.parts):
            continue

        # Skip drafts if draft mode is not enabled
        if md_file.stem.startswith('_') and md_file.stem != '_index':
            continue

        # Check if this is a blog post (in the blog directory)
        is_post = "blog" in md_file.parts and md_file.stem != '_index'

        # Check if this is an index file
        is_index = md_file.stem == '_index'

        # Check if this is a content index file (index.md in a content folder)
        is_content_index = md_file.stem == 'index'

        # Get directory level (0 = directly in content)
        level = len(md_file.relative_to(content_path).parts) - 1

        # Parse frontmatter and content
        page = frontmatter.load(md_file)

        # Extract or generate metadata
        title = page.get('title', md_file.stem.replace('-', ' ').title())
        date = page.get('date', datetime.fromtimestamp(md_file.stat().st_mtime).date())

        # Generate slug if not provided
        slug = page.get('slug', slugify(title) if not is_index else '')

        # Determine URL path and output path
        rel_path = md_file.relative_to(content_path).parent
        if is_index:
            # Section index files (_index.md)
            if rel_path == Path(''):
                # Root _index.md
                url = "/"
                output_path = Path(PUBLIC_DIR) / "index.html"
            else:
                # Section _index.md
                url = f"/{rel_path}/"
                output_path = Path(PUBLIC_DIR) / rel_path / "index.html"
        elif is_content_index:
            # Content index.md files (treat as the content for their directory)
            url = f"/{rel_path}/"
            output_path = Path(PUBLIC_DIR) / rel_path / "index.html"
        else:
            # Regular pages and posts
            if rel_path == Path(''):
                # Top-level page
                url = f"/{slug}/"
                output_path = Path(PUBLIC_DIR) / slug / "index.html"
            else:
                # Nested page
                url = f"/{rel_path}/{slug}/"
                output_path = Path(PUBLIC_DIR) / rel_path / slug / "index.html"

        # Determine layout template
        layout = page.get('layout', None)
        if layout is None:
            if is_index:
                layout = HOME_LAYOUT if rel_path == Path('') else LIST_LAYOUT
            elif is_post:
                layout = POST_LAYOUT
            else:
                layout = DEFAULT_LAYOUT

        page_obj = {
            'title': title,
            'date': date,
            'date_formatted': date.strftime("%d %b, %Y"),
            'content': render_markdown(page.content),
            'url': url,
            'output_path': output_path,
            'metadata': page.metadata,
            'is_post': is_post,
            'is_index': is_index,
            'section': rel_path.parts[0] if rel_path != Path('') else None,
            'level': level,
            'layout': layout
        }

        # Add to appropriate lists
        pages.append(page_obj)
        if is_post:
            posts.append(page_obj)

            post_tags = page.get('tags', [])
            if post_tags:
                for tag in post_tags:
                    tag_slug = slugify(tag)
                    if tag_slug not in tags:
                        tags[tag_slug] = {
                            'name': tag,
                            'slug': tag_slug,
                            'count': 0,
                            'posts': []
                        }
                    tags[tag_slug]['count'] += 1
                    tags[tag_slug]['posts'].append(page_obj)

        # Build section data
        if rel_path != Path('') and not is_post:
            section = rel_path.parts[0]
            if section not in sections:
                sections[section] = []

    # Sort posts by date, newest first
    posts.sort(key=lambda x: x['date'], reverse=True)

    # Group posts by section
    for post in posts:
        section = post['section']
        if section in sections:
            sections[section].append(post)

    return {
        'pages': pages,
        'posts': posts,
        'sections': sections,
        'nav': get_nav_pages(pages),
        'tags': tags
    }

def build_site():
    """Build the entire site"""
    # Load configuration
    config = load_config()

    # Setup Jinja environment
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

    # Add custom filters
    env.filters['slugify'] = slugify

    # Clean public directory
    if os.path.exists(PUBLIC_DIR):
        shutil.rmtree(PUBLIC_DIR)
    ensure_dir(PUBLIC_DIR)

    # Copy static files
    copy_static_files()

    # Copy asset files from content
    copy_content_assets()

    # Process content
    content = process_content()

    # Add current year for copyright
    config["current_year"] = datetime.now().year

    context = {
        "site": config,
        "pages": content['pages'],
        "posts": content['posts'],
        "sections": content['sections'],
        "nav": content['nav'],
        "tags": content['tags']
    }

    # Render all pages
    for page in content['pages']:
        template = env.get_template(page['layout'])
        page_context = context.copy()
        page_context["page"] = page

        # For section pages, add section-specific posts
        if page['is_index'] and page['section']:
            section_posts = content['sections'].get(page['section'], [])
            page_context["section_posts"] = section_posts

        html = template.render(**page_context)

        # Write output file
        ensure_dir(page['output_path'].parent)
        with open(page['output_path'], 'w') as f:
            f.write(html)

    # Generate tag pages for the blog
    if "blog" in content['sections'] and content['tags']:
        # Get the blog template
        tag_template = env.get_template(LIST_LAYOUT)

        # Create a tag page for each tag
        for tag_slug, tag_data in content['tags'].items():
            tag_dir = Path(PUBLIC_DIR) / "blog" / tag_slug
            ensure_dir(tag_dir)

            # Create page context
            tag_context = context.copy()
            tag_context["page"] = {
                'is_index': True,
                'section': 'blog',
                'is_tag_page': True,
                'tag': tag_data['name'],
                'tag_slug': tag_slug
            }
            tag_context["section_posts"] = tag_data['posts']
            tag_context["is_filtered"] = True
            tag_context["current_tag"] = tag_data['name']

            # Render and write tag page
            html = tag_template.render(**tag_context)
            with open(tag_dir / "index.html", 'w') as f:
                f.write(html)

    # Create 404 page
    if env.list_templates() and "404.html" in env.list_templates():
        template = env.get_template("404.html")
        html = template.render(**context)
        with open(f"{PUBLIC_DIR}/404.html", 'w') as f:
            f.write(html)

    print(f"Site built successfully! {len(content['pages'])} pages processed.")

if __name__ == "__main__":
    build_site()