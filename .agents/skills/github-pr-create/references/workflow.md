---
main_config: '{project-root}/_bmad/bmm/config.yaml'
---

# GitHub PR Create Workflow

## Overview

This workflow prepares and opens a GitHub pull request from the current branch by using the repository PR template as the source of truth. Act as a pragmatic release engineer. Use when the user wants a PR created, wants the PR description drafted from the current diff, or wants the PR opened against the repository default branch. Produces a GitHub pull request with the required template sections filled.

## On Activation

1. Load available config from `{project-root}/_bmad/config.yaml` and `{project-root}/_bmad/config.user.yaml` if present. Use sensible defaults for anything not configured.
2. Treat `.github/pull_request_template.md` as the required PR body structure.
3. Use `gh` for repository metadata and PR creation.

## Workflow

1. Validate prerequisites.
   - Confirm the current directory is a Git repository.
   - Confirm the current branch is not the repository default branch.
   - Confirm `.github/pull_request_template.md` exists.
   - Confirm `gh auth status` succeeds before attempting PR creation.

2. Gather PR context from the repository.
   - Read the current branch name.
   - Resolve the repository default branch with `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`.
   - Collect the diff summary against the default branch using Git.
   - Inspect recent commits on the current branch if they help produce a tighter summary.

3. Draft the PR content.
   - Read `.github/pull_request_template.md`.
   - Fill every required section in the template with concrete content derived from the branch diff.
   - Keep the description concise and reviewer-oriented.
   - `Summary` should explain the behavioral change in a few bullets.
   - `Scope` must fill both `Included` and `Not included`.
   - `Risks` must contain a real note when risk exists; if risk is low, state that directly instead of leaving the section blank.
   - `Links` must include whatever relevant Jira/spec links are discoverable from branch name, commits, changed docs, or user-provided context. If a link cannot be determined, write `TBD` rather than leaving the field empty.

4. Validate the draft before opening the PR.
   - Ensure no template headings are removed.
   - Ensure required bullets are not blank placeholders.
   - Ensure the body does not leave empty `Included`, `Not included`, `Jira`, or `Spec` lines.
   - If essential context is missing and cannot be inferred safely, stop and ask the user for the missing item instead of opening a weak PR.

5. Create the PR.
   - Build the PR title from the ticket/branch context and actual change scope.
   - Open the PR with `gh pr create`.
   - Always pass the resolved default branch explicitly via `--base`.
   - Pass the generated PR body via `--body-file`.
   - Prefer the current branch as the head branch.

6. Report the result.
   - Return the PR URL.
   - Summarize the final title, base branch, and filled links.
   - If PR creation was blocked, state exactly what information was missing or what command failed.

## Guardrails

- Do not open a PR with unfilled template placeholders.
- Do not guess Jira or spec links when the repo context does not support them; use `TBD` or ask the user if the link is essential.
- Do not target a non-default base branch unless the user explicitly asks for it.
- Keep the PR body aligned with `.github/pull_request_template.md`; do not invent extra sections unless the user asks for them.

## Tools Used

- `git`
- `gh`

## Output

- GitHub pull request URL
- Final PR title
- Final PR body aligned with `.github/pull_request_template.md`
