# gs reference card

## If you remember one thing

Follow the numbers. If you lose your place, type `/gs:help`.

## The seven steps, in order

1. `/gs:1-explore` **Explore**: set up the project and look at what you have. Nothing is built.
2. `/gs:2-define` **Define**: Claude asks you a few questions, one at a time, then writes the spec. **You approve the spec.**
3. `/gs:3-design` **Design**: the picture of how it will work, and a plan in small phases. **You approve the plan.**
4. `/gs:4-implement` **Implement**: one phase is built and proved with a check. Type it again for each phase. **You approve each phase.**
5. `/gs:5-verify` **Verify**: independent evidence and a verdict: PROVEN, PARTLY PROVEN or NOT PROVEN. **You approve the result.**
6. `/gs:6-deploy` **Deploy**: make it a routine you run with one command.
7. `/gs:7-operate` **Operate**: keep it working, change it, share it.

## Three commands for any time

- `/gs:approve`: accept what Claude just showed you.
- `/gs:fix`: something is wrong. Say what you saw and what you expected.
- `/gs:help`: where am I, is my setup ready, what does that mean.

## At each decision, three choices

- **Accept**: type `/gs:approve`. Only this counts. "Yes" in the chat does not.
- **Revise**: say in your own words what to change.
- **Stop**: say "stop". Nothing is deleted.

## What you are checking at each decision

- **Spec**: does it describe what I want, and could each acceptance check actually fail?
- **Plan**: is each step marked script or AI for a good reason, and are the phases small?
- **Phase**: did the check pass, and does the one value I was shown match my own records?
- **Result**: what is the verdict, and what was not checked?

## Things you just ask for, in your own words

- "Explain that." / "What does that word mean?"
- "Show me a rough version first."
- "Look that up."
- "Review it more deeply."
- "What did we learn?"
- "Hand this to a colleague."
- "I keep doing this by hand. Turn it into a skill."

## What the plugin does for you

- **Order**: the agreed order is spec, plan, then code. If a step is skipped you are told, and you decide.
- **Quality**: the check runs when code changes, and once per project something is broken on purpose to prove the check can fail.
- **Short reading**: one question at a time, a short summary and one decision at a time.

It warns and advises. It does not lock anything.

## What stays with you

Safety. Read permission prompts. Allow reading. Answer No to an action that sends, creates, changes or deletes, unless you asked for that action. Never switch off permission prompts. See `safety.md`.

## Words

- **Spec**: what should be built and how each part will be checked. The agreement.
- **Plan**: the steps, in small phases.
- **Phase**: one small piece that can be seen working.
- **Check**: an automatic test. Useful only if it could have failed.
- **Verdict**: PROVEN, PARTLY PROVEN or NOT PROVEN, worked out by a script.
- **Script**: a small program. It does the same thing the same way each time.
- **Version**: a saved state of the project you can go back to.
- **Change request**: a short file describing one wish for a change. In a team, a ticket.
