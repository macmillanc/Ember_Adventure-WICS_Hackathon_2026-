#!/bin/bash

set -e

# Make sure we're inside a Git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Not inside a Git repository."
    exit 1
fi

echo "Repository:"
git rev-parse --show-toplevel

echo
echo "Current branch:"
git branch --show-current

echo
echo "Adding all files..."
git add -A

echo
echo "Changes to be committed:"
git status --short

# Don't create an empty commit
if git diff --cached --quiet; then
    echo
    echo "Nothing to commit."
else
    echo
    read -p "Commit message: " MESSAGE

    if [ -z "$MESSAGE" ]; then
        MESSAGE="Update files"
    fi

    git commit -m "$MESSAGE"
fi

echo
echo "Pushing to remote..."
git push

echo
echo "Done!"
