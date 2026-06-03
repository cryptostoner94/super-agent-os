#!/bin/bash

# Supreme AI Agent OS - Auto-commit Script
# Automatically saves changes to git with timestamps

REPO_PATH="."
PUSH_TO_REMOTE=false

# Handle arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH_TO_REMOTE=true
            shift
            ;;
        *)
            REPO_PATH="$1"
            shift
            ;;
    esac
done

cd "$REPO_PATH" || exit 1

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
if [ "$PUSH_TO_REMOTE" = true ]; then
    git push origin $(git rev-parse --abbrev-ref HEAD)
    echo "✓ Pushed to remote"
fi
