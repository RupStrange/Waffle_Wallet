---
name: new-branch
description: Create a new git branch with a name the user gives and switch to it, but only if the working tree is clean. Manual-only — run it with /new-branch <branch-name>. Refuses and explains if there are uncommitted changes.
disable-model-invocation: true
---

# new-branch

This skill is explicit-only: it runs when the user types `/new-branch <branch-name>`. Never start it on your own because a conversation mentions branches.

Creates a new git branch from the current HEAD and switches to it. The one hard rule: **never create the branch if the working tree has uncommitted changes.** The user wants a clean starting point for every branch, so carrying half-done work across is exactly what this skill exists to prevent.

## Steps

1. **Get the branch name.** Use the argument passed to `/new-branch` (available as $ARGUMENTS). If they didn't give one, ask for it — don't invent a name.

2. **Run the helper script** from the repo the user is working in:

   ```bash
   bash <path-to-this-skill>/scripts/new_branch.sh "<branch-name>"
   ```

   The script does all the checks in order and stops at the first failure:
   - confirms you're inside a git repository
   - validates the name with `git check-ref-format --branch`
   - refuses if a local branch with that name already exists
   - refuses if `git status --porcelain` shows anything (staged, unstaged, or untracked files)
   - otherwise runs `git switch -c <name>` (falls back to `git checkout -b` on older git)

3. **Report the result.**
   - On success, print one short line: `Created and switched to branch '<name>' (from '<previous-branch>').`
   - On a dirty working tree, show the list of uncommitted files the script printed and tell the user to commit (or stash) them first, then run the command again. Stop there.
   - On any other failure (not a repo, bad name, branch exists), relay the script's message and stop.

## What not to do

- Don't commit, stash, or discard the user's changes to "make it work". Rejecting is the correct outcome when the tree is dirty; the user decides what to do with their changes.
- Don't push the branch or set an upstream unless the user asks.
- Don't silently rename or "fix" an invalid branch name — tell the user why it's invalid and let them pick a new one.

## Examples

**Clean tree**
User: /new-branch feature/login-page
Output: `Created and switched to branch 'feature/login-page' (from 'main').`

**Dirty tree**
User: /new-branch fix-navbar
Output:
```
Can't create 'fix-navbar': you have uncommitted changes.
 M src/App.jsx
?? notes.txt
Commit (or stash) these first, then try again.
```
