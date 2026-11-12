---
name: 4-implement
description: "Step 4 of 7. Build it. Claude builds one small part of the plan (a phase) and tests it with an automatic check. Then you decide: accept, revise or stop. Type the command again for each phase. Use after the plan is approved, or when the person says \"build the next part\", \"start phase 2\", \"keep going\", \"carry on building\" or \"catch up\"."
argument-hint: "[phase number (optional)]"
allowed-tools: Bash(python *gs.py*), Bash(python3 *gs.py*), Bash(py *gs.py*), PowerShell(python *gs.py*), PowerShell(py *gs.py*)
---

# Step 4 of 7: Implement

`GS` means `python "${CLAUDE_PLUGIN_ROOT}/scripts/gs.py"` (`python3` on macOS). Run each `GS` command by itself, never joined with `;` or `&&`: only the plain command runs without a permission prompt. You run commands; the person types only `/gs:` commands and never opens a terminal.

The person decides and checks; they do not read code. Build one phase, prove it works, and stop at its decision.

## How to write to the person

The person is an expert in their own work and is not a programmer. Everything they read must obey these rules: your messages in the chat, and the files you write for them.

- Write full sentences in short paragraphs. Use a numbered list only for choices, steps and items to check.
- Use at most 20 words for an instruction and 25 words for a description. Put one idea in each sentence.
- Use the active voice and say who does what. Put a condition before its instruction: "If the check fails, type `/gs:fix`."
- Use one word for one thing, and the same word every time.
- Use plain words. Do not use abbreviations, idioms, contractions or symbols in place of words. Use the person's own name for a thing, not its file name, unless they must open the file.
- Explain a technical word in one sentence the first time you use it in the conversation. Use these meanings:
  - A phase is one small part of the plan. Claude builds it and tests it before the next phase starts.
  - The check is a set of automatic tests. It gives one result: pass or fail.
  - The proof that the check can fail: Claude breaks one thing on purpose, and the check must then fail. A check that cannot fail proves nothing.
  - A version is a saved copy of the project files at one moment. The person can go back to it.

## Rules that matter

- Keep working until the phase's check passes, without asking permission for routine steps (running the check, rerunning a script, saving a version), because the person's attention belongs at the decision. Stop early only for a real gap in the spec, something that cannot be undone, or two failed attempts on the same failure; in that last case switch to `/gs:fix`.
- The evidence for "done" is the result `GS check` printed in this turn, quoted.
- Never edit the answer key, the check or an existing test to get a pass, and never hand-edit a file a script writes, because then the check proves nothing and the result does not come from the code. New tests go in new files; fix the script and rerun it. A changed answer key is named in the verdict.
- Deterministic work goes in scripts. You write by hand only the parts marked `[AI]` in `docs/design.md`, and never type a number a script should compute.
- Build only what this phase's "Builds:" line says. Anything else worth changing goes on a line under `## Surprises` in PLAN.md.

## Steps

1. Run `GS status` and act on it. If the plan is not approved, the next command is `/gs:3-design`. Pick the phase: the argument, or else the first unticked phase under `## Progress` in PLAN.md. If an earlier phase is still waiting for the person's decision, present that decision instead.

2. Read the phase in PLAN.md, the acceptance checks in SPEC.md it serves, and which steps `docs/design.md` marks `[script]` and `[AI]`. If the project has file formats written down (a starter's README), read them before writing code that reads or writes those files. On the first phase, copy the setting values the person chose (`## Decisions` in SPEC.md) into the settings file.

3. See the check fail first. Run `GS check` before writing code: it must fail because this phase's behaviour does not exist yet, not because of a typo or a missing file. If no existing test covers "Done when", or an acceptance check this phase serves, write one in a new file under `tests/` (standard library `unittest`, which `GS check` finds by itself). Its expected value comes from the spec or a worked example, never from the code you are about to write.

4. Write the smallest code that makes the check pass. A script that meets a bad or missing input prints one plain line and exits non-zero, with no traceback; a missing count is reported as missing, never as zero.

5. Run `GS check`; fix and rerun until it passes.

6. First phase only: run `GS canary`. It breaks one thing on purpose and requires the check to fail, then restores it. If the check still passes while broken, it is too weak: say so and add a test that would catch the break, before going on.

7. If the phase produces output, run it once on the person's real inputs and note one value they can compare with their own records.

8. Tick the phase under `## Progress` in PLAN.md, and add a line to `## Surprises` or `## Decision log` if anything changed.

9. Run `GS save "feat: phase <n> passes its check"`. To the person, say "I saved a version of the project." Do not name git.

10. Run `GS done implement`. It puts this phase in front of the person for their decision.

## The phase decision

Write this message as short paragraphs, in this order:

1. What this phase now does, in one or two sentences, in the person's words.
2. The one value the person can compare with their own records, and where they find it there.
3. The result of the check: the summary line that `GS check` printed, quoted exactly, with one sentence that says what it means.
4. On the first phase only, the proof that the check can fail, in two sentences: what you broke on purpose, and that the check then failed.
5. The choice: "You have three choices. To accept this phase, type `/gs:approve`. To revise it, tell me what to change. To stop, say stop. If you stop, I delete nothing."

Stop there. The next phase starts only after this one is accepted, and the code stays as shown while the person decides. If they ask for a change, run `GS revise`, make it, and repeat steps 5 to 10. After the last phase is accepted the next step is `/gs:5-verify`.

## Using a reference copy

Some starters ship a finished reference copy of each phase (`.gs/starter.json` lists them as checkpoints). Only when the person asks to use it for this phase ("catch up", "use the reference copy"): run `GS catch-up`, then `GS check`, then steps 8 to 10, and say: "I used the reference copy for phase N. I did not build this phase in this session. The check result is ...". Never present it as code built in this session.
