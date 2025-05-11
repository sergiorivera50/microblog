#!/usr/bin/env python3
"""
serve.py - A development server that watches for changes and rebuilds site
"""

import os
import time
from watchdog.events import FileSystemEventHandler
from livereload import Server

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

def start_livereload_server():
    """Start the livereload server"""
    # First build the site
    build_site()

    # Create livereload server
    server = Server()

    # Watch directories for changes
    watch_dirs = [CONTENT_DIR, TEMPLATES_DIR, 'static', CONFIG_FILE]
    for watch_dir in watch_dirs:
        if os.path.exists(watch_dir):
            server.watch(watch_dir, lambda: build_site())

    # Serve the site
    server.serve(root=PUBLIC_DIR, port=8000, host='localhost', open_url_delay=1)

def main():
    """Main function"""
    print("Starting development server...")
    print("Watching for changes in content, templates, and static directories")
    print("Access your site at http://localhost:8000")

    try:
        start_livereload_server()
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == "__main__":
    main()