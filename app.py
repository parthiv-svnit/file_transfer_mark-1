# ==============================================================================
# QuickDrop Application (v12 - Professional)
#
# A simple, local file sharing application.
# This script first opens a native GUI window to select a folder,
# then launches a Flask web server to share the contents of that folder.
# ==============================================================================

# --- Standard Library Imports ---
import os
import socket
import webbrowser
from threading import Timer
import tkinter as tk
from tkinter import filedialog

# --- Third-Party Library Imports ---
# This section checks if Flask is installed and provides a helpful error message.
try:
    from flask import Flask, send_from_directory, jsonify, abort
except ImportError:
    print("\n--- ERROR: Flask is not installed ---")
    print("QuickDrop requires the Flask library to run.")
    print("Please install it by running this command in your terminal:")
    print("\tpip install Flask\n")
    exit()

# ==============================================================================
# Configuration & Global Variables
# ==============================================================================

# These variables will be set after the user selects a folder.
# Using global variables is acceptable here because the application's state
# is simple and set only once at startup.
SHARED_DIRECTORY = ""
ROOT_FOLDER_NAME = ""
PORT = 5000

app = Flask(__name__)

# ==============================================================================
# Helper Functions
# ==============================================================================

def get_local_ip() -> str:
    """
    Finds the local IP address of the machine to display to the user.
    Returns the IP address as a string.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This is a dummy connection and doesn't have to be reachable.
        s.connect(('10.255.255.255', 1))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = '127.0.0.1'  # Fallback to localhost
    finally:
        s.close()
    return ip_address

def open_browser_after_delay():
    """Opens the web browser to the connection page after a short delay."""
    def _open():
        webbrowser.open_new(f'http://127.0.0.1:{PORT}')
    # Use a timer to ensure the server has time to start before the browser opens.
    Timer(1, _open).start()

# ==============================================================================
# API Endpoints (for the frontend to fetch data)
# ==============================================================================

@app.route('/api/info')
def get_info():
    """Provides the root folder name to the frontend."""
    return jsonify({'root_folder_name': ROOT_FOLDER_NAME})

@app.route('/api/files/')
@app.route('/api/files/<path:subpath>')
def list_files(subpath: str = ''):
    """
    Lists files and directories for the frontend file browser.
    Returns a JSON list of items in the requested directory.
    """
    directory = os.path.join(SHARED_DIRECTORY, subpath)
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return abort(404, "Directory not found")

    items = []
    for item_name in os.listdir(directory):
        item_path = os.path.join(directory, item_name)
        is_dir = os.path.isdir(item_path)
        try:
            items.append({
                'name': item_name,
                'path': os.path.join(subpath, item_name).replace("\\", "/"),
                'is_dir': is_dir,
                'size': os.path.getsize(item_path) if not is_dir else 0,
                'last_modified': os.path.getmtime(item_path)
            })
        except OSError:
            # Skip files that might be temporarily inaccessible (e.g., system files)
            continue
    return jsonify(items)

@app.route('/download/<path:filepath>')
def download_file(filepath: str):
    """Serves a single file for download."""
    abs_path = os.path.join(SHARED_DIRECTORY, filepath)
    if not os.path.exists(abs_path) or os.path.isdir(abs_path):
        return abort(404, "File not found")
    
    dir_path, filename = os.path.split(abs_path)
    return send_from_directory(dir_path, filename, as_attachment=True)
    
# ==============================================================================
# Web Page Routes (what the user sees)
# ==============================================================================

@app.route('/')
def connection_page():
    """Serves the main connection page with IP address and QR code."""
    ip_address = get_local_ip()
    # The HTML is embedded here for simplicity, making the app a single file.
    return f"""
    <!DOCTYPE html><html lang="en" class="dark"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connect to QuickDrop</title><script src="https://cdn.tailwindcss.com"></script><script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"><style>body {{ font-family: 'Inter', sans-serif; background-color: #111827; }}</style></head>
    <body class="flex items-center justify-center min-h-screen text-white"><div class="max-w-md w-full bg-gray-800 rounded-2xl shadow-2xl p-8 text-center">
    <div class="flex justify-center items-center gap-3 mb-4"><i class="fas fa-bolt-lightning text-4xl text-indigo-400"></i><h1 class="text-4xl font-bold">QuickDrop</h1></div>
    <p class="text-gray-400 mb-6">Scan the QR code or enter the address in your phone's browser.</p><div id="qrcode" class="flex justify-center p-4 bg-white rounded-lg mb-6"></div>
    <div class="bg-gray-900 rounded-lg p-4"><p class="text-lg font-mono break-all">http://{ip_address}:{PORT}/files</p></div></div><script>new QRCode(document.getElementById("qrcode"), {{ text: "http://{ip_address}:{PORT}/files", width: 256, height: 256, colorDark : "#000000", colorLight : "#ffffff", correctLevel : QRCode.CorrectLevel.H }});</script></body></html>
    """

@app.route('/files')
def files_page():
    """Serves the main file browser interface (index.html)."""
    # This assumes index.html is in the same directory as this script.
    return send_from_directory('.', 'index.html')

# ==============================================================================
# Main Application Logic
# ==============================================================================

def select_folder_and_start_server():
    """
    Uses Tkinter to open a native folder selection dialog, then starts the server.
    This is the main entry point of the application.
    """
    global SHARED_DIRECTORY, ROOT_FOLDER_NAME
    
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    
    print("--------------------------------------------------")
    print("A folder selection dialog has opened.")
    print("Please choose a folder to share with QuickDrop.")
    print("--------------------------------------------------")
    
    selected_path = filedialog.askdirectory(title="Select a Folder to Share")
    
    if selected_path:
        # Set the global variables with the chosen path
        SHARED_DIRECTORY = os.path.abspath(selected_path)
        ROOT_FOLDER_NAME = os.path.basename(SHARED_DIRECTORY)
        
        print(f"\n[INFO] Sharing folder: {SHARED_DIRECTORY}")
        print(f"[INFO] Access QuickDrop on other devices at: http://{get_local_ip()}:{PORT}/files\n")
        
        open_browser_after_delay()
        
        # Start the Flask web server
        # debug=False is important for performance and security in a shared script.
        app.run(host='0.0.0.0', port=PORT, debug=False)
    else:
        print("\n[INFO] No folder selected. QuickDrop will now exit.")

if __name__ == '__main__':
    select_folder_and_start_server()

