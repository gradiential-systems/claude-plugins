---
name: help
description: "Type this if you do not know what to do next. Claude shows where you are in the seven steps and the one command to type next. Claude can also test that your computer is ready, and explain a word in plain language. Use when the person asks \"where am I\", \"what's next\", \"what do I do now\", \"where were we\", \"is my setup ready\", \"what does X mean\", \"I don't follow\", \"say that again\", or comes back to the project after a break."
argument-hint: "[a question, a word, or 'setup' (optional)]"
allowed-tools: Bash(python *gs.py*), Bash(python3 *gs.py*), Bash(py *gs.py*), PowerShell(python *gs.py*), PowerShell(py *gs.py*)
---

# Help

`GS` means `python "${CLAUDE_PLUGIN_ROOT}/scripts/gs.py"` (`python3` on macOS). Run each `GS` command by itself, never joined with `;` or `&&`: only the plain command runs without a permission prompt. You run commands; the person types only `/gs:` commands and never opens a terminal.

This command answers one of three things, chosen from what the person typed after it: where am I, is my setup ready, or what does that mean.

## How to write to the person

The person is an expert in their own work and is not a programmer. Everything they read must obey these rules: your messages in the chat, and the files you write for them.

- Write full sentences in short paragraphs. Use a numbered list only for choices, steps and items to check.
- Use at most 20 words for an instruction and 25 words for a description. Put one idea in each sentence.
- Use the active voice and say who does what. Put a condition before its instruction: "If the check fails, type `/gs:fix`."
- Use one word for one thing, and the same word every time.
- Use plain words. Do not use abbreviations, idioms, contractions or symbols in place of words. Use the person's own name for a thing, not its file name, unless they must open the file.
- Explain a technical word in one sentence the first time you use it in the conversation. Use these meanings:
  - Use the meanings in the last section of this skill.

## Rules that matter

- Change nothing: no files, installs, settings or new work, and never an approval. The one exception is a glossary entry they agree to (part 3).
- Report what a `GS` command printed in this turn, not what you remember, because the person will act on it.
- Keep it short: the map, at most five sentences, then exactly one next command.

## 1. Where am I (nothing typed, "what's next", "where were we")

1. Run `GS map` and show what it prints exactly, in a code block: the seven steps in order, marked `done` and `here`.
2. If the folder has a project, add at most three sentences. Leave out any that has nothing to say:
   - what is approved so far, or "nothing approved yet";
   - what the last check said, and whether the code has changed since;
   - what is waiting for their decision, as the question they are answering: for the spec, does `SPEC.md` describe what they want and how each part will be checked; for the plan, does `PLAN.md` break the work into the right steps; for a phase, is its result good enough to build on; for the result, is the finished system proven enough to use. Then give the three choices as three sentences: to accept, type `/gs:approve`; to revise, say what to change; to stop, say stop.
3. If the folder has no project, run `GS doctor` and report it as in part 2.
4. End on the command from the `NEXT:` line, as "Next, type `/gs:<step>`.", with one sentence that says what that step does.

## 2. Is my setup ready ("setup", "check my setup", "why isn't it working")

1. Run `GS doctor`. For each line it prints, write one sentence: the item in plain words and "is ready" or "is not ready". For an item that is not ready, add the one action the person can do in the app. If there is none, tell them to ask the person who looks after their computer.
   - Python not found: ask whoever looks after the computer. Stop the list here, because everything else needs it.
   - Git not found: the same person; the project still works, but versions are not saved.
   - Automatic reminders off: start a new session, or quit and reopen the app. The steps keep the same order and record without them.
2. If the project uses connected services (`GS doctor` names them; `setup_checks` in `.gs/starter.json` or the project `CLAUDE.md` says how to test each), make one small read-only call to each and report only whether it answered and a count. If a call fails or asks for a sign-in, the action is: open Settings, then Connectors, reconnect it, then type `/gs:help setup` again. A project that names no connected service needs none.
3. End with "Your computer is ready." or "Your computer is not ready. N items need an action.", then the first action, then the one next command.

## 3. What does that mean (a question, a word, "I don't follow", "too technical")

1. Find what to explain: what they typed, or else the last thing you said that they reacted to. If it could be either of two things, ask which, naming both.
2. Read `GLOSSARY.md` if it exists and the file the point is about, so the example comes from their own project.
3. Answer in three sentences: what it is, why it matters to the decision in front of them, and one example from their own project. Say it differently from the first time. Use the meanings below for the plugin's own words.
4. Ask: "Is that clear? If not, I can explain it in a different way." If not, try once more with a comparison from their own work; after that, offer to open the actual file or output together.
5. If the word is one of their own whose meaning they have just settled, offer to write it down; on a yes add it to `GLOSSARY.md` as `## <term>`, a one-sentence meaning, and `Example:` from this project. One meaning per word.
6. End on the `NEXT:` line of `GS status`.

## The plugin's own words, in plain language

- Project: this folder and everything in it that belongs to the work.
- Starter: a ready-made project. It has its own instructions, test data and checks.
- Connector: a link between the Claude app and one of your accounts, for example your email.
- Spec: the short written agreement of what the result must do. Its file is `SPEC.md`. You approve the spec before Claude builds anything.
- Acceptance check: one line of the spec. It says what must be true and how we test it.
- Approve: to accept what Claude showed you. Only you approve, and you do it when you type `/gs:approve`.
- Plan: the order of the work, in phases. Its file is `PLAN.md`.
- Phase: one small part of the plan. Claude builds it and tests it before the next phase starts.
- Script: a small program. It does the same thing the same way each time. Scripts do the dates, the counts and the sorting.
- Template: the fixed layout of the output. It stays apart from the data and the rules, so you can change one and not the others.
- Test data and real data: test data are saved examples that stay in the project. Real data are your own files and accounts on that day.
- Test: one automatic comparison of a result with the expected result.
- Check: the set of all the tests. It gives one result: pass or fail. A check is useful only if it can fail.
- Canary: a proof that the check can fail. Claude breaks one thing on purpose, and the check must then fail.
- Gate: a point where you examine the evidence and decide. You accept, revise (ask for a change) or stop.
- Spot check: one item that you compare with your own records.
- Verdict: one of three results: PROVEN, PARTLY PROVEN or NOT PROVEN. A script calculates it from the check, the canary, the acceptance checks and your spot check.
- Defect: a result that is different from what the spec says, or from what you expect.
- Run: one use of the finished result. A test run uses test data. A real run uses real data.
- Run-book: one page. It says how to run the result, what a run writes, and what to do if a run fails.
- Version: a saved copy of the project files at one moment. You can go back to it.
- Change request: a short file that describes one change you want. In a team, a ticket does the same job.
