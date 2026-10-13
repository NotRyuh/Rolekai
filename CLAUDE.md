# Rolekai

Read `AGENTS.md` for shared instructions. Begin with `.planning/STATE.md`, then inspect the current native GSD handoff and plan only as needed. Product and architecture documents remain authoritative.

Use `/gsd-progress`, `/gsd-pause-work`, `/gsd-resume-work` and `/gsd-plan-phase`. Technical recovery: `node scripts/agent-continuity.cjs resume --runtime claude --session <stable-session-id>`. Start Claude from the repository root so its GSD status line resolves locally. No product execution or automatic Git commits are authorized by the environment integration task.
