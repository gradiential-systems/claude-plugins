# Handoff

Done means: `HANDOFF.md` exists with the seven headings below, every lasting fact also lives in SPEC.md, PLAN.md or the run-book, and a version is saved.

## Rules that matter

- Point to files instead of copying them, because a copy goes stale while the original keeps changing. Facts that should outlive the handoff go into SPEC.md, PLAN.md or `docs/run-book.md` first; HANDOFF.md points there.
- Verified means evidence: each item names the check, log or file that shows it. Anything without evidence goes under Not checked, because the next person will trust whatever is listed as verified.
- One handoff at a time: overwrite `HANDOFF.md`, keep no older copies, because two handoffs will disagree.
- Write for someone who was not in the room: plain words, no shorthand from this session.

## Steps

1. Run `GS status`; its lines go under "Where it stands".
2. Read SPEC.md, PLAN.md, `docs/decisions.md`, `docs/verify-report.md`, `docs/run-book.md`, `docs/changes/` and the newest check log in `.gs/logs/`, whichever exist.
3. Move lasting facts first. A decision that exists only in the conversation goes into the file it belongs to. If adding it to an approved SPEC.md or PLAN.md would reopen that gate, ask the person one question first, recommending `docs/decisions.md` as the place that does not reopen it.
4. If the argument names who takes over or what the next session is for, shape "Next step" and "Not checked" for that.
5. Write `HANDOFF.md` with exactly these headings:
   - `## What this is`: two sentences: what the project makes and for whom.
   - `## Where it stands`: the lines from `GS status`.
   - `## Decided`: the main decisions, one line each, with the file where each is recorded.
   - `## Verified`: what is proven, one line each, with its evidence (the check result and date, the log path, the output that shows it).
   - `## Not checked`: what nobody has verified yet, including anything the person has not tried by hand.
   - `## Next step`: one command, from the `NEXT:` line of `GS status`.
   - `## Where things are`: the main files and folders, one line each; and "In a fresh session, type `/gs:1-explore` first: it picks the project up from here."
6. Save a version, so the handoff matches a version that can be returned to: run `GS save "docs: handoff <date>"` (the project's ignore list keeps the person's data and outputs out of saved versions). Before the folder goes to a colleague, say that saved versions leave out the person's data and outputs, and that these should be added only if the colleague is allowed to see them.
7. End on the one next command from `## Next step`.
