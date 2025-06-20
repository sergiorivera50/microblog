#!/usr/bin/env python3
"""
serve.py - A development server that watches for changes and rebuilds site
"""

import os
import time
from watchdog.events import FileSystemEventHandler
from livereload import Server
from pathlib import Path

from src.build import build_site, CONTENT_DIR, TEMPLATES_DIR, PUBLIC_DIR, CONFIG_FILE


class ChangeHandler(FileSystemEventHandler):
    """Handle file system change events and rebuild site"""

    def __init__(self, callback):
        self.callback = callback
        self.last_event_time = 0
        self.cooldown = 0.5  # seconds

    def on_any_event(self, event):
        # Skip temporary files and directories
        if event.src_path.endswith('.swp') or event.src_path.endswith('~'):
            return

        # Debounce multiple events
        current_time = time.time()
        if current_time - self.last_event_time < self.cooldown:
            return

        self.last_event_time = current_time
        print(f"Change detected: {event.src_path}")
        self.callback()

def get_watch_directories(config):
    """Get directories to watch based on configuration"""
    watch_dirs = []

    # Check if site requires an external source
    sync_config = config.get("sync", {})
    external_sync_path = sync_config.get("path")

    if external_sync_path:
        # Watch external source instead of content/blog
        external_path = Path(external_sync_path).expanduser()
        if external_path.exists():
            watch_dirs.append(str(external_path))

        # Still watch other content directories (not blog)
        content_path = Path(CONTENT_DIR)
        if content_path.exists():
            for item in content_path.iterdir():
                if item.is_dir() and item.name != 'blog':
                    watch_dirs.append(str(item))
    else:
        # Watch standard content directory
        if os.path.exists(CONTENT_DIR):
            watch_dirs.append(CONTENT_DIR)

    # Always watch templates, static, and config
    standard_dirs = [TEMPLATES_DIR, 'static', CONFIG_FILE]
    for watch_dir in standard_dirs:
        if os.path.exists(watch_dir):
            watch_dirs.append(watch_dir)

    return watch_dirs

def get_server_config(config):
    """Get server configuration from site.toml"""
    server_config = config.get("server", {})

    return {
        "port": server_config.get("port", 8000),
        "host": server_config.get("host", "localhost"),
        "open_browser": server_config.get("open_browser", True)
    }

def start_livereload_server():
    """Start the livereload server"""
    # First build the site
    config = build_site()

    # Create livereload server
    server = Server()

    # Watch directories for changes
    for watch_dir in get_watch_directories(config):
        if os.path.exists(watch_dir):
            server.watch(watch_dir, lambda: build_site())

    server_cfg = get_server_config(config)

    # Serve the site
    open_delay = 1 if server_cfg['open_browser'] else None
    server.serve(
        root=PUBLIC_DIR,
        port=server_cfg['port'],
        host=server_cfg['host'],
        open_url_delay=open_delay
    )

def main():
    try:
        print("Starting development server...")
        start_livereload_server()
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == "__main__":
    main()