# Quick Start Options — ZeroCode Career Coach

Three ways to launch the app without typing WSL commands every time.

---

## Option 1 — Desktop shortcut (recommended)

A `Career Coach.bat` file is already on your Desktop. Double-click it:
- Opens **http://localhost:8501** in your browser automatically
- Starts the Streamlit app in WSL in the background
- Close the terminal window to stop the app

If the shortcut is ever missing, recreate it by saving this as `Career Coach.bat` on your Desktop:

```bat
@echo off
start "" http://localhost:8501
wsl -d Ubuntu bash -lc "cd /mnt/c/Users/GPU/Documents/ClaudeProjects/ZeroCode-Career-Coach && ~/cc-venv/bin/streamlit run app.py"
```

---

## Option 2 — `coach` alias in WSL

From any WSL (Ubuntu) terminal, just type:

```bash
coach
```

The alias is saved in `~/.bashrc` so it survives reboots. If it ever disappears, re-run:

```bash
bash /mnt/c/Users/GPU/Documents/ClaudeProjects/ZeroCode-Career-Coach/scripts/add_alias.sh
source ~/.bashrc
```

---

## Option 3 — Windows Terminal profile

Adds a one-click tab to Windows Terminal:

1. Open Windows Terminal → **Settings** (Ctrl+,)
2. Click **"Add a new profile"** → **"New empty profile"**
3. Fill in:
   - **Name:** `Career Coach`
   - **Command line:**
     ```
     wsl.exe -d Ubuntu bash -lc "cd /mnt/c/Users/GPU/Documents/ClaudeProjects/ZeroCode-Career-Coach && ~/cc-venv/bin/streamlit run app.py"
     ```
   - **Starting directory:** *(leave blank)*
   - **Icon:** pick any emoji or icon you like
4. **Save** — it now appears in the `+` dropdown in Windows Terminal

---

## Stopping the app

- **Desktop shortcut / Windows Terminal:** close the terminal window
- **WSL alias:** press `Ctrl + C` in the terminal

---

## Prerequisites (already set up — just for reference)

| What | Where |
|------|-------|
| Python venv | `~/cc-venv` in WSL Ubuntu |
| App code | `/mnt/c/Users/GPU/Documents/ClaudeProjects/ZeroCode-Career-Coach` |
| Ollama models | `qwen3:14b-q4_K_M` + `nomic-embed-text` (already pulled) |
| Ollama | Runs automatically in WSL background |

---

## Troubleshooting

**App won't start / model error:**
```bash
# Check Ollama is running
python scripts/smoke_check.py
# If not, start it
ollama serve
```

**Port 8501 already in use:**
```bash
pkill -f [s]treamlit
```
Then relaunch.
