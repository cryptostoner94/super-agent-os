#!/bin/bash

# Supreme AI Agent OS - Auto-commit Script
# Automatically saves changes to git with timestamps

REPO_PATH="${1:-.}"
cd "$REPO_PATH"

# Check if git repo exists
if [ ! -d .git ]; then
    echo "❌ Not a git repository"
    exit 1
fi

# Get uncommitted changes
CHANGES=$(git status --porcelain)

if [ -z "$CHANGES" ]; then
    echo "✓ No changes to commit"
    exit 0
fi

# Create commit message with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_MSG="auto: update at $TIMESTAMP"

# Add all changes
git add -A

# Commit
git commit -m "$COMMIT_MSG"

echo "✓ Auto-committed changes at $TIMESTAMP"

# Optionally push to remote
if [ "$2" == "--push" ]; then
    git push origin $(git rev-parse --abbrev-ref HEAD)
    echo "✓ Pushed to remote"
fi
