---
name: 3-design
description: "Step 3 of 7. Agree how it will work. Claude shows you the parts of the system and how they connect. Claude also writes the plan, which is the order of the work in small parts. You approve both. Use after the spec is approved, or when the person says \"how will we build it\", \"plan the build\", \"draw me the picture\" or \"what are the steps\"."
allowed-tools: Bash(python *gs.py*), Bash(python3 *gs.py*), Bash(py *gs.py*), PowerShell(python *gs.py*), PowerShell(py *gs.py*)
---

# Step 3 of 7: Design

`GS` means `python "${CLAUDE_PLUGIN_ROOT}/scripts/gs.py"` (`python3` on macOS; `py` on Windows when `python` is not found). Run each `GS` command by itself, never joined with `;` or `&&`: only the plain command runs without a permission prompt. You run commands; the person types only `/gs:` commands and never opens a terminal.

The person is commissioning the system: they read the picture and the plan, not code.

## How to write to the person

The person is an expert in their own work and is not a programmer. Everything they read must obey these rules: your messages in the chat, and the files you write for them.

- Write full sentences in short paragraphs. Use a numbered list only for choices, steps and items to check.
- Use at most 20 words for an instruction and 25 words for a description. Put one idea in each sentence.
- Use the active voice and say who does what. Put a condition before its instruction: "If the check fails, type `/gs:fix`."
- Use one word for one thing, and the same word every time.
- Use plain words. Do not use abbreviations, idioms, contractions or symbols in place of words. Use the person's own name for a thing, not its file name, unless they must open the file.
- Explain a technical word in one sentence the first time you use it in the conversation. Use these meanings:
  - The plan is the order of the work, in small parts. Its file is `PLAN.md`.
  - A phase is one small part of the plan. Claude builds it and tests it before the next phase starts.
  - A script is a small program. It does the same thing the same way each time.
  - A template is the fixed layout of the output.
  - Test data are saved examples that stay in the project. Real data are the person's own files and accounts.

## Rules that matter

- Write no code in this step, because the plan decision is the person's chance to change course cheaply.
- Mark every step `[script]` or `[AI]`. Scripts do counting, dates, parsing, sorting and formatting, because those must give the same answer every time and can be checked; AI does only what needs judgment or language.
- Keep the template, the data, the rules (settings) and the logic in separate places, so the person can change a setting or the layout without touching code and each part can be checked alone.
- Design for what is already on the person's computer: Python's standard library and file types they can open by double-click (text, CSV, HTML). Anything that must be installed first is a question for the person, with the plain alternative recommended, because they cannot install or repair a package themselves.
- If the starter defines the phases, use them as they are, because its checks and reference copies are built around them.

## Steps

1. Run `GS status` and act on it. If the spec is not approved, the next command is `/gs:2-define`. If PLAN.md already has ticked items under `## Progress`, ask whether to revise the plan or continue with `/gs:4-implement`, because overwriting a plan in progress loses work.

2. Read `SPEC.md`, `docs/decisions.md`, `docs/explore-notes.md`, and what the starter ships if there is one (its README, settings file, template, check and `.gs/starter.json`). Reuse what exists.

3. Write `docs/design.md` with exactly these headings, in plain words, defining a technical word in one clause the first time:
   - `## The picture`: inputs, then steps, then outputs, as a short numbered list. Each step names what it reads and what it writes, carries its `[script]` or `[AI]` mark, and gives a one-clause reason. Example: "3. Add up each customer's orders for the month `[script]`: arithmetic must be exact."
   - `## Where things live`: the template, the data, the rules or settings, and the logic, each with its file or folder, and one sentence on why they are kept apart.
   - `## Test data and real data`: how a run on test data differs from a real run, which folder each reads and where each writes, so a test never overwrites the real output and real data never lands in the tests.
   - `## When something goes wrong`: for each script, the one plain line it prints on a bad input before stopping with a non-zero exit code (which means "failed"), and where its log goes. A missing input is reported as missing, never as zero, because "nothing to report" and "the file was empty" look the same in the output.
   - `## Risks`: at most five, each with what would show it is happening.

4. Write `PLAN.md`:
   - `## Summary`: at most 120 words: what gets built, in how many phases, and how the person will know each phase works.
   - `## Phases`: thin slices, smallest first, each one running from input to output so it can be seen working:
     ```
     ### Phase N: <name>
     Builds: <what this phase adds, in the person's words>
     Done when: <a result that could turn out false, with the exact value or behaviour expected>
     Check: <what runs it, usually GS check, plus one thing the person can check by hand against their own records>
     ```
     "The script runs" is not a "Done when". If the starter defines phases (`.gs/starter.json`), write those, in that order, with their names, filling the three lines from the starter's own documents.
   - `## Progress`: one checkbox line per phase, all `[ ]`.
   - `## Decision log`: each design choice so far, one line with its reason.
   - `## Surprises`: empty for now.

5. If a choice needs the person (for example where the finished output should be saved), ask one question, recommended answer first, options written in the chat, and record the answer in the decision log.

6. Run `GS lint plan` and fix each line it prints until it prints none. Then run `GS done design`.

## The decision

Write this message and nothing more. The person can open the files, so do not paste them.

1. One or two sentences that say what the design and the plan are, and that both are ready.
2. The picture as a numbered list of at most seven steps. Each step is one full sentence that says what goes in, what happens and what comes out. End each with "(a script does this)" or "(Claude does this)", not with the `[script]` and `[AI]` marks.
3. The phases as a numbered list. Each is one or two sentences: what the phase adds, and how we will know that it works.
4. One sentence that names the two files and says that both passed the format check, which tests that no part is missing.
5. The choice: "You have three choices. To accept the design and the plan, type `/gs:approve`. To revise it, tell me what to change. To stop, say stop. If you stop, I delete nothing."

A request that changes what the system must do goes back to `/gs:2-define`, because the approved spec needs a new approval when it changes.
