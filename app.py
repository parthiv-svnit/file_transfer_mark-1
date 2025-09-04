import socket
import sys
import webbrowser
import os
import html
import threading
import posixpath # Use this for URL path manipulation

# --- Part 1: Dependency Check ---
try:
    from flask import Flask, jsonify, send_from_directory, abort, render_template_string
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    print("="*60)
    print("FATAL ERROR: A required library is not installed.")
    print("Please open your terminal (Command Prompt/PowerShell) and run this command:")
    print("pip install Flask")
    print("="*60)
    sys.exit(1)

# --- Part 2: Global State and Configuration ---
SHARED_FOLDER_PATH = None
APP_PORT = 5000

app = Flask(__name__)

# --- Part 3: The Core Application Logic ---

def get_local_ip():
    """Finds the computer's local IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

@app.route('/')
def index():
    """Serves the main user interface."""
    return send_from_directory('.', 'index.html')

@app.route('/status')
def status():
    """Provides the status of the current share."""
    if SHARED_FOLDER_PATH:
        return jsonify(
            sharing=True, 
            folder=os.path.basename(SHARED_FOLDER_PATH), 
            ip=get_local_ip(), 
            port=APP_PORT
        )
    return jsonify(sharing=False, error="No folder has been selected.")

@app.route('/shared/', defaults={'subpath': ''})
@app.route('/shared/<path:subpath>')
def serve_shared_content(subpath):
    """Serves the shared folder's contents (files and directory listings)."""
    if not SHARED_FOLDER_PATH:
        return abort(404, "Sharing is not active.")

    # Convert URL path to a safe OS-specific path
    # e.g., 'folder/file.txt' becomes 'folder\file.txt' on Windows
    local_path = os.path.join(SHARED_FOLDER_PATH, *subpath.split('/'))
    
    # Security Check: Prevent access outside the shared folder
    if not os.path.abspath(local_path).startswith(os.path.abspath(SHARED_FOLDER_PATH)):
        return abort(403, "Forbidden")

    if not os.path.exists(local_path):
        return abort(404)

    if os.path.isdir(local_path):
        # Generate an HTML page for directory listing
        items = os.listdir(local_path)
        dirs = sorted([d for d in items if os.path.isdir(os.path.join(local_path, d))], key=str.lower)
        files = sorted([f for f in items if not os.path.isdir(os.path.join(local_path, f))], key=str.lower)
        
        # CORRECTED: Use posixpath for URL-safe path manipulation
        parent_path = posixpath.dirname(subpath)
        parent_link = f'<li><a href="/shared/{parent_path}">⬆️ Parent Directory</a></li>' if subpath else ''
        links = parent_link
        for d in dirs: links += f'<li class="dir"><a href="/shared/{posixpath.join(subpath, d)}">{html.escape(d)}/</a></li>'
        for f in files: links += f'<li class="file"><a href="/shared/{posixpath.join(subpath, f)}">{html.escape(f)}</a></li>'
        
        return render_template_string(f"""
            <!DOCTYPE html><html lang="en"><head><title>Files</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;margin:2em;background:#f8f9fa;}}a{{color:#007bff;text-decoration:none;}}ul{{list-style:none;padding:0}}li{{display:flex;align-items:center;padding:.5em;border-radius:8px;}}li:hover{{background-color:#e9ecef;}}li a{{font-size:1.1em;}}li::before{{font-size:1.5em;margin-right:.75em;}}li.dir::before{{content:'📁';}}li.file::before{{content:'📄';}}</style>
            </head><body><ul>{links}</ul></body></html>
        """)
    else:
        # Serve the requested file for download
        return send_from_directory(os.path.dirname(local_path), os.path.basename(local_path))

# --- Part 4: Main Execution ---
if __name__ == '__main__':
    if not os.path.exists('index.html'):
        print("[ERROR] 'index.html' not found. It must be in the same folder as 'app.py'.")
        sys.exit(1)

    # STEP 1: Ask the user to select a folder immediately
    print("[*] Please select the folder you want to share...")
    root = tk.Tk()
    root.withdraw() # Hide the empty tkinter window
    SHARED_FOLDER_PATH = filedialog.askdirectory(title="Select a Folder to Share with QuickDrop")
    root.destroy()
    
    if not SHARED_FOLDER_PATH:
        print("[!] No folder selected. Exiting application.")
        sys.exit(0)

    # STEP 2: Only start the web server AFTER a folder has been chosen
    url = f"http://127.0.0.1:{APP_PORT}"
    print("="*60)
    print("🚀 QuickDrop Server is RUNNING")
    print(f"   Sharing Folder -> {SHARED_FOLDER_PATH}")
    print(f"   Your control panel is opening at: {url}")
    print("   (This terminal window must stay open)")
    print("="*60)
    
    threading.Timer(1, lambda: webbrowser.open(url)).start()
    
    app.run(host='0.0.0.0', port=APP_PORT)

