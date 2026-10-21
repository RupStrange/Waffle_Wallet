#!/usr/bin/env bash
# Create a new git branch and switch to it, only if the working tree is clean.
# Usage: new_branch.sh <branch-name>

set -u

name="${1:-}"

if [ -z "$name" ]; then
  echo "Error: no branch name given. Usage: new_branch.sh <branch-name>" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

if ! git check-ref-format --branch "$name" >/dev/null 2>&1; then
  echo "Error: '$name' is not a valid git branch name." >&2
  exit 1
fi

if git show-ref --verify --quiet "refs/heads/$name"; then
  echo "Error: branch '$name' already exists." >&2
  exit 1
fi

changes="$(git status --porcelain)"
if [ -n "$changes" ]; then
  echo "Can't create '$name': you have uncommitted changes."
  echo "$changes"
  echo "Commit (or stash) these first, then try again."
  exit 2
fi

prev="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"

if git switch -c "$name" >/dev/null 2>&1 || git checkout -b "$name" >/dev/null 2>&1; then
  echo "Created and switched to branch '$name' (from '$prev')."
else
  echo "Error: git failed to create branch '$name'." >&2
  exit 1
fi
