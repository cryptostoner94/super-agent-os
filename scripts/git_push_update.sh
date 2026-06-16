#!/usr/bin/env bash
set -e
MSG="${1:-update supreme ai agent os}"
git status
git add .
git commit -m "$MSG" || echo "No changes to commit."
git push
