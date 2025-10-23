# SwiftShare

> Lightweight, mobile-friendly file explorer and transfer server for your PC — browse, download, and upload files over your local network or mobile hotspot.

---

## What this is

SwiftShare is a tiny Flask-based web app that turns your PC into a temporary file server and remote file manager you can access from any device on the same network (for example your phone connected to your mobile hotspot). It is designed for simplicity and speed:

* Mobile-first UI with upload progress
* Browse any folder on your PC (optional unrestricted mode)
* Download any file to your phone or desktop browser
* Upload multiple files into the folder you are currently viewing
* Works offline over your local network or phone hotspot

This repo contains the working Python server script and documentation so anyone can run it locally in minutes.

---

## Key features

* Fast, single-file Flask app
* Multiple file uploads with client-side progress bar
* Recursive browsing of folders and subfolders on your PC
* Direct downloads from PC to mobile
* Optional behavior to fall back to a writable download folder if the target directory is not writable
* Minimal dependencies (`Flask` only)

---

## Why use this

* Quick file transfer between PC and phone without cloud services
* No third-party apps or accounts required
* Useful for testing, quick file sharing, and mobile access to local files

---

## Demo (quick)

1. Start your phone hotspot (or ensure phone and PC are on the same Wi‑Fi).
2. Run the server on your PC.
3. Open the shown URL on your phone browser: `http://<PC-IP>:8000`
4. Browse folders, download files, or upload multiple files with a progress bar.

---

## Files in this repo

* `full_access_explorer.py` — main Flask server (single-file, drop-in).
* `README.md` — this file.

---

## Quick start (Windows / macOS / Linux)

These commands assume you are comfortable running Python scripts from a terminal.

1. **Clone the repo**

```bash
git clone https://github.com/uttam-aggarwal/SwiftShare.git
cd SwiftShare
```

2. **Create a virtual environment (recommended)**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
# or simply
pip install flask
```

4. **Run the server**

```bash
python SwiftShare.py
```

5. **Open it on your phone**

Find your PC IP address (for Windows: `ipconfig`, for macOS/Linux: `ifconfig` / `ip a`), then on your phone visit:

```
http://<PC-IP>:8000
```

---

## Configuration & options

Open the Python file and edit the top of `SwiftSharer.py` to tweak behavior. Important variables and notes:

* `DEFAULT_UPLOAD_DIR` — set a safe default folder where uploads land when the app can't write to the target directory. Example: `C:\Users\<you>\Downloads`.
* `HOST` and `PORT` — defaults are `0.0.0.0` and `8000`. If you change the port, remember to open it in any local firewall if necessary.
* If you want *restricted* mode (only a chosen root directory), use the `safe_path` variant instead of the full-access version found in this repo. You can find an example in the commit history.

---

## Security & privacy (READ THIS)

This project gives remote devices direct file system access to the host machine. That makes it powerful, but also potentially dangerous if used carelessly. Follow these rules:

* **Only run this on networks you trust**. Avoid public Wi‑Fi. If you must use public networks, use a VPN and firewall rules that limit access.
* **Do not run as Administrator/System unless necessary.** Running the server as an elevated user gives the app permission to modify system files. Run as a normal user unless you understand the risks.
* **Turn it off when not in use.** Running an open file server unnecessarily is a security risk.
* **Do not expose this server to the public internet.** Do not forward the port in your router. This tool is intended for local networks and personal hotspots only.
* **Be careful with file uploads.** Uploaded content could overwrite local files if names clash. Use a dedicated `uploads` folder for temporary sharing when possible.
* **Firewall and OS prompts.** When you run the server first time, your OS firewall may warn about incoming connections. Allow it only on private/trusted networks.

If you want an extra layer of protection, add a simple authentication guard or run this behind an SSH tunnel.

**Danger checklist (copy to your project page)**

* Do not run on public or unknown networks.
* Avoid running this as System/Administrator.
* Do not forward the port publicly.
* Delete uploads you no longer need.

---

## Troubleshooting

**1. Internal Server Error on upload**
This usually means the script tried to write to a path where your user doesn't have permission. Fixes:

* Run the script as a normal user and pick a writable `DEFAULT_UPLOAD_DIR`.
* If you need to write into system locations, run the script from an elevated shell (not recommended).

**2. Folders show but clicking gives errors**
That happens when paths are URL-encoded or decoded incorrectly. Use the provided version of the script (it decodes paths properly). If you fork or modify the code, keep `urllib.parse.quote` and `unquote` usage consistent.

**3. Cannot reach from phone**

* Ensure both devices are on the same Wi‑Fi or hotspot.
* Check Windows Firewall or macOS firewall; allow Python to accept incoming connections on private networks.
* Confirm PC IP address and the port are correct.

---

## License

This project is released under the **MIT License**. See `LICENSE` for details. (Include a standard MIT license file when you push.)

---

## Contribution

Pull requests are welcome. If you add features (authentication, HTTPS, delete/rename, folder creation), please document them and keep changes minimal so others can still run the script straight away.

---

## Final notes

This tool is intentionally simple. It’s designed to solve a common, practical problem quickly: transfer files between phone and PC without cloud services. If you want, I can prepare a `demo.gif`, a minimal `index.html` web UI improvement, or a small blog post you can paste on your website to drive traffic — tell me which and I’ll create it.

---
