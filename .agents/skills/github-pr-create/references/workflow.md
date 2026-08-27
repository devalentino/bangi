---
main_config: '{project-root}/_bmad/bmm/config.yaml'
---

# GitHub PR Create Workflow

## Overview

This workflow prepares and opens a GitHub pull request from the current branch by using the repository PR template as the source of truth. Act as a pragmatic release engineer. Use when the user wants a PR created, wants the PR description drafted from the current diff, or wants the PR opened against the repository default branch. Produces a GitHub pull request with the required template sections filled and the release version bumped when the branch didn't already bump it.

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

3. Ensure the release version has moved.
   - This repo tracks one release version across three places that must always agree: `BANGI_RELEASE_TAG` in `{project-root}/infra/installer/install.sh`, and the `bangi-web` and `bangi-api` image tags in `{project-root}/infra/installer/templates/compose.prod.yml`.
   - Diff all three against the default branch. If none of them changed on this branch, the version wasn't bumped — bump it yourself before opening the PR: increment the trailing pre-release number (e.g. `0.0.1a75` -> `0.0.1a76`) and apply the same new value to all three locations so they stay in lockstep.
   - If the version already moved on this branch (whatever the new value), leave it alone — don't second-guess an intentional bump.
   - Stage and include any version-bump edit you make as part of the PR's changes.

4. Draft the PR content.
   - Read `.github/pull_request_template.md`.
   - Fill every required section in the template with concrete content derived from the branch diff.
   - Keep the description concise and reviewer-oriented.
   - `Summary` should explain the behavioral change in a few bullets.
   - `Scope` must fill both `Included` and `Not included`.
   - `Risks` must contain a real note when risk exists; if risk is low, state that directly instead of leaving the section blank.
   - `Links` must include whatever relevant Jira/spec links are discoverable from branch name, commits, changed docs, or user-provided context. If a link cannot be determined, write `TBD` rather than leaving the field empty.

5. Validate the draft before opening the PR.
   - Ensure no template headings are removed.
   - Ensure required bullets are not blank placeholders.
   - Ensure the body does not leave empty `Included`, `Not included`, `Jira`, or `Spec` lines.
   - Ensure the PR title matches either `<jira_ticket>: <prefix>: <pr_title>` or `<prefix>: <pr_title>`.
   - When `jira_ticket` is present, ensure it is a concrete ticket ID such as `KAN-11`, not `TBD`.
   - Ensure `prefix` is exactly one of: `feat`, `fix`, `migration`, `refactor`, `chore`, `test`, `docs`, `perf`.
   - Ensure `pr_title` names the affected area when the task wording is generic, so it is clear without Jira or branch context.
   - If essential context is missing and cannot be inferred safely, stop and ask the user for the missing item instead of opening a weak PR.

6. Create the PR.
   - Build the PR title as `<jira_ticket>: <prefix>: <pr_title>` when a Jira ticket can be resolved confidently; otherwise build it as `<prefix>: <pr_title>`.
   - Resolve `jira_ticket` from the strongest available repo context, preferring branch name, then recent commits, then user-provided context.
   - If no Jira ticket can be resolved confidently, omit it from the title instead of using a placeholder.
   - Choose `prefix` from the actual scope of change:
     - `feat`: A new feature for the user or system.
     - `fix`: A bug fix for the existing functionality.
     - `migration`: Database schema changes or major version upgrades.
     - `refactor`: Code changes that neither fix a bug nor add a feature.
     - `chore`: Routine tasks, dependency updates, or configuration changes.
     - `test`: Adding missing tests or correcting existing ones.
     - `docs`: Documentation-only changes.
     - `perf`: A code change that improves performance.
   - Write `pr_title` as a concise reviewer-oriented summary of the actual change, without repeating the ticket or prefix.
   - Derive area wording from changed paths when useful, e.g. `infra/installer/**` -> `provisioner installer fetches pinned deployment assets`.
   - If the workflow cannot determine a valid `prefix` confidently, stop and ask the user instead of guessing.
   - Open the PR with `gh pr create`.
   - Always pass the resolved default branch explicitly via `--base`.
   - Pass the generated PR body via `--body-file`.
   - Prefer the current branch as the head branch.

7. Report the result.
   - Return the PR URL.
   - Summarize the final title, base branch, and filled links.
   - State whether the release version was already bumped on the branch or bumped by this workflow, and the resulting version value.
   - If PR creation was blocked, state exactly what information was missing or what command failed.

## Guardrails

- Do not open a PR with unfilled template placeholders.
- Do not guess Jira or spec links when the repo context does not support them; use `TBD` or ask the user if the link is essential.
- Do not open a PR whose title does not match either `<jira_ticket>: <prefix>: <pr_title>` or `<prefix>: <pr_title>`.
- Do not use placeholder ticket values in the title when Jira context is missing; omit the ticket segment instead.
- Do not invent or normalize unsupported prefixes; use only `feat`, `fix`, `migration`, `refactor`, `chore`, `test`, `docs`, or `perf`.
- Do not target a non-default base branch unless the user explicitly asks for it.
- Keep the PR body aligned with `.github/pull_request_template.md`; do not invent extra sections unless the user asks for them.
- Do not open a PR where the release version wasn't bumped anywhere on the branch; bump it yourself rather than opening it un-bumped or blocking on the user.
- Do not bump the version again if the branch already moved it — trust an existing intentional bump.

## Tools Used

- `git`
- `gh`

## Output

- GitHub pull request URL
- Final PR title
- Final PR body aligned with `.github/pull_request_template.md`
- Release version status (already bumped vs. bumped by this workflow) and its final value
