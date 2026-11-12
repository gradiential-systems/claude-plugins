# Lessons

Done means: at most three lessons are in `docs/lessons.md`, each in its strongest home, and any new check has been seen to fail on the old mistake and pass now.

## Rules that matter

- One question, then work: "What went wrong or was slow?", with Claude's own suggestion attached as the recommended answer, because the person remembers what hurt and Claude can read what happened.
- At most three lessons, because a long list gets skimmed and none of it changes anything.
- Give each lesson the strongest home it can have, in this order: a new automated check (best, because a check can fail and a sentence cannot); a rule in the project's CLAUDE.md, which Claude reads every session; a note in `docs/lessons.md` only.
- A mistake that happened twice becomes a check that fails next time, because a written rule has already failed once to prevent it.

## Steps

1. Run `GS status` and act on it. Read the end of `.gs/log.jsonl`, `docs/lessons.md` (to spot repeats), the newest files in `docs/changes/` and the recent conversation.

2. Ask the one question, with your suggestion written out, for example: "What went wrong or was slow? My suggestion: the date check failed twice because the time zone was wrong."

3. Pick at most three lessons and a home for each:
   - A check: add a test in a new file under `tests/` that fails on the old mistake. Show it failing by putting the mistake back for a moment, then passing once it is removed, then run `GS check`. Do not touch the check, the answer key or an existing test, because changing them weakens the bar instead of raising it. If the spec and plan are not approved yet, choose a rule or a note for now.
   - A rule: one line in the project's CLAUDE.md, with its reason in a clause, for example "Read the time zone from the settings file, because the computer's clock zone can differ from the person's."
   - A note: when neither a check nor a rule fits, such as a lesson about how long a step takes.

4. Write each lesson as one line in `docs/lessons.md` (`/gs:fix` adds one line per defect to the same file): `<date>: <the lesson>. What happened: <one clause>. Home: check <test file> | rule in CLAUDE.md | note only.`

5. Report in two sentences what changed and where, then end on the `NEXT:` line of `GS status`.
