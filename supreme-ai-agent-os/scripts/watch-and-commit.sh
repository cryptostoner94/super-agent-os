#!/bin/bash

# Supreme AI Agent OS - Watch and Auto-Commit
# Saves to git whenever files change

REPO_PATH="${1:-.}"
cd "$REPO_PATH"

echo "👀 Watching for changes (Ctrl+C to stop)..."
echo "📁 Monitoring: $REPO_PATH"

inotifywait -m -r -e modify,create,delete \
    --exclude '\.git|__pycache__|\.pyc|node_modules|\.venv' \
    . | while read path action file; do
    
    # Skip if file is in .gitignore
    git check-ignore -q "$path$file" && continue
    
    # Auto-commit
    echo "📝 Change detected: $path$file"
    bash scripts/auto-commit.sh --push
    sleep 1
done
