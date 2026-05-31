#!/usr/bin/env bash
set -e
cd /mnt/c/Users/GPU/Documents/ClaudeProjects/ZeroCode-Career-Coach
git config user.email "faithinusa@outlook.com"
git config user.name "fayfayMN"
git add docs/quick-start-options.md scripts/add_alias.sh
git commit -m "Add quick-start guide and launch alias script"
git push origin main
echo "PUSHED"
