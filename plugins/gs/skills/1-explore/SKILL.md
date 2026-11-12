---
name: 1-explore
description: "Step 1 of 7. Start here. Claude sets up the project in this folder. Then Claude looks at your files and your data. Nothing is decided or built in this step. Use when the person says \"get me started\", \"I want to build...\", \"look at my data\", \"what do we have to work with\", or types /gs:1-explore, optionally followed by the name of a starter."
argument-hint: "[starter name (optional)]"
allowed-tools: Bash(python *gs.py*), Bash(python3 *gs.py*), Bash(py *gs.py*), PowerShell(python *gs.py*), PowerShell(py *gs.py*)
---

# Step 1 of 7: Explore

`GS` means `python "${CLAUDE_PLUGIN_ROOT}/scripts/gs.py"` (`python3` on macOS; `py` on Windows when `python` is not found). Run each `GS` command by itself, never joined with `;` or `&&`: only the plain command runs without a permission prompt. You run commands; the person types only `/gs:` commands and never opens a terminal.

Done means: this folder is a project, `docs/explore-notes.md` says what is here and what the data looks like, and the person knows the next command.

## How to write to the person

The person is an expert in their own work and is not a programmer. Everything they read must obey these rules: your messages in the chat, and the files you write for them.

- Write full sentences in short paragraphs. Use a numbered list only for choices, steps and items to check.
- Use at most 20 words for an instruction and 25 words for a description. Put one idea in each sentence.
- Use the active voice and say who does what. Put a condition before its instruction: "If the check fails, type `/gs:fix`."
- Use one word for one thing, and the same word every time.
- Use plain words. Do not use abbreviations, idioms, contractions or symbols in place of words. Use the person's own name for a thing, not its file name, unless they must open the file.
- Explain a technical word in one sentence the first time you use it in the conversation. Use these meanings:
  - A project is this folder and everything in it that belongs to the work.
  - A starter is a ready-made project. It has its own instructions, test data and checks.
  - A connector is a link between the Claude app and one of the person's accounts.
  - The seven steps are Explore, Define, Design, Implement, Verify, Deploy and Operate. Each step ends with the command for the next step.

## Rules that matter

- Build nothing here: no project code, no saved scripts, no settings changes beyond the ones the starter asks for in Part B, because the Define step decides from what you find.
- Describe data by counts, field names, date ranges and shapes, not by contents, because the person may be sharing their screen. If they ask to see an item, show it.
- Look at files with the Read and file-search tools, one call each, never with a shell command such as `ls`, `cat` or `find`, because every shell command stops to ask the person for a permission they cannot judge. The one exception is the counting command in Part B step 3.
- Mark every fact as confirmed (and how: counted, read in a file, returned by a service) or assumed, because Define must not build on a guess it takes for a fact.

## Part A: set the project up (only when this folder has no project yet)

1. Run `GS status`.
   - A project past Explore: say so in one sentence and end on the command from the `NEXT:` line, unless the person asked to explore again.
   - A project at Explore: go to Part B.
   - No project yet: continue.

2. Decide what is being built.
   - The folder holds a file named `starter.json`: the person unpacked a starter here. Go to step 4 and run plain `GS init`, which uses the starter where it is. Skip step 3.
   - The person named a starter (the argument): use it.
   - The person already said what they want: use their sentence.
   - Otherwise run `GS starters` and ask one question, with the options written in the chat and also offered through the question tool when it is available: "What do you want to build in this folder?" The first option is "Something of my own. I describe it in one sentence." Each starter listed is a further option, with its one-line description as a full sentence.

3. If the folder already holds files of the person's (hidden system files do not count), ask whether these are the files to work from. If they are unrelated, recommend a new empty folder and carry on here only on a clear yes. Setup never replaces an existing file.

4. Run `GS init --starter <name>`, or `GS init` for something of their own.

5. For something of their own, write their sentence as the first line of `docs/decisions.md` under the heading `# Decisions`, as `D0. What we are building: <their words>`.

6. Tell the person what you created, in two or three short sentences: a hidden folder named `.gs` that keeps the record of their approvals, the starter files if there are any, and a first saved copy of the project. Carry straight on to Part B in the same turn.

## Part B: look at what is here

1. Read what the project declares: `.gs/starter.json` if present, the project `CLAUDE.md`, `README.md`, `docs/starter-brief.md` and `docs/decisions.md` if present. Note the sources the work will use.

2. Get the data in front of you.
   - Files the person brought (spreadsheets, exports, documents): they are the sources. If they named a source that is not in the folder, ask them to save an export of it here, because a file works on any computer and can be checked later.
   - A connected service (a connector in the Claude app): use it only when the starter declares it, or the person names it and it is available in this session. Read only. If it is missing or asks for a sign-in, give the one action ("Open Settings, then Connectors, and connect it again. Then type `/gs:1-explore` again.") and offer the export route instead.
   - A starter with its own data step (`data_step` in `.gs/starter.json`): when its data files are missing or older than today, ask for the settings it lists under `ask_first` in one question, tell the person what is about to be read using its `announce` line, then read the skill file it names and follow its steps exactly, in this turn.

3. Look at the data and count. With many files, or a large one, count with a one-off `python -c` command (standard library only) instead of reading item by item, and do not save it as a script. For each source find out:
   - what period it covers and how many items fall in each period that matters;
   - which fields each item has, and which are missing in some items;
   - the unusual cases, by shape: duplicates, blanks, dates in more than one format or time zone, totals rows mixed in with data, items cut off by a limit, and any the starter lists;
   - totals: items, sizes, date range, anything that came back truncated.

4. If a question needs an outside fact (a service's limit, a file format), run `GS guide research` and follow it for that one question.

5. Write `docs/explore-notes.md` with these sections:
   - `## What is already here`: the files and folders, one line each on what they are for.
   - `## Sources`: each source the work will use, how it is read, and what was read.
   - `## What the data looks like`: counts and shapes from step 3.
   - `## Facts`: two lists, `Confirmed` (each with how) and `Assumed`.
   - `## Open questions for Define`: each question the person must decide, in words they would understand without this file; the words that need an agreed meaning (the person's own terms, and any the starter lists under `terms_to_agree`); and settings that still hold example values.

   If the person names an item they do not want used, remove it from the saved data (the way the starter's data step describes, if there is one) and record only that one item was removed.

6. Run `GS done explore`.

7. Tell the person what you found, in one short paragraph. Include the one thing they are least likely to expect. End on the `NEXT:` line of `GS status`, normally "Next, type `/gs:2-define`. In that step we agree what to build."
