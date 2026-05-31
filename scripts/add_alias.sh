#!/usr/bin/env bash
ALIAS_LINE='alias coach="cd /mnt/c/Users/GPU/Documents/ClaudeProjects/ZeroCode-Career-Coach && ~/cc-venv/bin/streamlit run app.py"'
if ! grep -q 'alias coach=' ~/.bashrc; then
    echo "$ALIAS_LINE" >> ~/.bashrc
    echo "✅ Alias added. Run: source ~/.bashrc  (or open a new WSL terminal)"
else
    echo "ℹ️  Alias already exists in ~/.bashrc"
fi
