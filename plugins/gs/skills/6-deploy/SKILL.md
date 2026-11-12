---
name: 6-deploy
description: "Step 6 of 7. Make it a routine. Claude makes one command that runs the accepted result. You type that command yourself. Claude also writes the run-book: one page on how to run the result and what to do if a run fails. Use after the result is approved, or when the person says \"make it runnable\", \"how do I run this every day\", \"set it up for real\" or \"can it run on its own\"."
allowed-tools: Bash(python *gs.py*), Bash(python3 *gs.py*), Bash(py *gs.py*), PowerShell(python *gs.py*), PowerShell(py *gs.py*)
---

# Step 6 of 7: Deploy

`GS` means `python "${CLAUDE_PLUGIN_ROOT}/scripts/gs.py"` (`python3` on macOS). Run each `GS` command by itself, never joined with `;` or `&&`: only the plain command runs without a permission prompt. You run commands; the person types only `/gs:` commands and never opens a terminal.

Done means: the person can run the accepted result by typing one command in the app, can tell a test run from a real run, has `docs/run-book.md` to fall back on, and has watched one real run succeed.

## How to write to the person

The person is an expert in their own work and is not a programmer. Everything they read must obey these rules: your messages in the chat, and the files you write for them.

- Write full sentences in short paragraphs. Use a numbered list only for choices, steps and items to check.
- Use at most 20 words for an instruction and 25 words for a description. Put one idea in each sentence.
- Use the active voice and say who does what. Put a condition before its instruction: "If the check fails, type `/gs:fix`."
- Use one word for one thing, and the same word every time.
- Use plain words. Do not use abbreviations, idioms, contractions or symbols in place of words. Use the person's own name for a thing, not its file name, unless they must open the file.
- Explain a technical word in one sentence the first time you use it in the conversation. Use these meanings:
  - A test run uses the saved examples in the project. A real run uses the person's own data on that day.
  - The run-book is one page. It says how to run the result and what to do if a run fails.
  - A version is a saved copy of the project files at one moment. The person can go back to it.

## Rules that matter

- Deploy only what was accepted. If `GS status` shows the result is not approved, give the command it names.
- Real runs and test runs never write to the same place, because a test output mistaken for a real one is the likeliest silent mistake after deploy.
- One step to run: one command typed in the app, no terminal.
- The routine only reads the person's accounts and files outside the project, and writes only inside the project folder, unless the approved spec says otherwise.
- Nothing runs unattended unless the person asks for it after hearing the risks.

## Steps

1. Run `GS status` and act on it. Read SPEC.md, `docs/design.md`, PLAN.md and the project's CLAUDE.md to learn the steps of a run in order and where each writes. A starter may name the routine and its order under `routine` in `.gs/starter.json`.

2. Keep test runs and real runs apart. Start from `## Test data and real data` in `docs/design.md`, then confirm in the scripts where each actually writes. If they share a folder or a file name, make the smallest change that separates them (for example `out/test/` for test runs, and a first line "TEST RUN: made from test data" on every test output), then run `GS check`. If it needs more than a small change, run `GS change new "<title>"` and end on `/gs:2-define`.

3. Create the project skill `.claude/skills/<name>/SKILL.md`, named after what the person calls the result, so the command is `/<name>`. The description says in their words what it makes and when to use it. The body:
   - runs every step of a run in order. A step that is itself a project skill is followed by reading its file, because one skill cannot start another;
   - stops at the first failing step, says in one sentence which step failed and what the message means, and points to `/gs:fix`;
   - runs the check at the end;
   - reports only the counts and where the output is;
   - does a test run when given the argument `test`, and a real run otherwise.

   The app asks the person to allow this file to be created; tell them beforehand in one sentence that this prompt is expected.

4. Write `docs/run-book.md` in plain words, with exactly these headings:
   - `## How to run it`: the one command, and what the person sees when it finishes.
   - `## Test run versus real run`: which data each uses, where each writes, how to tell the outputs apart.
   - `## What it writes and where`: every file or folder a run writes, including the run log, one line each.
   - `## If it fails`: the messages a run can end with and what each means in one sentence, then: "Type `/gs:fix`."
   - `## Version`: the saved version the result was accepted at (short id and date), the version saved in step 6, and one line per recorded real run.

5. Do a test run (`/<name> test`) and confirm it wrote only to the test place. Then ask the person to type the command themselves for one real run, because that proves the one step works for them. Ask: "Please open the output. Is this your data, and is it correct? Answer yes, or tell me what is wrong." Something wrong goes to `/gs:fix`, not a quick edit. Record the run under `## Version`: date, time, command, counts, output path, check result.

6. Run `GS save "release: <project> deployed"` and write the short version id it prints into `## Version`.

7. Offer an unattended scheduled run as an optional extra, without setting it up. Say these three things, each as its own sentence. A scheduled run works only while the Claude app is open and the computer is on. It reads real data when nobody is there to watch, so you see a bad run only afterwards. Use the one command yourself for a few days before you schedule it. Set it up only if they ask, then add the schedule to `## How to run it`. For what to share and what to keep private, point to the plugin's `docs/safety.md`.

8. Run `GS done deploy`. Tell the person in two sentences what they can now run and which command runs it. Then say: "After the next run, type `/gs:7-operate`. That step tells you if the run was normal."
