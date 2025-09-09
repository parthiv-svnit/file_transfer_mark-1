# ==============================================================================
# QuickDrop for Termux (v16 - with Defaults)
#
# This version is specifically for non-GUI environments like Termux.
# It now defaults to sharing the standard ~/storage/downloads folder,
# making the --dir argument optional for the most common use case.
# ==============================================================================

# --- Standard Library Imports ---
import os
import socket
import argparse

# --- Third-Party Library Imports ---
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
SHARED_DIRECTORY = ""
ROOT_FOLDER_NAME = ""
PORT = 5000

app = Flask(__name__)

# ==============================================================================
# Helper Functions
# ==============================================================================

def get_local_ip() -> str:
    """Finds the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This is a dummy connection and doesn't have to be reachable.
        s.connect(('10.255.255.255', 1))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = '127.0.0.1'
    finally:
        s.close()
    return ip_address

# ==============================================================================
# API & Web Routes
# ==============================================================================

@app.route('/api/info')
def get_info():
    return jsonify({'root_folder_name': ROOT_FOLDER_NAME})

@app.route('/api/files/')
@app.route('/api/files/<path:subpath>')
def list_files(subpath: str = ''):
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
            continue
    return jsonify(items)

@app.route('/download/<path:filepath>')
def download_file(filepath: str):
    abs_path = os.path.join(SHARED_DIRECTORY, filepath)
    if not os.path.exists(abs_path) or os.path.isdir(abs_path):
        return abort(404, "File not found")
    
    dir_path, filename = os.path.split(abs_path)
    return send_from_directory(dir_path, filename, as_attachment=True)

@app.route('/')
def connection_page():
    ip_address = get_local_ip()
    # This is the multi-line f-string. It must start with f""" and end with """.
    return f"""
    <!DOCTYPE html><html lang="en" class="dark"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connect to QuickDrop</title><script src="https://cdn.tailwindcss.com"></script><script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"><style>body {{ font-family: 'Inter', sans-serif; background-color: #111827; }}</style></head>
    <body class="flex items-center justify-center min-h-screen text-white"><div class="max-w-md w-full bg-gray-800 rounded-2xl shadow-2xl p-8 text-center">
    <div class="flex justify-center items-center gap-3 mb-4"><i class="fas fa-bolt-lightning text-4xl text-indigo-400"></i><h1 class="text-4xl font-bold">QuickDrop</h1></div>
    <p class="text-gray-400 mb-6">Scan the QR code or enter the address in your PC's browser.</p><div id="qrcode" class="flex justify-center p-4 bg-white rounded-lg mb-6"></div>
    <div class="bg-gray-900 rounded-lg p-4"><p class="text-lg font-mono break-all">http://{ip_address}:{PORT}/files</p></div></div><script>new QRCode(document.getElementById("qrcode"), {{ text: "http://{ip_address}:{PORT}/files", width: 256, height: 256, colorDark : "#000000", colorLight : "#ffffff", correctLevel : QRCode.CorrectLevel.H }});</script></body></html>
    """

@app.route('/files')
def files_page():
    return send_from_directory('.', 'index.html')

# ==============================================================================
# Main Application Logic for Termux
# ==============================================================================

def start_server(directory: str):
    """Starts the Flask server with the specified directory."""
    global SHARED_DIRECTORY, ROOT_FOLDER_NAME
    
    # Use os.path.expanduser to handle the '~' character correctly
    full_path = os.path.expanduser(directory)

    if not os.path.isdir(full_path):
        print(f"\n[ERROR] The directory does not exist: {full_path}")
        print("Please provide a valid path or check permissions.\n")
        return

    SHARED_DIRECTORY = os.path.abspath(full_path)
    ROOT_FOLDER_NAME = os.path.basename(SHARED_DIRECTORY)
    
    print(f"\n[INFO] Sharing folder: {SHARED_DIRECTORY}")
    print(f"[INFO] Access QuickDrop on other devices at: http://{get_local_ip()}:{PORT}/files")
    print("\nPress CTRL+C to stop the server.")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    # Define the default path to the standard Termux downloads folder
    default_downloads_path = '~/storage/downloads'
    
    parser = argparse.ArgumentParser(description="QuickDrop for Termux: Share a folder from your phone.")
    
    # Make the --dir argument optional and set its default value
    parser.add_argument(
        "--dir", 
        default=default_downloads_path,
        help=f"The full path to the directory to share. Defaults to your downloads folder: {default_downloads_path}"
    )
    args = parser.parse_args()
    
    start_server(args.dir)

