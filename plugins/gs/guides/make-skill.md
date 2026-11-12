# Make a skill

A skill is a short written procedure that Claude follows whenever the person types its command or asks for that task. Done means: `.claude/skills/<name>/SKILL.md` exists, and the person has seen in three lines what it changes compared with working without it.

## Rules that matter

- At most four questions, one at a time, each with a recommended answer: what starts it, what the steps are, what must never happen, what a good result looks like. Skip any question the conversation already answers, because the person knows the procedure and Claude's job is to write it down.
- Steps that must come out the same every time become scripts that the skill calls; only judgement steps (wording, choosing what matters) are left to Claude, because a script does the same thing every time and Claude may not.
- Every "never" in the skill carries its reason, because Claude follows a rule more reliably when it knows what the rule prevents.
- Try it once with the skill and once without it on a real example, because a skill that changes nothing is not worth keeping.

## Steps

1. Run `GS status` and act on it.
2. Ask the questions, one per turn, with options written in the chat and your recommendation first. Use the argument as the starting description.
3. List the steps, each marked "script" or "Claude". If a step needs a new script and the spec and plan are not approved yet, keep that step as written instructions for now and say so; it can become a script later through `/gs:2-define`.
4. Write `.claude/skills/<name>/SKILL.md`, with a short lowercase name joined by hyphens:
   - frontmatter with `name` and a `description` that says what it does and when to use it, in the words the person uses for this task;
   - one sentence on what it is for;
   - the "never" rules, each with its reason;
   - the steps in order, naming any script it runs;
   - what a good result looks like, so Claude can check its own result.
   Keep it under about 60 lines; a long skill gets followed loosely.
5. Try it on a real example the person names. Run the task once following the skill, and once in a separate agent given only the plain request and told not to use the skill. Show the difference in three lines: what the skill made better, what came out the same, what to sharpen. If there is no real difference, say so and offer to sharpen or delete it.
6. Tell the person how to use and share it: type `/<name>` in this project; anyone who gets a copy of the project folder gets the skill too; to use it in every project, it can be copied to the personal skills folder (`~/.claude/skills/`), which Claude can do on request. For a fuller test, Anthropic's skill-creator plugin writes test requests, runs them with and without the skill and grades the results (install it with `/plugin install skill-creator@claude-plugins-official`).
7. Save a version: run `GS save "feat: <name> skill"`. End on the `NEXT:` line of `GS status`.
