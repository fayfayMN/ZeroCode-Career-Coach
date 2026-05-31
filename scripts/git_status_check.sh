#!/usr/bin/env bash
cd /mnt/c/Users/GPU/Documents/ClaudeProjects/ZeroCode-Career-Coach
echo "=== git status ==="
git status
echo ""
echo "=== untracked files ==="
git ls-files --others --exclude-standard
echo ""
echo "=== latest 5 commits ==="
git log --oneline -5
