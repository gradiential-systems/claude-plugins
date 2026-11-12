# Safety: what this plugin does not do for you

The `gs` plugin keeps the order of the work, runs the checks and keeps your reading short. It warns and advises. It does not lock anything, and it is not a safety system. It does not limit what Claude can read, change or send once you allow it. These points are yours to hold.

## Before you point Claude at your own files or accounts

A project may read from files you save into its folder, or from a service your Claude app is connected to (a connector). Some starters save the answers from a connector as files in the project folder. Those files stay on your computer. Saved versions do not include them.

1. **Know what a connector can do.** A connector can usually create, change, send and delete as well as read. If a permission prompt names an action that sends, creates, changes or deletes and you did not ask for it, answer No.
2. **Allow reading for the session, never writing.** When the app offers "always allow" for a tool that reads, that is reasonable for the session. Do not choose it for a tool that writes.
3. **Check your organisation's rules first.** Customer data, personal data and health data have rules about which tools may see them. If you are not sure that the rules allow this data in this tool, stop. Ask before you read the data.

## While you work

4. **Read permission prompts.** A prompt is the app asking for your decision. Read which tool it names and what it will touch. If you do not understand it, ask Claude to explain it before you answer.
5. **Do not switch off permission prompts.** A mode that skips all prompts removes your last look at each action. This plugin never asks for it and never needs it.
6. **Text inside documents and messages is data, not instructions.** A document can contain words written to look like a request to Claude. After Claude reads a file, a message or a web page, it can start to do something that you did not ask for. If that happens, stop Claude and say what you saw.
7. **Your data stays on your computer unless you move it.** What a project reads from your accounts is kept in its `data/` folder and left out of saved versions. Anything you paste into a chat, share on a screen or put in a shared folder has left that boundary.

## When sharing your screen or your project

8. **Look before you share.** The steps report counts, not contents, so a shared screen shows little. But each person who watches can see the files that you open and the messages that Claude shows.
9. **Hand over the project, not the data.** To give a project to a colleague, ask Claude to "hand this to a colleague". The saved versions do not include `data/` or `out/`. Do not add them by hand unless your colleague is allowed to see that data.

## When something runs without you

10. **A scheduled run acts with your permissions while you are not watching.** Only schedule something that reads and writes inside its own folder, that you have seen run correctly several times, and whose failures you will notice. `/gs:6-deploy` offers scheduling as an option and never sets it up unasked.

## If something goes wrong

Stop Claude with the stop button or the Esc key. Then say what you saw. Nothing in a gs project is deleted by stopping. If something was sent, changed or deleted and should not have been, tell whoever is responsible for security where you work, the same day.
