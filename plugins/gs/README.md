# gs: a guided way to build small tools with Claude Code

`gs` is a Claude Code plugin from Gradiential Systems. It is for people who know their work well and are not programmers. You decide what Claude builds, and you check the result. Claude does the technical work in a fixed order. Claude tells you before it skips a step.

The plugin has ten commands. Seven commands are the steps. The number in each name gives the order:

```
/gs:1-explore    Set up the project and look at your files and data.
/gs:2-define     Agree what to build. You approve the written agreement (the spec).
/gs:3-design     Agree how it will work. You approve the plan.
/gs:4-implement  Build it in small parts (phases). You approve each part.
/gs:5-verify     Prove that it works. You approve the result.
/gs:6-deploy     Make it one command that you run yourself.
/gs:7-operate    Keep it working, change it, or give it to a colleague.
```

You can type three commands at any time:

```
/gs:approve      Accept what Claude showed you.
/gs:fix          Tell Claude that something is wrong.
/gs:help         Find where you are, or ask what a word means.
```

For everything else, ask in your own words. Some examples:

- "Explain that."
- "Show me a rough version first."
- "Look that up."
- "Review it more deeply."
- "Hand this to a colleague."
- "What did we learn?"
- "Turn this into a skill."

## What it does for you

- **It keeps the order.** The order is spec, then plan, then code. The spec is the written agreement of what the result must do. The plan is the order of the work. You approve each one when you type `/gs:approve`. No other words count as approval. If Claude writes code before you approve, the plugin tells you immediately. You then decide what happens.
- **It checks the work.** A check is a set of automatic tests. When code changes, the plugin runs the check and tells you if it fails. One time in each project, the plugin breaks something on purpose. The check must then fail, because a check that cannot fail proves nothing. A script, not Claude, calculates the final verdict: PROVEN, PARTLY PROVEN or NOT PROVEN.
- **It keeps your reading short.** Claude asks one question at a time and recommends an answer. At each decision, you get a short summary, the evidence and three choices: accept, revise or stop.

## Install

Open the Claude desktop app. Open the Code tab in a local session. Type these two lines into the prompt box, one at a time:

```
/plugin marketplace add gradiential-systems/claude-plugins
/plugin install gs@gradiential
```

Then start a new session, open an empty folder for your project, and type:

```
/gs:help
```

It shows the seven steps. It also tells you if Python, Git and the automatic reminders are ready on your computer.

You need: the Claude desktop app (or Claude Code) on a paid Claude plan, Python 3.11 or later, and Git.

## Use

To start, type `/gs:1-explore`. Say in one sentence what you want to build, or name the files that you want to use. Then follow the numbers. Each step ends with the next command. If you do not know where you are, type `/gs:help`.

At each decision point you have three choices:

- **Accept**: type `/gs:approve`.
- **Revise**: say in your own words what to change.
- **Stop**: say "stop". Claude deletes nothing.

## What you need to bring

You need a folder and an idea of what you want to build. The plugin needs no connector. A connector is a link between the Claude app and one of your accounts. The simplest source is a file that you save into the folder, for example a spreadsheet. If your Claude app has a connector and you ask Claude to use it, Claude reads from it.

## Starters

A starter is a ready-made project. It has its own instructions, test data and checks. No starter comes with this plugin. Each starter comes in a plugin of its own, which you install in the same way. `/gs:1-explore` lists the starters on your computer. `/gs:1-explore <name>` sets one up. The README of a starter tells you what it needs, including any connector. You do not need a starter. A project of your own starts from an empty folder.

## What the automatic reminders do, and what they do not

The plugin installs small programs that the app runs automatically. Their name is hooks. Hooks never refuse or undo anything. In a gs project, the hooks do five things:

1. They remind Claude where the project is at the start of each message.
2. They tell Claude and you when Claude writes code before you approve the spec and the plan.
3. They tell Claude and you when Claude changes a file that is part of the check.
4. They record your typed `/gs:approve`, so the approval on the record is yours and not from Claude.
5. They run the check after code changes, and they tell you if it fails.

Some starters ask for one more thing. The hooks then save each answer from the read tools that the starter names. The answers go to files in the project folder, so that a script builds the data files. Claude does not type your data again. The hooks save nothing in any other project.

Outside a gs project, the hooks do nothing.

The `gs` command that Claude runs at each step keeps the record correct. It marks a step as done only when the check passes. It records an approval only when you typed it. If a file that is part of the check changed, the verdict names that file.

If the hooks cannot start on your computer, `/gs:help` tells you. The steps keep the same order and the same record without the hooks.

The plugin is about process, quality and keeping your reading short. **It is not a safety system.** It does not stop Claude from reading, sending or deleting things you allow it to. Read `docs/safety.md` before you point it at your own files or accounts.

## What gets added to your project folder

- `.gs/`: the record of the current step, your approvals and the check results. Do not change it. The commands keep it correct.
- `.claude/settings.json`: five lines that let Claude run the plugin's own `gs.py` command in this project without asking each time. These lines allow nothing else. Each other command still asks you.
- `SPEC.md`, `PLAN.md`, and a `docs/` folder with the notes, the design, the verify report and the run-book.
- Saved versions, using Git, at each approval.

## Working with other people

The spec is the shared agreement, the saved versions are the history, and each wish for a change gets its own short file under `docs/changes/`. That is sufficient for one person. If more than one person or agent works on the same thing, use a ticket tool. Each change then has an owner, a status and a place for discussion.

## Tested with

Claude Sonnet 5.5 and Claude Opus 5.5.

## Licence and credits

MIT. See `LICENSE`. This plugin adapts ideas from several published skill collections. `NOTICE.md` credits them.
