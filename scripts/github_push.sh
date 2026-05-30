#!/usr/bin/env bash
set -e
export PATH="$HOME/bin:$PATH"

REPO_DIR="/mnt/c/Users/GPU/Documents/ClaudeProjects/Career-Orchestrator-MultiAgent-Platform"
REPO_NAME="ZeroCode-Career-Coach"

cd "$REPO_DIR"

# --- git init + first commit ---
git init
git config user.email "feifeiusa30@gmail.com"
git config user.name "fayfayMN"

# Stage everything except gitignored files
git add .

git commit -m "Initial release: ZeroCode Career Coach

3-agent + deterministic orchestrator job-search platform.
Runs on local Ollama (qwen3:14b). Voice mock interview via
faster-whisper. Single-file HTML career dossier export."

# --- create GitHub repo and push ---
gh repo create "$REPO_NAME" \
  --public \
  --description "A recruiter-designed, fully local AI job-search assistant — fit scoring, tailored resume & cover letter, voice mock interview, one-click dossier. Zero coding required to use it. Runs on Ollama." \
  --source . \
  --remote origin \
  --push

echo ""
echo "✅ Pushed to: https://github.com/$(gh api user --jq .login)/${REPO_NAME}"
