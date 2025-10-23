from flask import Flask, request, send_file, render_template_string, jsonify, redirect, url_for
import os
import urllib.parse

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Full Access Explorer</title>
<style>
  body { font-family: Arial, sans-serif; background: #121212; color: #eee; margin: 0; padding: 20px; }
  .container { max-width: 800px; margin: auto; background: #1e1e1e; padding: 20px; border-radius: 10px; }
  h2 { color: #00bcd4; text-align: center; }
  input[type=file], button { background: #333; color: white; border: none; padding: 10px; border-radius: 6px; margin-top: 10px; width: 100%; }
  button { background: #00bcd4; cursor: pointer; }
  button:hover { background: #0197a7; }
  progress { width: 100%; height: 18px; border-radius: 6px; margin-top: 10px; }
  ul { list-style: none; padding: 0; text-align: left; }
  li { margin: 8px 0; background: #2a2a2a; padding: 10px; border-radius: 6px; word-wrap: break-word; }
  a { color: #00bcd4; text-decoration: none; }
  a:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="container">
  <h2>💻 Full Access Explorer</h2>

  <form id="uploadForm" enctype="multipart/form-data">
    <input type="hidden" name="current_path" value="{{ abs_path }}">
    <input type="file" name="files" multiple>
    <progress id="progressBar" value="0" max="100"></progress>
    <button type="submit">Upload Files Here</button>
  </form>

  <h3>Current Directory: {{ abs_path }}</h3>

  {% if parent_link %}
    <p><a href="{{ parent_link }}">⬆️ Go up one level</a></p>
  {% endif %}

  <ul>
  {% for folder in folders %}
    <li>📁 <a href="{{ url_for('browse') }}?path={{ folder_paths[loop.index0] }}">{{ folder }}</a></li>
  {% endfor %}
  {% for file in files %}
    <li>📄 <a href="{{ url_for('download') }}?path={{ file_paths[loop.index0] }}">{{ file }}</a></li>
  {% endfor %}
  </ul>
</div>

<script>
document.getElementById('uploadForm').addEventListener('submit', function(e){
  e.preventDefault();
  var formData = new FormData();
  var files = e.target.files.files;
  var currentPath = e.target.current_path.value;
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }
  formData.append('path', currentPath);

  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/upload', true);

  xhr.upload.onprogress = function(e) {
    if (e.lengthComputable) {
      var percent = (e.loaded / e.total) * 100;
      document.getElementById('progressBar').value = percent;
    }
  };

  xhr.onload = function() {
    if (xhr.status == 200) {
      alert('Upload complete!');
      location.reload();
    } else {
      alert('Error uploading.');
    }
  };
  xhr.send(formData);
});
</script>
</body>
</html>
'''


def decode_path(raw_path):
    if not raw_path:
        return os.path.abspath(os.path.expanduser("C:/"))
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

    return render_template_string(
        HTML,
        folders=folders,
        files=files,
        folder_paths=folder_paths,
        file_paths=file_paths,
        parent_link=parent_link,
        abs_path=abs_path
    )


@app.route('/download')
def download():
    raw_path = request.args.get('path', '')
    abs_path = decode_path(raw_path)
    if os.path.isfile(abs_path):
        return send_file(abs_path, as_attachment=True)
    return f"<h3 style='color:red;'>Not a valid file: {abs_path}</h3>"


@app.route('/upload', methods=['POST'])
def upload():
    target_dir = request.form.get('path', '')
    target_dir = decode_path(target_dir)
    uploaded_files = request.files.getlist('files')

    for file in uploaded_files:
        if file.filename:
            file.save(os.path.join(target_dir, file.filename))

    return jsonify({"message": "Uploaded successfully"})


if __name__ == '__main__':
    print("⚠️ Full unrestricted file access enabled")
    print("Open from your phone: http://<your-PC-IP>:8000")
    app.run(host='0.0.0.0', port=8000)
