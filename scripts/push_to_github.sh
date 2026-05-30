#!/usr/bin/env bash
set -e
cd /mnt/c/Users/GPU/Documents/ClaudeProjects/Career-Orchestrator-MultiAgent-Platform

git init
git config user.email "feifeiusa30@gmail.com"
git config user.name "fayfayMN"
git remote add origin https://github.com/fayfayMN/ZeroCode-Career-Coach.git

git add .
git commit -m "Initial release: ZeroCode Career Coach

3-agent + deterministic orchestrator job-search platform.
Runs on local Ollama (qwen3:14b). Voice mock interview via
faster-whisper + streamlit-mic-recorder. Single-file HTML
career dossier export. 13 passing tests (LLM mocked)."

git branch -M main
git push -u origin main
