#!/usr/bin/env bash
set -e
cd /mnt/c/Users/GPU/Documents/ClaudeProjects/Career-Orchestrator-MultiAgent-Platform
git config user.email "faithinusa@outlook.com"
git config user.name "fayfayMN"

# Add everything tracked + the helper scripts; _dev_*.html excluded by .gitignore
git add .gitignore scripts/git_push_update.sh scripts/git_status_check.sh

git commit -m "Housekeeping: add dev scripts, fix .gitignore for dev artifacts"
git push origin main
echo "PUSHED"
