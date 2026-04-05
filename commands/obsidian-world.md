---
description: Load your identity, values, priorities, and current state in one shot — Claude knows who you are instantly
---

Use the obsidian-second-brain skill. Execute `/obsidian-world`:

1. Read `_CLAUDE.md` first if it exists in the vault root
2. Load the identity layer — read these files if they exist (search for them if paths differ):
   - `SOUL.md` or `About Me.md` — who the user is, communication style, thinking preferences
   - `CORE_VALUES.md` or `Values.md` — decision-making principles and non-negotiables
   - `Home.md` or `Dashboard.md` — current top-level priorities and active projects
3. Load the current state:
   - Read today's daily note (if it exists) for what's already in progress
   - Read the last 3 daily notes for recent momentum and open threads
   - Scan active kanban boards for in-progress and overdue items
   - Check for any session digest from the previous conversation (look for "End of Day" or "Session Digest" sections in recent daily notes)
4. Load the context:
   - Read active project notes (status: active) for current goals and blockers
   - Identify key people the user has interacted with recently (last 7 days of daily notes)
5. Synthesize and present a brief status:
   - **Who I am to you**: confirm the persona and communication style
   - **Your current priorities**: top 3-5 active threads
   - **Open threads from last session**: anything unfinished
   - **Overdue / needs attention**: tasks or projects that are stale
   - **Today so far**: what's already logged today

Keep the output concise — this is a boot-up sequence, not a report. The user should be able to glance at it and say "yes, Claude is up to speed" and start working immediately.

If identity files (SOUL.md, CORE_VALUES.md) don't exist, offer to create them by interviewing the user with 5-7 quick questions about their role, values, and communication preferences.
