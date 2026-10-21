---
name: commit-merge-branch
description: Update CLAUDE.md with the current changes, then commit everything on the current feature branch, push it, open a GitHub pull request into main, merge it, switch to main, pull, and delete the local branch. Manual-only — the user runs it themselves with /commit-merge-branch "<commit message>".
disable-model-invocation: true
user-invocable: true
---

# commit-merge-branch

## Who can start this

Only the user, by typing `/commit-merge-branch "<commit message>"` themselves. Do not run it on your own initiative, from another skill, from a hook, from a scheduled or background task, or because a conversation mentions merging, pushing, or PRs. If you think it would help, you may suggest the user run `/commit-merge-branch`, but never run it for them. This skill pushes code and merges into main, so a person has to decide each time.

## Steps

1. **Get the commit message.** Use the argument passed to `/commit-merge-branch` ($ARGUMENTS). If there is none, ask the user for one — don't write your own.

2. **Run the safety checks first** (this changes nothing):

   ```bash
   bash <path-to-this-skill>/scripts/commit_merge_branch.sh --check
   ```

   It confirms you're in a git repo, `gh` is installed and logged in, and you're not on `main`, then lists the uncommitted changes and the branch's commits. If it fails, relay the message and stop — don't touch CLAUDE.md.

3. **Update CLAUDE.md with the current changes.** Read the actual diff (`git diff`, `git diff --cached`, `git status`, and `git log origin/main..HEAD` for already-committed work) so CLAUDE.md describes what really changed, not what you assume.
   - Edit `CLAUDE.md` in the repo root. If it doesn't exist, create it with a short project overview (one or two lines) plus the changelog section below.
   - Update any existing sections the changes make out of date: project structure, new files or modules, setup or run commands, dependencies, environment variables, conventions. Leave sections the changes don't touch as they are.
   - Add an entry at the top of a `## Changelog` section (create the section at the end of the file if missing), in this format:

     ```markdown
     ### YYYY-MM-DD — <branch-name>
     <commit message>
     - <one short bullet per meaningful change>
     ```

   - Keep it brief and factual. CLAUDE.md is read at the start of every Claude Code session, so it should stay short; don't paste code or diffs into it.

4. **Run the full workflow:**

   ```bash
   bash <path-to-this-skill>/scripts/commit_merge_branch.sh "<commit message>"
   ```

   Because it starts with `git add .`, the CLAUDE.md update goes into the same commit. Then, stopping at the first failure:
   1. `git add .` and `git commit -m "<message>"`
   2. `git push -u origin <branch>`
   3. `gh pr create --base main --head <branch> --title "<message>"` (reuses an open PR for this branch)
   4. `gh pr merge <branch> --merge` (a normal merge commit, so the safe delete works)
   5. `git switch main`
   6. `git pull origin main`
   7. `git branch -d <branch>`

5. **Report the result.**
   - On success, print the PR URL, one line saying what you changed in CLAUDE.md, and one line saying the branch was merged and deleted and you're on an up-to-date main.
   - If the merge step fails (conflicts, failing required checks, branch protection, required reviews), the script stops on the feature branch and prints the PR URL. Tell the user the PR is open but not merged, relay the reason, and stop. Don't retry with admin overrides or force flags.
   - On any other failure, relay the script's message and stop.

## What not to do

- Don't run this unless the user typed `/commit-merge-branch` themselves.
- Don't use `git push --force`, `gh pr merge --admin`, or `git branch -D`.
- Don't edit, stash, or discard files other than CLAUDE.md to get past an error.
- Don't run this on `main`.
