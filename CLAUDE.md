# Workflow Orchestration

## Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - dont keep pushing
- Use plan mode for verification steps, not just building 
- Write detailed spec upfront to reduce ambiguity

## Self-improvement Loop
- After ANY correction from the user: update `docs/memory/pattern.md` with the pattern
- Write rules for yourself the prevent the same mistake
- Ruthlessly iterate on these pattern util mistake rate drops
- Review pattern at session start for relevant project

## Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One tack per sebagent for focused execution

## Verification Before Done
- Never mark a taks complete without proving it works
- Diff behavior between main and your changes when relevant 
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

## Task Management 
- **Plan First**: Write plan to `docs/memory/tasks/{task_name}/todo.md` with checkable items
- **Verify Plan**: Check in before starting implementation
- **Track Progress**: Mark items complete as you go
- **Explain Changes**: High-level summary at each step
- **Document Results**: Add review section to `docs/tasks/{task_name}/todo.md`
- **Capture Lessons**: Update `docs/memory/tasks/{task_name}/lessons.md` after corrections

## Core Principles
- **Simplicity First**: Make every change as simple as possible. Impact minimal code 
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards
- **Minimal Impact**: Changes should only touch what´s necessary. Avoid introducing bugs

--- 

To verify the project architecture and development patterns, read the `/docs/architecture.md` doc