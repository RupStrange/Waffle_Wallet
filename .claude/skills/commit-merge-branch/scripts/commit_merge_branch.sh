#!/usr/bin/env bash
# Commit, push, open a PR into main, merge it, then switch to main, pull, and delete the branch.
# Usage: commit_merge_branch.sh "<commit message>"
#        commit_merge_branch.sh --check    (run the safety checks only and show what changed; changes nothing)

set -u
BASE="main"
msg="${1:-}"

fail() { echo "Error: $*" >&2; exit 1; }

check_only=0
[ "$msg" = "--check" ] && check_only=1
[ -n "$msg" ] || fail "no commit message given. Usage: commit_merge_branch.sh \"<commit message>\""
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not inside a git repository."
command -v gh >/dev/null 2>&1 || fail "GitHub CLI (gh) is not installed. See https://cli.github.com"
gh auth status >/dev/null 2>&1 || fail "gh is not logged in. Run: gh auth login"

branch="$(git rev-parse --abbrev-ref HEAD)"
[ "$branch" != "HEAD" ] || fail "you're in detached HEAD state; switch to a branch first."
[ "$branch" != "$BASE" ] || fail "you're on '$BASE'. Run this from a feature branch."

if [ "$check_only" -eq 1 ]; then
  echo "Checks passed. On branch '$branch'."
  echo "--- uncommitted changes:"
  git status --short
  git fetch -q origin "$BASE" 2>/dev/null
  echo "--- commits on '$branch' not yet in '$BASE':"
  git log --oneline "origin/$BASE..HEAD" 2>/dev/null || git log --oneline "$BASE..HEAD"
  exit 0
fi

# 1. add + commit
echo "==> git add ."
git add . || fail "git add failed."
if git diff --cached --quiet; then
  git fetch -q origin "$BASE" 2>/dev/null
  ahead="$(git rev-list --count "origin/$BASE..HEAD" 2>/dev/null || git rev-list --count "$BASE..HEAD")"
  [ "${ahead:-0}" -gt 0 ] || fail "nothing to commit and '$branch' has no commits that '$BASE' doesn't. Nothing to merge."
  echo "==> nothing new to commit; using the $ahead existing commit(s) on '$branch'"
else
  echo "==> git commit -m \"$msg\""
  git commit -q -m "$msg" || fail "git commit failed."
fi

# 2. push
echo "==> git push -u origin $branch"
git push -u origin "$branch" || fail "push failed."

# 3. create PR (or reuse an open one)
url="$(gh pr view "$branch" --json url,state -q 'select(.state=="OPEN") | .url' 2>/dev/null)"
if [ -z "$url" ]; then
  echo "==> gh pr create --base $BASE --head $branch"
  url="$(gh pr create --base "$BASE" --head "$branch" --title "$msg" --body "Merged via /commit-merge-branch.")" \
    || fail "could not create the pull request."
else
  echo "==> reusing open PR"
fi
echo "PR: $url"

# 4. merge PR
echo "==> gh pr merge $branch --merge"
if ! gh pr merge "$branch" --merge; then
  echo "The PR is open but was NOT merged (conflicts, failing checks, or branch protection?)." >&2
  echo "Still on '$branch'. PR: $url" >&2
  exit 2
fi

# 5. switch to main, pull, delete branch
echo "==> git switch $BASE"
git switch "$BASE" 2>/dev/null || git checkout "$BASE" || fail "could not switch to '$BASE'."
echo "==> git pull origin $BASE"
git pull origin "$BASE" || fail "pull failed. The PR was merged; '$branch' was not deleted."
echo "==> git branch -d $branch"
git branch -d "$branch" || fail "could not delete '$branch' (the PR was merged)."

echo ""
echo "Done: '$branch' merged into '$BASE' ($url), branch deleted, and '$BASE' is up to date."
