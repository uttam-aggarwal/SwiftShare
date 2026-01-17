# file_explorer_unlimited.py
# Requires: pip install qrcode[pil] Flask

import os
import socket
import urllib.parse
from flask import Flask, request, send_file, render_template_string, jsonify
import qrcode
import io
import zipfile
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)

# CONFIGURATION
app.config['MAX_CONTENT_LENGTH'] = None 
app.config['TEMPLATES_AUTO_RELOAD'] = False

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Direct Stream Explorer</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #121212; color: #eee; margin: 0; padding: 20px; }
  .container { max-width: 900px; margin: auto; background: #1e1e1e; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
  h2 { color: #00bcd4; text-align: center; margin-bottom: 8px; }
  .qr-block { text-align: center; margin-bottom: 16px; }
  .qr-block img { width: 160px; height: 160px; border-radius: 12px; background: #fff; padding: 8px; }
  
  .upload-area { background: #2a2a2a; padding: 15px; border-radius: 8px; border: 1px dashed #444; text-align: center; }
  input[type=file] { display: none; }
  .custom-file-upload { border: 1px solid #00bcd4; display: inline-block; padding: 10px 20px; cursor: pointer; border-radius: 5px; color: #00bcd4; font-weight: bold; margin-bottom: 10px; }
  .custom-file-upload:hover { background: #00bcd4; color: #fff; }
  
  button#uploadBtn { background: #00bcd4; color: white; border: none; padding: 12px; border-radius: 6px; width: 100%; font-size: 1rem; cursor: pointer; margin-top: 10px; }
  button#uploadBtn:disabled { background: #555; cursor: not-allowed; }
  
  .progress-wrapper { margin-top: 15px; display: none; }
  progress { width: 100%; height: 20px; border-radius: 6px; }
  progress::-webkit-progress-bar { background-color: #333; border-radius: 6px; }
  progress::-webkit-progress-value { background-color: #00bcd4; border-radius: 6px; }

  ul { list-style: none; padding: 0; text-align: left; margin-top: 20px; }
  li { margin: 8px 0; background: #2a2a2a; padding: 12px; border-radius: 6px; word-wrap: break-word; display: flex; align-items: center; }
  .icon { margin-right: 10px; font-size: 1.2rem; }
  a { color: #00bcd4; text-decoration: none; flex-grow: 1; }
  a:hover { text-decoration: underline; }
  
  #statusMessage { text-align: center; margin-top: 10px; font-size: 0.9rem; font-weight: bold; }
  #currentFileLabel { font-size: 0.85rem; color: #aaa; margin-bottom: 5px; display:block; text-align: left;}
</style>
</head>
<body>
<div class="container">
  <h2>🚀 Direct Stream (Unlimited)</h2>

  {% if qr_img %}
  <div class="qr-block">
    <img src="{{ qr_img }}" alt="Scan to open on phone" />
    <div style="margin-top:5px; font-size:0.9rem; color:#aaa;">{{ access_url }}</div>
  </div>
  {% endif %}

  <div class="upload-area">
      <input type="hidden" id="targetPath" value="{{ abs_path }}">
      
      <label for="fileInput" class="custom-file-upload">
        📂 Select Files
      </label>
      <input type="file" id="fileInput" multiple onchange="updateCount()">
      <div id="fileCount" style="color:#aaa;">No files selected</div>

      <div class="progress-wrapper" id="progressWrapper">
          <span id="currentFileLabel">Waiting...</span>
          <progress id="progressBar" value="0" max="100"></progress>
      </div>
      
      <div id="statusMessage"></div>
      <button id="uploadBtn" onclick="startUploadQueue()">Upload Selected Files</button>
  </div>

  <h3>Directory: {{ abs_path }}</h3>

  {% if parent_link %}
    <p><a href="{{ parent_link }}">⬆️ Go up one level</a></p>
  {% endif %}

  <ul>
  {% for folder in folders %}
    <li><span class="icon">📁</span> <a href="{{ url_for('browse') }}?path={{ folder_paths[loop.index0] }}">{{ folder }}</a></li>
  {% endfor %}
  {% for file in files %}
    <li><span class="icon">📄</span> <a href="{{ url_for('download') }}?path={{ file_paths[loop.index0] }}">{{ file }}</a></li>
  {% endfor %}
  </ul>
</div>

<script>
function updateCount() {
    var input = document.getElementById('fileInput');
    var countDisplay = document.getElementById('fileCount');
    if (input.files.length > 0) {
        countDisplay.textContent = input.files.length + " file(s) selected";
        countDisplay.style.color = "#00bcd4";
    } else {
        countDisplay.textContent = "No files selected";
        countDisplay.style.color = "#aaa";
    }
}

async function startUploadQueue() {
    var input = document.getElementById('fileInput');
    var targetPath = document.getElementById('targetPath').value;
    var btn = document.getElementById('uploadBtn');
    var statusMsg = document.getElementById('statusMessage');
    var progressWrapper = document.getElementById('progressWrapper');
    
    if(input.files.length === 0) {
        alert("Please select files first!");
        return;
    }

    btn.disabled = true;
    progressWrapper.style.display = 'block';
    
    // Iterate through files one by one (Sequential Upload)
    for (let i = 0; i < input.files.length; i++) {
        let file = input.files[i];
        try {
            await uploadSingleFile(file, targetPath, i + 1, input.files.length);
        } catch (error) {
            statusMsg.style.color = "#ff4444";
            statusMsg.textContent = "Error uploading " + file.name + ": " + error;
            btn.disabled = false;
            return; 
        }
    }

    statusMsg.style.color = "#00ff00";
    statusMsg.textContent = "All files uploaded! Reloading...";
    setTimeout(function() { location.reload(); }, 1000);
}

function uploadSingleFile(file, path, index, total) {
    return new Promise((resolve, reject) => {
        var xhr = new XMLHttpRequest();
        var progressBar = document.getElementById('progressBar');
        var currentLabel = document.getElementById('currentFileLabel');
        var statusMsg = document.getElementById('statusMessage');

        // Note: Using a query param for the path logic, but sending raw binary body
        var url = '/upload_stream?path=' + encodeURIComponent(path);
        
        xhr.open('POST', url, true);
        
        // Critical Headers for the Python script
        xhr.setRequestHeader("X-File-Name", encodeURIComponent(file.name));
        xhr.setRequestHeader("Content-Type", "application/octet-stream");

        currentLabel.textContent = `Uploading ${index}/${total}: ${file.name} (${(file.size / (1024*1024)).toFixed(2)} MB)`;
        statusMsg.textContent = "Uploading...";
        statusMsg.style.color = "#eee";

        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                var percent = (e.loaded / e.total) * 100;
                progressBar.value = percent;
            }
        };

        xhr.onload = function() {
            if (xhr.status == 200) {
                resolve();
            } else {
                var resp = {};
                try { resp = JSON.parse(xhr.responseText); } catch(e){}
                reject(resp.message || xhr.statusText);
            }
        };

        xhr.onerror = function() {
            reject("Network Error");
        };

        // Send the file directly (RAW STREAM), not as FormData
        xhr.send(file);
    });
}
</script>
</body>
</html>
'''

def decode_path(raw_path):
    if not raw_path:
        return os.path.abspath("/") 
    decoded = urllib.parse.unquote(raw_path)
    return os.path.abspath(decoded)

@app.route('/')
@app.route('/browse')
def browse():
    raw_path = request.args.get('path', '')
    abs_path = decode_path(raw_path)

    folders, files = [], []
    folder_paths, file_paths = [], []

    try:
        for entry in sorted(os.listdir(abs_path)):
            full_entry = os.path.join(abs_path, entry)
            if os.path.isdir(full_entry):
                folders.append(entry)
                folder_paths.append(urllib.parse.quote(full_entry))
            else:
                files.append(entry)
                file_paths.append(urllib.parse.quote(full_entry))
    except Exception as e:
        return f"<h3 style='color:red;'>Error accessing {abs_path}: {e}</h3>"

    parent_link = None
    parent_dir = os.path.dirname(abs_path)
    if abs_path != parent_dir:
        parent_link = f"/browse?path={urllib.parse.quote(parent_dir)}"

    qr_img = None
    static_folder = os.path.join(app.root_path, 'static')
    if os.path.exists(os.path.join(static_folder, 'access_qr.png')):
        qr_img = '/static/access_qr.png'

    access_url = generate_access_url_display()
    return render_template_string(
        HTML,
        folders=folders,
        files=files,
        folder_paths=folder_paths,
        file_paths=file_paths,
        parent_link=parent_link,
        abs_path=abs_path,
        qr_img=qr_img,
        access_url=access_url
    )

@app.route('/download')
def download():
    raw_path = request.args.get('path', '')
    abs_path = decode_path(raw_path)

    if os.path.isfile(abs_path):
        return send_file(abs_path, as_attachment=True)
    elif os.path.isdir(abs_path):
        memory_file = io.BytesIO()
        try:
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(abs_path):
                    for f in files:
                        full_path = os.path.join(root, f)
                        zf.write(full_path, os.path.relpath(full_path, abs_path))
            memory_file.seek(0)
            return send_file(memory_file, download_name=f"{os.path.basename(abs_path)}.zip", as_attachment=True)
        except Exception as e:
             return f"<h3 style='color:red;'>Zip Error: {e}</h3>"
    else:
        return f"<h3 style='color:red;'>Not a valid file or folder: {abs_path}</h3>"

@app.route('/upload_stream', methods=['POST'])
def upload_stream():
    """
    Handles raw binary stream upload. 
    Does not use Flask's request.files/request.form which triggers temp files.
    Reads directly from the network socket to the final file.
    """
    target_dir = request.args.get('path', '')
    target_dir = decode_path(target_dir)
    
    # Get filename from header (sent by JS)
    raw_filename = request.headers.get('X-File-Name')
    if not raw_filename:
        raw_filename = f"unknown_{int(time.time())}.dat"
    else:
        raw_filename = urllib.parse.unquote(raw_filename)
        
    clean_name = secure_filename(raw_filename)
    full_save_path = os.path.join(target_dir, clean_name)
    
    # 1. CHECK DISK SPACE (Pre-flight)
    # The 'Content-Length' header tells us the size of THIS specific file
    try:
        file_size = int(request.headers.get('Content-Length', 0))
        total, used, free = shutil.disk_usage(target_dir)
        
        # Buffer of 1MB
        if file_size > (free - 1024*1024):
            print(f"❌ Rejected {clean_name}: Need {file_size}, Free {free}")
            return jsonify({
                "message": f"Not enough space for {clean_name}. Need {file_size//(1024*1024)}MB"
            }), 507
    except ValueError:
        pass # If content-length is missing, we proceed (risky but rare)

    # 2. STREAM DIRECTLY TO DISK
    print(f"⬇️ Streaming {clean_name} directly to {target_dir}")
    
    try:
        with open(full_save_path, 'wb') as f:
            # Read in 1MB chunks from the network socket
            chunk_size = 1024 * 1024 
            while True:
                chunk = request.stream.read(chunk_size)
                if len(chunk) == 0:
                    break
                f.write(chunk)
                
        print(f"✅ Finished: {clean_name}")
        return jsonify({"message": "Upload successful"})
        
    except Exception as e:
        print(f"❌ Stream Error: {e}")
        return jsonify({"message": str(e)}), 500

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def generate_access_url_display(host_ip=None, port=8000):
    if host_ip is None:
        host_ip = get_local_ip()
    return f"http://{host_ip}:{port}"

def generate_and_save_qr(url, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(out_path)

if __name__ == '__main__':
    PORT = 8000
    ip = get_local_ip()
    url = generate_access_url_display(ip, PORT)
    
    static_dir = os.path.join(app.root_path, 'static')
    os.makedirs(static_dir, exist_ok=True)
    
    qr_out = os.path.join(static_dir, 'access_qr.png')
    generate_and_save_qr(url, qr_out)

    print("-" * 50)
    print(f"🚀 DIRECT STREAM SERVER STARTED")
    print(f"📱 Access here: {url}")
    print("-" * 50)
    
    app.run(host='0.0.0.0', port=PORT, threaded=True, debug=False)
