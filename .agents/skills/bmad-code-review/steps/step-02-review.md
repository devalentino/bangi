---
failed_layers: '' # set at runtime: comma-separated list of layers that failed or returned empty
---

# Step 2: Review

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- The Blind Hunter subagent receives NO project context — diff only.
- The Edge Case Hunter subagent receives diff and project read access.
- The Acceptance Auditor subagent receives diff plus the full accepted context bundle: PR description/metadata, Jira issue details, Jira comments, spec/story docs, and any additional context docs.

## INSTRUCTIONS

1. If `{review_mode}` = `"no-spec"`, note to the user: "Acceptance Auditor skipped — no PR/Jira/spec context was provided."

2. Launch parallel subagents without conversation context. If subagents are not available, generate prompt files in `{implementation_artifacts}` — one per reviewer role below — and HALT. Ask the user to run each in a separate session (ideally a different LLM) and paste back the findings. When findings are pasted, resume from this point and proceed to step 3.

   - **Blind Hunter** — receives `{diff_output}` only. No spec, no context docs, no project access. Invoke via the `bmad-review-adversarial-general` skill.

   - **Edge Case Hunter** — receives `{diff_output}` and read access to the project. Invoke via the `bmad-review-edge-case-hunter` skill.

   - **Acceptance Auditor** (only if `{review_mode}` = `"full"`) — receives `{diff_output}` and the full loaded context bundle, including PR title/body, Jira issue details, Jira comments, the content of the file at `{spec_file}` if present, and any loaded context docs. Its prompt:
     > You are an Acceptance Auditor. Review this diff against the full context bundle: PR description, Jira issue details, Jira comments, spec/story docs, and any additional context docs. Check for: violations of acceptance criteria, deviations from the current agreed scope, missing implementation of specified behavior, and contradictions between code and the most up-to-date context. Treat explicit Jira comment decisions, scope clarifications, and terminology changes as newer authority than older spec wording unless the user says otherwise. Output findings as a Markdown list. Each finding: one-line title, which AC/constraint/decision it violates, and evidence from the diff and context.

3. **Subagent failure handling**: If any subagent fails, times out, or returns empty results, append the layer name to `{failed_layers}` (comma-separated) and proceed with findings from the remaining layers.

4. Collect all findings from the completed layers.


## NEXT

Read fully and follow `./step-03-triage.md`
