#!/usr/bin/env python3
"""gs.py: state, gates, checks and hooks for the gs plugin.

Standard library only. Works on Python 3.8 and later, on Windows and macOS.
Every command prints plain sentences. Predictable problems print one line and
exit 1; they never print a traceback.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

SCHEMA = "gs/1"
STAGES = ["explore", "define", "design", "implement", "verify", "deploy", "operate"]
STAGE_TITLES = {s: s.capitalize() for s in STAGES}
COMMANDS = {name: "%d-%s" % (index + 1, name) for index, name in enumerate(STAGES)}
STAGE_PURPOSE = {
    "explore": "Set up the project and look at your files and data.",
    "define": "Agree what to build. You approve the written agreement (the spec).",
    "design": "Agree how it will work. You approve the plan.",
    "implement": "Build it in small parts (phases). You approve each part.",
    "verify": "Prove that it works. You approve the result.",
    "deploy": "Make it one command that you run yourself.",
    "operate": "Keep it working, change it, or give it to a colleague.",
}
GUIDES = ["prototype", "research", "review", "handoff", "lessons", "make-skill"]
ASK_IN_WORDS = ('"explain that", "show me a rough version first", "look that up", "review it more deeply", '
                '"hand this to a colleague", "what did we learn", "turn this into a skill"')


def step(stage):
    """The command a person types for a stage, for example /gs:2-define."""
    return "/gs:" + COMMANDS[stage]
CODE_EXT = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh", ".ps1", ".bat",
    ".cmd", ".sql", ".rb", ".go", ".rs", ".java", ".php", ".html", ".css",
}
ALWAYS_PROTECTED = [".gs/**"]
EXEMPT_FROM_GATE = ["prototype/**"]
SPEC_HEADINGS = [
    "Summary", "Who it is for", "Inputs", "Output", "Acceptance checks",
    "Out of scope", "Decisions", "Open questions",
]
PLAN_HEADINGS = ["Summary", "Phases", "Progress", "Decision log", "Surprises"]
DESIGN_HEADINGS = [
    "The picture", "Where things live", "Test data and real data",
    "When something goes wrong", "Risks",
]
SUMMARY_MAX_WORDS = 120
TOKEN_MAX_AGE_S = 15 * 60
HOOK_FRESH_S = 12 * 3600
CHECK_TIMEOUT_S = 150


class Problem(Exception):
    """A predictable problem: print one line, exit 1."""


# ---------------------------------------------------------------- utilities

def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def age_seconds(stamp):
    try:
        then = datetime.datetime.fromisoformat(stamp)
    except (TypeError, ValueError):
        return float("inf")
    return (datetime.datetime.now().astimezone() - then).total_seconds()


def clock(stamp):
    try:
        return datetime.datetime.fromisoformat(stamp).strftime("%H:%M")
    except (TypeError, ValueError):
        return "?"


def out(*lines):
    for line in lines:
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode("ascii", "replace").decode("ascii"))


def read_text(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        return ""


def write_text(path, text):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temp, path)


def read_json(path, default=None):
    text = read_text(path)
    if not text.strip():
        return {} if default is None else default
    try:
        return json.loads(text)
    except ValueError:
        return {} if default is None else default


def write_json(path, data):
    write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def text_hash(text):
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    return hashlib.sha256("\n".join(lines).strip().encode("utf-8")).hexdigest()[:16]


def glob_to_regex(pattern):
    pattern = pattern.replace("\\", "/")
    parts = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            parts.append("(?:.*/)?")
            index += 3
        elif pattern.startswith("**", index):
            parts.append(".*")
            index += 2
        elif pattern[index] == "*":
            parts.append("[^/]*")
            index += 1
        elif pattern[index] == "?":
            parts.append("[^/]")
            index += 1
        else:
            parts.append(re.escape(pattern[index]))
            index += 1
    return re.compile("^" + "".join(parts) + "$", re.IGNORECASE)


def matches_any(rel, patterns):
    rel = rel.replace("\\", "/")
    return any(glob_to_regex(p).match(rel) for p in patterns or [])


def plugin_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def plugin_data_dir():
    """One fixed folder, so that a hook and a command run by Claude both find the same files."""
    return os.path.join(os.path.expanduser("~"), ".claude", "gs-plugin-data")


LAUNCHER = ""   # the command name that started this hook (python, python3 or py), when known
GS_ALLOW = ["Bash(python *gs.py*)", "Bash(python3 *gs.py*)", "Bash(py *gs.py*)",
            "PowerShell(python *gs.py*)", "PowerShell(py *gs.py*)"]


def allow_gs_command(root):
    """Let the gs command run without a permission prompt in this project, in every turn.

    The skills already allow it while they run; this covers a plain-words request, where no skill is loaded.
    It names the gs command only. The project's own scripts still go through the normal prompt."""
    path = os.path.join(root, ".claude", "settings.json")
    settings = read_json(path) or {}
    if not isinstance(settings, dict):
        return
    allow = settings.setdefault("permissions", {}).setdefault("allow", [])
    if not isinstance(allow, list):
        return
    added = [rule for rule in GS_ALLOW if rule not in allow]
    if added:
        allow.extend(added)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_json(path, settings)


def python_command():
    return os.environ.get("GS_PYTHON") or sys.executable or "python"


# ------------------------------------------------------------------- state

def find_root(start=None):
    """Walk up from start to the folder that holds .gs/state.json."""
    here = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isfile(os.path.join(here, ".gs", "state.json")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


class Project:
    def __init__(self, root):
        self.root = root
        self.state_path = os.path.join(root, ".gs", "state.json")
        self.runtime_path = os.path.join(root, ".gs", "runtime.json")
        self.state = read_json(self.state_path)
        self.runtime = read_json(self.runtime_path)
        self.state.setdefault("gates", {})
        self.state.setdefault("stage", "explore")
        self.state.setdefault("phase", 1)
        self.state.setdefault("check", {})
        self.state.setdefault("starter_cfg", {})

    # paths
    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def rel(self, file_path):
        try:
            rel = os.path.relpath(os.path.abspath(file_path), self.root)
        except ValueError:
            return None
        rel = rel.replace("\\", "/")
        return None if rel.startswith("..") else rel

    # persistence
    def save(self):
        write_json(self.state_path, self.state)

    def save_runtime(self):
        write_json(self.runtime_path, self.runtime)

    def log(self, event, **fields):
        entry = dict(at=now(), event=event, **fields)
        folder = self.path(".gs")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "log.jsonl"), "a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")

    # configuration
    @property
    def cfg(self):
        return self.state.get("starter_cfg") or {}

    def code_globs(self):
        return self.cfg.get("code_globs") or []

    def protected_globs(self):
        return ALWAYS_PROTECTED + list(self.cfg.get("protected_globs") or [])

    def is_code(self, rel):
        if matches_any(rel, EXEMPT_FROM_GATE):
            return False
        if self.code_globs() and matches_any(rel, self.code_globs()):
            return True
        return os.path.splitext(rel)[1].lower() in CODE_EXT

    def phases(self):
        return self.state.get("phases") or self.cfg.get("phases") or []

    def phase_count(self):
        return len(self.phases())

    def phase_info(self, number=None):
        number = number or self.state.get("phase", 1)
        for item in self.phases():
            if int(item.get("n", 0)) == int(number):
                return item
        return {}

    # gates
    def gate(self, name):
        return self.state["gates"].setdefault(name, {"approved": False})

    def approved(self, name):
        return bool(self.gate(name).get("approved"))

    def waiting(self):
        return self.state.get("waiting")

    def frozen_text(self, name):
        if name == "spec":
            return read_text(self.path("SPEC.md"))
        if name == "plan":
            sections = md_sections(read_text(self.path("PLAN.md")))
            return "\n".join(sections.get(h.lower(), "") for h in ("Summary", "Phases"))
        return ""

    def reopen_changed_gates(self):
        """An approved spec or plan that was edited afterwards is no longer approved."""
        changed = []
        for name in ("spec", "plan"):
            gate = self.gate(name)
            if gate.get("approved") and gate.get("hash") != text_hash(self.frozen_text(name)):
                gate["approved"] = False
                gate["reopened_at"] = now()
                self.state["waiting"] = name
                changed.append(name)
                self.log("gate_reopened", gate=name)
        if changed:
            self.save()
        return changed

    def building_unlocked(self):
        return self.approved("spec") and self.approved("plan")


def load_project(start=None, required=True):
    root = find_root(start)
    if not root:
        if required:
            raise Problem("This folder is not a gs project yet. Next: %s" % step("explore"))
        return None
    return Project(root)


# ---------------------------------------------------------------- markdown

def md_sections(text):
    """Map each '## Heading' (lower-cased) to the text under it."""
    sections = {}
    current = None
    for line in text.replace("\r\n", "\n").split("\n"):
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match and not line.startswith("###"):
            current = match.group(1).strip().lower()
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def numbered_items(text):
    """Split text into blocks that each start with '1.' or '1)'."""
    items = []
    for line in text.split("\n"):
        if re.match(r"^\s*\d+[.)]\s+\S", line):
            items.append(line)
        elif items:
            items[-1] += "\n" + line
    return items


def missing_headings(sections, wanted, file_name):
    problems = []
    for heading in wanted:
        if heading.lower() not in sections:
            problems.append("%s has no '## %s' section." % (file_name, heading))
    return problems


def lint_spec(project):
    path = project.path("SPEC.md")
    text = read_text(path)
    if not text.strip():
        return ["SPEC.md does not exist yet or is empty."]
    sections = md_sections(text)
    problems = missing_headings(sections, SPEC_HEADINGS, "SPEC.md")
    summary = sections.get("summary", "").strip()
    if "summary" in sections and not summary:
        problems.append("The Summary is empty.")
    words = len(summary.split())
    if words > SUMMARY_MAX_WORDS:
        problems.append("The Summary has %d words; the limit is %d so that it can be read in one go."
                        % (words, SUMMARY_MAX_WORDS))
    for heading in ("who it is for", "inputs", "output", "out of scope"):
        if heading in sections and not sections[heading].strip():
            problems.append("The '%s' section is empty." % heading.capitalize())
    checks = numbered_items(sections.get("acceptance checks", ""))
    if "acceptance checks" in sections and not checks:
        problems.append("Acceptance checks has no numbered check.")
    for index, block in enumerate(checks, 1):
        if "how we check:" not in block.lower():
            problems.append("Acceptance check %d has no 'How we check:' line." % index)
    for line in sections.get("open questions", "").split("\n"):
        stripped = line.strip().lstrip("-*0123456789.) ").strip()
        if not stripped or stripped.lower().rstrip(".") in ("none", "none yet", "nothing open"):
            continue
        if "deferred:" not in stripped.lower():
            problems.append("Open question not settled or marked 'deferred: <reason>': %s" % stripped[:70])
    if re.search(r"\b(TBD|TODO)\b|\?\?\?", text):
        problems.append("SPEC.md still contains a placeholder (TBD, TODO or ???).")
    return problems


def lint_plan(project):
    problems = []
    design = read_text(project.path("docs", "design.md"))
    if not design.strip():
        problems.append("docs/design.md does not exist yet or is empty.")
    else:
        sections = md_sections(design)
        problems += missing_headings(sections, DESIGN_HEADINGS, "docs/design.md")
        steps = numbered_items(sections.get("the picture", ""))
        if "the picture" in sections and not steps:
            problems.append("The picture has no numbered step.")
        for index, block in enumerate(steps, 1):
            first = block.split("\n")[0].lower()
            if "[script]" not in first and "[ai]" not in first:
                problems.append("Step %d of the picture is not marked [script] or [AI]." % index)
        for heading in DESIGN_HEADINGS[1:]:
            if heading.lower() in sections and not sections[heading.lower()].strip():
                problems.append("The '%s' section of docs/design.md is empty." % heading)
    plan = read_text(project.path("PLAN.md"))
    if not plan.strip():
        problems.append("PLAN.md does not exist yet or is empty.")
        return problems
    sections = md_sections(plan)
    problems += missing_headings(sections, PLAN_HEADINGS, "PLAN.md")
    summary = sections.get("summary", "").strip()
    if "summary" in sections and not summary:
        problems.append("The Summary of PLAN.md is empty.")
    if len(summary.split()) > SUMMARY_MAX_WORDS:
        problems.append("The Summary of PLAN.md has %d words; the limit is %d."
                        % (len(summary.split()), SUMMARY_MAX_WORDS))
    phases = parse_plan_phases(plan)
    if "phases" in sections and not phases:
        problems.append("PLAN.md has no '### Phase 1: <name>' heading.")
    for item in phases:
        for label in ("Builds:", "Done when:", "Check:"):
            if label.lower() not in item["text"].lower():
                problems.append("Phase %s has no '%s' line." % (item["n"], label))
    return problems


def parse_plan_phases(plan_text):
    phases = []
    for line in plan_text.replace("\r\n", "\n").split("\n"):
        match = re.match(r"^###\s+Phase\s+(\d+)\s*[:.\-]?\s*(.*)$", line, re.IGNORECASE)
        if match:
            phases.append({"n": int(match.group(1)), "name": match.group(2).strip(), "text": ""})
        elif line.startswith("## ") and phases:
            break
        elif phases:
            phases[-1]["text"] += line + "\n"
    return phases


def lint_verify_report(project):
    text = read_text(project.path("docs", "verify-report.md"))
    if not text.strip():
        return ["docs/verify-report.md does not exist yet or is empty."], {}
    sections = md_sections(text)
    problems = missing_headings(sections, ["Acceptance checks", "Spot check"], "docs/verify-report.md")
    tally = {"met": 0, "not met": 0, "not checked": 0}
    for index, block in enumerate(numbered_items(sections.get("acceptance checks", "")), 1):
        first = block.split("\n")[0].lower()
        found = [key for key in ("not met", "not checked", "met") if "[%s]" % key in first]
        if not found:
            problems.append("Line %d of the verify report has no [met], [not met] or [not checked] mark." % index)
        else:
            tally[found[0]] += 1
    spot = "not done"
    match = re.search(r"result:\s*(.+)", sections.get("spot check", ""), re.IGNORECASE)
    if match:
        word = match.group(1).strip().lower()
        if word.startswith("matched"):
            spot = "matched"
        elif word.startswith("did not match"):
            spot = "did not match"
    elif "spot check" in sections:
        problems.append("The Spot check section has no 'Result:' line (matched, did not match, or not done).")
    tally["spot"] = spot
    return problems, tally


# -------------------------------------------------------------------- check

def check_command(project, full=False):
    cfg = project.cfg
    stage_index = STAGES.index(project.state["stage"])
    full = full or stage_index >= STAGES.index("verify")
    command = project.state["check"].get("command")
    if not command:
        key = "full_check_command" if full and cfg.get("full_check_command") else "check_command"
        command = cfg.get(key)
    if not command:
        if os.path.isfile(project.path("check.py")):
            command = ["{python}", "check.py"]
        elif os.path.isdir(project.path("tests")):
            command = ["{python}", "-m", "unittest", "discover", "-s", "tests"]
        else:
            return None
    phase = min(int(project.state.get("phase", 1)), max(project.phase_count(), 1))
    resolved = []
    for part in command:
        resolved.append(part.replace("{python}", python_command()).replace("{phase}", str(phase)))
    return resolved


def summarise_output(text, limit=8):
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n") if line.strip()]
    key = [line for line in lines if re.search(
        r"FAIL|ERROR|Error|IMPLEMENTATION_MISSING|Traceback|CHECK:|AssertionError|not found", line)]
    chosen = key[-limit:] if key else lines[-limit:]
    return [line[:200] for line in chosen]


def run_check(project, full=False, record=True):
    command = check_command(project, full)
    if not command:
        raise Problem("There is no check to run yet. A check is created in the Implement step (tests in a 'tests' folder).")
    started = now()
    try:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        result = subprocess.run(command, cwd=project.root, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=CHECK_TIMEOUT_S, env=env)
        output = result.stdout.decode("utf-8", "replace")
        ok = result.returncode == 0
    except subprocess.TimeoutExpired as error:
        output = (error.stdout or b"").decode("utf-8", "replace") + "\nThe check ran longer than %d seconds and was stopped." % CHECK_TIMEOUT_S
        ok = False
    except OSError as error:
        output = "The check could not start: %s" % error
        ok = False
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_rel = ".gs/logs/check-%s.txt" % stamp
    write_text(project.path(*log_rel.split("/")), "$ %s\n%s" % (" ".join(command), output))
    summary = summarise_output(output)
    if record:
        if project.state.get("verdict") and project.state["stage"] == "verify" and project.runtime.get("dirty"):
            project.state["verdict"]["stale"] = True
        project.state["check"]["last"] = {
            "ok": ok, "at": started, "full": bool(full or STAGES.index(project.state["stage"]) >= 4),
            "phase": project.state.get("phase", 1), "summary": summary, "log": log_rel,
        }
        project.save()
        if ok:
            project.runtime["dirty"] = False
            project.save_runtime()
        project.log("check", ok=ok, log=log_rel)
    return ok, summary, log_rel


def check_lines(ok, summary, log_rel):
    lines = ["CHECK: PASS" if ok else "CHECK: FAIL"]
    if not ok:
        lines += ["  " + line for line in summary]
    lines.append("Full output: %s" % log_rel)
    return lines


# ---------------------------------------------------------------- commands

def status_lines(project):
    project.reopen_changed_gates()
    state = project.state
    stage = state["stage"]
    lines = ["Project: %s%s" % (state.get("project", os.path.basename(project.root)),
                                " (starter: %s)" % state["starter"] if state.get("starter") else "")]
    lines.append("Step %d of %d: %s" % (STAGES.index(stage) + 1, len(STAGES), STAGE_TITLES[stage]))
    for name, label in (("spec", "Spec"), ("plan", "Plan")):
        gate = project.gate(name)
        if gate.get("approved"):
            lines.append("%s: approved at %s" % (label, clock(gate.get("at"))))
        elif gate.get("reopened_at"):
            lines.append("%s: changed after approval, so it needs approving again" % label)
        else:
            lines.append("%s: not approved yet" % label)
    total = project.phase_count()
    if total and STAGES.index(stage) >= STAGES.index("implement"):
        number = min(int(state.get("phase", 1)), total)
        done = sum(1 for item in project.phases() if project.approved("phase:%s" % item["n"]))
        lines.append("Phases: %d of %d accepted. Current: phase %d, %s"
                     % (done, total, number, project.phase_info(number).get("name", "")))
    last = state["check"].get("last")
    if last:
        lines.append("Last check: %s at %s%s" % ("PASS" if last.get("ok") else "FAIL", clock(last.get("at")),
                                                 " (code changed since)" if project.runtime.get("dirty") else ""))
    elif STAGES.index(stage) >= STAGES.index("implement"):
        lines.append("Last check: none yet")
    verdict = state.get("verdict") or {}
    if stage == "verify" and verdict.get("word"):
        lines.append("Verdict: %s%s" % (verdict["word"], " (from before the latest change; verify again)" if verdict.get("stale") else ""))
    waiting = project.waiting()
    if waiting:
        lines.append("Waiting for the person's decision on %s: accept by typing /gs:approve, or say what to change, or stop."
                     % gate_label(waiting))
        lines.append("NEXT: /gs:approve")
    elif state.get("stopped"):
        lines.append("This project was stopped by the person. To carry on, they say: resume the project. NEXT: /gs:help")
    elif state.get("open_change"):
        lines.append("A change request is open (%s). It goes through Define first, so that the person approves the "
                     "changed spec." % state["open_change"])
        lines.append("NEXT: %s" % step("define"))
    elif stage == "verify" and verdict.get("word") == "NOT PROVEN" and not verdict.get("stale"):
        lines.append("NEXT: /gs:fix")
    else:
        lines.append("NEXT: %s" % step(stage))
    return lines


def gate_label(name):
    if name.startswith("phase:"):
        return "phase %s" % name.split(":", 1)[1]
    return {"spec": "the spec", "plan": "the design and plan", "result": "the result"}.get(name, name)


def cmd_status(args):
    project = load_project()
    out(*status_lines(project))


def git(project, *git_args):
    try:
        result = subprocess.run(["git"] + list(git_args), cwd=project.root, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=60)
        return result.returncode == 0, result.stdout.decode("utf-8", "replace").strip()
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)


def copy_starter(source, target):
    copied, skipped = 0, []
    for folder, dirs, files in os.walk(source):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        rel_folder = os.path.relpath(folder, source)
        for name in files:
            if rel_folder == "." and name == "starter.json":
                continue
            if name == ".DS_Store":
                continue
            rel = os.path.normpath(os.path.join(rel_folder, name))
            destination = os.path.join(target, rel)
            if os.path.exists(destination):
                skipped.append(rel.replace("\\", "/"))
                continue
            os.makedirs(os.path.dirname(destination) or target, exist_ok=True)
            shutil.copyfile(os.path.join(folder, name), destination)
            copied += 1
    return copied, skipped


def protected_files(project):
    """Hashes of the starter's answer key and check files as they are now."""
    globs = list(project.cfg.get("protected_globs") or [])
    found = {}
    if not globs:
        return found
    for folder, dirs, files in os.walk(project.root):
        dirs[:] = [d for d in dirs if d not in (".git", ".gs", "__pycache__")]
        for name in files:
            rel = os.path.relpath(os.path.join(folder, name), project.root).replace("\\", "/")
            if matches_any(rel, globs):
                try:
                    with open(os.path.join(folder, name), "rb") as handle:
                        found[rel] = hashlib.sha256(handle.read()).hexdigest()[:16]
                except OSError:
                    pass
    return found


def record_protected(project):
    files = protected_files(project)
    if files:
        write_json(project.path(".gs", "protected.json"), {"at": now(), "files": files})


def protected_changes(project):
    """Answer-key or check files that differ from the copy recorded at setup."""
    recorded = (read_json(project.path(".gs", "protected.json")) or {}).get("files") or {}
    if not recorded:
        return []
    current = protected_files(project)
    changed = [rel for rel, digest in recorded.items() if current.get(rel) != digest]
    changed += [rel for rel in current if rel not in recorded]
    return sorted(changed)


def starter_folders():
    """Every starter this computer has, as name -> folder. A starter is a folder that holds a starter.json.

    Starters do not come with this plugin. They come in plugins of their own, each with a 'starters' folder,
    and this finds them in the list of installed plugins that Claude Code keeps. GS_STARTER_PATH adds folders."""
    roots = [os.path.join(plugin_root(), "starters")]
    roots += [folder for folder in os.environ.get("GS_STARTER_PATH", "").split(os.pathsep) if folder]
    config = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    installed = (read_json(os.path.join(config, "plugins", "installed_plugins.json")) or {}).get("plugins") or {}
    for entries in installed.values():
        for entry in entries if isinstance(entries, list) else []:
            if isinstance(entry, dict) and entry.get("installPath"):
                roots.append(os.path.join(entry["installPath"], "starters"))
    found = {}
    for root in roots:
        if os.path.isdir(root):
            for name in sorted(os.listdir(root)):
                if os.path.isfile(os.path.join(root, name, "starter.json")):
                    found.setdefault(name, os.path.join(root, name))
    return found


def starter_source(name):
    """An installed starter, by name, or any folder that holds a starter.json, by path."""
    folders = starter_folders()
    if name in folders:
        return folders[name]
    folder = os.path.abspath(os.path.expanduser(name))
    if os.path.isfile(os.path.join(folder, "starter.json")):
        return folder
    raise Problem("There is no starter called '%s'. Installed starters: %s. A starter comes in a plugin of its own; "
                  "it can also be given as the path of a folder that holds a starter.json."
                  % (name, ", ".join(sorted(folders)) or "none"))


def cmd_init(args):
    root = os.getcwd()
    if find_root(root):
        out("This folder is already a gs project.")
        return cmd_status(args)
    cfg = {}
    copied, skipped = 0, []
    if args.starter:
        source = starter_source(args.starter)
        cfg = read_json(os.path.join(source, "starter.json"))
        args.starter = cfg.get("name") or os.path.basename(source)
        need = cfg.get("min_python")
        if need and not os.environ.get("GS_PYTHON"):
            have = sys.version_info[:2]
            want = tuple(int(x) for x in need.split(".")[:2])
            if have < want:
                raise Problem("This starter needs Python %s or later; this computer runs Python %d.%d."
                              % (need, have[0], have[1]))
        copied, skipped = copy_starter(source, root)
    os.makedirs(os.path.join(root, ".gs", "logs"), exist_ok=True)
    os.makedirs(os.path.join(root, "docs"), exist_ok=True)
    state = {
        "schema": SCHEMA, "project": args.name or args.starter or os.path.basename(root),
        "starter": args.starter or None, "starter_cfg": cfg, "stage": "explore", "phase": 1,
        "gates": {}, "check": {}, "created_at": now(),
    }
    write_json(os.path.join(root, ".gs", "state.json"), state)
    if cfg:
        write_json(os.path.join(root, ".gs", "starter.json"), cfg)
    project = Project(root)
    record_protected(project)
    allow_gs_command(root)
    ignore_path = project.path(".gitignore")
    ignore = read_text(ignore_path)
    wanted = [line for line in (".gs/runtime.json", ".gs/logs/") if line not in ignore.split("\n")]
    if wanted:
        write_text(ignore_path, ignore.rstrip("\n") + ("\n" if ignore.strip() else "") + "\n".join(wanted) + "\n")
    notes = []
    if not os.path.isdir(project.path(".git")):
        ok, _ = git(project, "init")
        if ok:
            git(project, "config", "core.autocrlf", "false")
            if not git(project, "config", "user.email")[1]:
                git(project, "config", "user.email", "gs@localhost")
                git(project, "config", "user.name", "gs project")
        else:
            notes.append("Git did not start, so versions are not being saved yet.")
    git(project, "add", "-A")
    ok, _ = git(project, "commit", "-m", "chore: start project with gs")
    project.log("init", starter=args.starter)
    out("Started the project '%s' in this folder." % state["project"])
    if args.starter:
        out("Copied %d starter files%s." % (copied, " (%d already existed and were left alone)" % len(skipped) if skipped else ""))
    out("Versions are saved with git." if ok else "The first version could not be saved; ask for 'save a version' later.")
    out(*notes)
    out("The project is set up. NEXT: %s (step 1, Explore)" % step("explore"))


def cmd_lint(args):
    project = load_project()
    problems = lint_spec(project) if args.what == "spec" else lint_plan(project)
    if problems:
        out("%d thing(s) to fix before this can go to the person:" % len(problems))
        out(*["- " + problem for problem in problems[:12]])
        raise SystemExit(1)
    out("The %s is complete enough to show the person." % args.what)


def cmd_done(args):
    project = load_project()
    project.reopen_changed_gates()
    state = project.state
    stage = args.stage
    if stage == "phase":
        stage = "implement"
    current = state["stage"]
    if STAGES.index(stage) > STAGES.index(current):
        raise Problem("%s cannot be finished yet: the project is still at %s. Next: %s"
                      % (STAGE_TITLES[stage], STAGE_TITLES[current], step(current)))
    same_gate = (stage, project.waiting()) in (("define", "spec"), ("design", "plan"))
    if project.waiting() and stage != current and not same_gate:
        raise Problem("Waiting for the person's decision on %s. Next: /gs:approve" % gate_label(project.waiting()))
    if stage == "explore":
        if not read_text(project.path("docs", "explore-notes.md")).strip():
            raise Problem("docs/explore-notes.md is missing or empty, so Explore is not finished.")
        if current == "explore":
            state["stage"] = "define"
        finish(project, "explore", "Explore is finished. NEXT: %s" % step("define"))
    elif stage == "define":
        problems = lint_spec(project)
        if problems:
            raise Problem("The spec is not ready: %s (run 'lint spec' for the list)" % problems[0])
        state["waiting"] = "spec"
        finish(project, "define", "The spec is ready for the person's decision. NEXT: /gs:approve")
    elif stage == "design":
        if not project.approved("spec"):
            raise Problem("The spec is not approved yet, so the design cannot be finished. Next: /gs:approve")
        problems = lint_plan(project)
        if problems:
            raise Problem("The design and plan are not ready: %s (run 'lint plan' for the list)" % problems[0])
        state["waiting"] = "plan"
        finish(project, "design", "The design and plan are ready for the person's decision. NEXT: /gs:approve")
    elif stage == "implement":
        if not project.building_unlocked():
            raise Problem("The spec and plan must both be approved before a phase can be finished. Next: /gs:help")
        ok, summary, log_rel = fresh_check(project)
        if not ok:
            out(*check_lines(ok, summary, log_rel))
            raise Problem("Phase %s is not done: its check is failing." % state.get("phase", 1))
        number = min(int(state.get("phase", 1)), max(project.phase_count(), 1))
        state["waiting"] = "phase:%d" % number
        finish(project, "phase", "Phase %d passes its check and is ready for the person's decision. NEXT: /gs:approve" % number)
    elif stage == "verify":
        ok, summary, log_rel = fresh_check(project, full=True)
        if not ok:
            out(*check_lines(ok, summary, log_rel))
            raise Problem("Verify is not done: the full check is failing.")
        if not (state["check"].get("canary") or {}).get("ok"):
            raise Problem("No proof yet that the check can fail. Run 'canary' first.")
        problems, _ = lint_verify_report(project)
        if problems:
            raise Problem("The verify report is not ready: %s" % problems[0])
        word, reasons = compute_verdict(project)
        state["verdict"] = {"word": word, "at": now(), "reasons": reasons}
        if word == "NOT PROVEN":
            state.pop("waiting", None)
            finish(project, "verify", "Verdict: NOT PROVEN (%s). There is nothing sound to accept yet, so no gate is "
                   "waiting. NEXT: /gs:fix" % "; ".join(reasons[:3]))
        else:
            state["waiting"] = "result"
            finish(project, "verify", "Verdict: %s. The result is ready for the person's decision. NEXT: /gs:approve" % word)
    elif stage == "deploy":
        if not project.approved("result"):
            raise Problem("The result is not accepted yet, so there is nothing to deploy. Next: /gs:help")
        if not read_text(project.path("docs", "run-book.md")).strip():
            raise Problem("docs/run-book.md is missing or empty, so Deploy is not finished.")
        if current == "deploy":
            state["stage"] = "operate"
        finish(project, "deploy", "Deploy is finished. NEXT: %s" % step("operate"))
    else:
        out("Operate has no finish line: it is the ongoing care of something that runs. NEXT: %s" % step("operate"))


def finish(project, event, message):
    project.save()
    project.log("done", stage=event)
    out(message)


def fresh_check(project, full=False):
    last = project.state["check"].get("last") or {}
    same_scope = bool(last.get("full")) == bool(full or STAGES.index(project.state["stage"]) >= 4)
    same_phase = last.get("phase") == project.state.get("phase", 1)
    if last.get("ok") and same_scope and same_phase and not project.runtime.get("dirty") and age_seconds(last.get("at")) < 1800:
        return True, last.get("summary", []), last.get("log", "")
    return run_check(project, full)


def hooks_guard_approvals(project):
    return age_seconds(project.runtime.get("prompt_hook_seen_at")) < HOOK_FRESH_S


def approve_gate(project, note="", typed_by_person=False):
    """Approve the waiting gate. Returns the lines to show. Raises Problem when it cannot."""
    project.reopen_changed_gates()
    state = project.state
    name = project.waiting()
    if not name:
        raise Problem("Nothing is waiting for a decision right now. Next: /gs:help")
    if (not typed_by_person and hooks_guard_approvals(project)
            and age_seconds(project.runtime.get("human_token_at")) > TOKEN_MAX_AGE_S):
        raise Problem("An approval has to come from the person, and no typed approval was seen. "
                      "Ask the person to type /gs:approve (or the single word: approve) in the chat.")
    if name == "spec":
        problems = lint_spec(project)
    elif name == "plan":
        problems = lint_plan(project)
    elif name.startswith("phase:"):
        ok, summary, log_rel = fresh_check(project)
        problems = [] if ok else ["the check for this phase is failing (%s)" % log_rel]
    else:
        word = (state.get("verdict") or {}).get("word")
        problems = ["the verdict is NOT PROVEN, so there is nothing sound to accept yet"] if word == "NOT PROVEN" else []
        if not word:
            problems = ["Verify has not produced a verdict yet"]
    if problems:
        raise Problem("This cannot be approved yet: %s" % problems[0])
    gate = project.gate(name)
    gate.update({"approved": True, "at": now(), "note": note or ""})
    gate.pop("reopened_at", None)
    if name in ("spec", "plan"):
        gate["hash"] = text_hash(project.frozen_text(name))
        if state.get("verdict"):
            state["verdict"]["stale"] = True
    state.pop("waiting", None)
    project.runtime.pop("human_token_at", None)
    if name == "spec":
        state.pop("open_change", None)
        if state["stage"] == "define":
            state["stage"] = "design"
        message = "The spec is approved."
    elif name == "plan":
        if not project.cfg.get("phases"):
            state["phases"] = [{"n": p["n"], "name": p["name"]} for p in parse_plan_phases(read_text(project.path("PLAN.md")))]
        if state["stage"] == "design":
            state["stage"] = "implement"
            state["phase"] = 1
        message = "The design and plan are approved. Building is unlocked."
    elif name.startswith("phase:"):
        number = int(name.split(":", 1)[1])
        if number >= project.phase_count():
            state["stage"] = "verify"
            message = "Phase %d is accepted. All phases are built." % number
        else:
            state["phase"] = number + 1
            message = "Phase %d is accepted." % number
    else:
        gate["verdict"] = (state.get("verdict") or {}).get("word")
        if state["stage"] == "verify":
            state["stage"] = "deploy"
        message = "The result is accepted (%s)." % gate["verdict"]
    project.save()
    project.save_runtime()
    project.log("approved", gate=name, note=note or "", typed_by_person=typed_by_person)
    saved, _ = git(project, "add", "-A")
    if saved:
        git(project, "commit", "-m", "chore: %s approved" % gate_label(name))
    return [message, status_lines(project)[-1]]


def cmd_approve(args):
    out(*approve_gate(load_project(), args.note))


def cmd_revise(args):
    project = load_project()
    name = project.waiting()
    if not name:
        out("Nothing was waiting for a decision, so there is nothing to reopen.")
        return
    project.state.pop("waiting", None)
    project.save()
    project.log("revise", gate=name, note=args.note or "")
    out("Reopened %s for changes. When the change is made, finish the step again so it returns to the person."
        % gate_label(name))


def cmd_stop(args):
    project = load_project()
    project.state["stopped"] = {"at": now(), "note": args.note or ""}
    project.state.pop("waiting", None)
    project.save()
    project.log("stopped", note=args.note or "")
    out("The project is marked as stopped. Nothing was deleted. To carry on later, the person says: resume the project.")


def cmd_resume(args):
    project = load_project()
    project.state.pop("stopped", None)
    project.save()
    out(*status_lines(project))


def cmd_check(args):
    project = load_project()
    ok, summary, log_rel = run_check(project, full=args.full)
    if not args.quiet or not ok:
        out(*check_lines(ok, summary, log_rel))
    if not ok:
        raise SystemExit(1)


def canary_target(project, given):
    if given:
        rel = project.rel(project.path(given))
        if not rel or not os.path.isfile(project.path(rel)):
            raise Problem("There is no file '%s' to break." % given)
        return rel
    script = project.phase_info().get("script")
    if script and os.path.isfile(project.path(script)):
        return script
    newest, newest_time = None, 0
    for folder, dirs, files in os.walk(project.root):
        dirs[:] = [d for d in dirs if d not in (".git", ".gs", "vendor", "__pycache__", "node_modules", "checkpoints", "tests")]
        for name in files:
            rel = project.rel(os.path.join(folder, name))
            if rel and project.is_code(rel) and not matches_any(rel, project.protected_globs()):
                modified = os.path.getmtime(os.path.join(folder, name))
                if modified > newest_time:
                    newest, newest_time = rel, modified
    if not newest:
        raise Problem("There is no script yet to break on purpose.")
    return newest


def cmd_canary(args):
    project = load_project()
    ok, summary, log_rel = fresh_check(project)
    if not ok:
        out(*check_lines(ok, summary, log_rel))
        raise Problem("The check has to pass before it can be shown to fail on purpose.")
    rel = canary_target(project, args.file)
    path = project.path(*rel.split("/"))
    with open(path, "rb") as handle:
        original = handle.read()
    stub = b'raise SystemExit("gs canary: this file was broken on purpose")\n' if rel.endswith(".py") else b""
    try:
        with open(path, "wb") as handle:
            handle.write(stub)
        broke_ok, _, broke_log = run_check(project, record=False)
    finally:
        with open(path, "wb") as handle:
            handle.write(original)
    back_ok, summary, back_log = run_check(project)
    proved = (not broke_ok) and back_ok
    project.state["check"]["canary"] = {"ok": proved, "at": now(), "file": rel, "broken_log": broke_log}
    project.save()
    project.log("canary", ok=proved, file=rel)
    if broke_ok:
        raise Problem("The check still passed while %s was broken on purpose, so it cannot fail and proves nothing yet. "
                      "The file is restored." % rel)
    if not back_ok:
        out(*check_lines(back_ok, summary, back_log))
        raise Problem("%s was restored but the check now fails; look at the log." % rel)
    out("Canary proved: with %s broken on purpose the check failed, and with it restored the check passed." % rel)
    out("So this check could have failed, which is what makes its pass worth something.")


def compute_verdict(project):
    reasons = []
    state = project.state
    last = state["check"].get("last") or {}
    check_ok = bool(last.get("ok")) and not project.runtime.get("dirty")
    canary_ok = bool((state["check"].get("canary") or {}).get("ok"))
    problems, tally = lint_verify_report(project)
    if not check_ok:
        reasons.append("the check is not passing on the current files")
    if tally.get("not met"):
        reasons.append("%d acceptance check(s) not met" % tally["not met"])
    if tally.get("spot") == "did not match":
        reasons.append("the person's spot check did not match")
    changed = protected_changes(project)
    tampered = ["the check's own files were changed after setup (%s%s), so a pass proves less"
                % (", ".join(changed[:3]), " and %d more" % (len(changed) - 3) if len(changed) > 3 else "")] if changed else []
    if reasons or problems and not tally:
        return "NOT PROVEN", (reasons or problems[:1]) + tampered
    if not canary_ok:
        reasons.append("no proof that the check can fail")
    if tally.get("not checked"):
        reasons.append("%d acceptance check(s) not checked" % tally["not checked"])
    if tally.get("spot") != "matched":
        reasons.append("no spot check by the person")
    if problems:
        reasons.append(problems[0])
    if not tally.get("met"):
        reasons.append("no acceptance check marked met")
    reasons += tampered
    return ("PARTLY PROVEN", reasons) if reasons else ("PROVEN", ["check passing, canary proved, every acceptance check met, spot check matched"])


def cmd_verdict(args):
    project = load_project()
    word, reasons = compute_verdict(project)
    project.state["verdict"] = {"word": word, "at": now(), "reasons": reasons}
    project.save()
    out("VERDICT: %s" % word)
    out(*["- " + reason for reason in reasons[:6]])


def cmd_change(args):
    project = load_project()
    folder = project.path("docs", "changes")
    os.makedirs(folder, exist_ok=True)
    numbers = [int(m.group(1)) for m in (re.match(r"^(\d+)-", n) for n in os.listdir(folder)) if m]
    number = max(numbers or [0]) + 1
    slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")[:40] or "change"
    rel = "docs/changes/%03d-%s.md" % (number, slug)
    write_text(project.path(*rel.split("/")),
               "# Change %03d: %s\n\nOpened: %s\nStatus: open\n\n## What should change\n\n\n## Why\n\n\n"
               "## How we will know it worked\n\n\n## Decision\n\n" % (number, args.title, now()))
    project.state["open_change"] = rel
    project.save()
    project.log("change_opened", file=rel)
    out("Opened change request %s" % rel)
    out("A change goes through Define first, so that the person approves the changed spec. NEXT: %s" % step("define"))


def cmd_save(args):
    project = load_project()
    git(project, "add", "-A")
    ok, text = git(project, "commit", "-m", args.message)
    if ok:
        _, short = git(project, "log", "-1", "--format=%h")
        out("Saved a version (%s): %s" % (short, args.message))
    elif "nothing to commit" in text:
        out("Nothing has changed since the last saved version.")
    else:
        raise Problem("The version could not be saved: %s" % (text.split("\n")[-1] if text else "git did not answer"))


def cmd_catch_up(args):
    project = load_project()
    if not project.building_unlocked():
        raise Problem("The spec and plan must be approved before reference files are copied in. Next: /gs:help")
    number = int(args.phase or project.state.get("phase", 1))
    source_rel = project.phase_info(number).get("checkpoint")
    if not source_rel or not os.path.isdir(project.path(source_rel)):
        raise Problem("This project has no reference checkpoint for phase %d." % number)
    copied = 0
    for folder, dirs, files in os.walk(project.path(source_rel)):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            rel = os.path.relpath(os.path.join(folder, name), project.path(source_rel))
            destination = project.path(rel)
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copyfile(os.path.join(folder, name), destination)
            copied += 1
    project.runtime["dirty"] = True
    project.save_runtime()
    project.log("catch_up", phase=number, files=copied)
    out("Copied the reference files for phase %d (%d files). This phase now uses the reference, not a fresh build." % (number, copied))
    out("Run the check next.")


def cmd_starters(args):
    folders = starter_folders()
    if not folders:
        out("No starters are installed on this computer. A starter is a ready-made project that comes in a plugin "
            "of its own. A project of the person's own needs none and starts with: init")
        return
    out("Starters installed on this computer:")
    for name in sorted(folders):
        out("- %s: %s" % (name, (read_json(os.path.join(folders[name], "starter.json")) or {}).get("title", "")))
    out("Set one up with: init --starter <name>. For a project of the person's own: init")


def cmd_guide(args):
    folder = os.path.join(plugin_root(), "guides")
    names = sorted(name[:-3] for name in os.listdir(folder) if name.endswith(".md")) if os.path.isdir(folder) else []
    if not args.name:
        out("Guides: %s" % ", ".join(names))
        out("Print one with: guide <name>")
        return
    if args.name not in names:
        raise Problem("There is no guide called '%s'. Guides: %s" % (args.name, ", ".join(names)))
    out('In this guide, GS means the gs command you are running now, with the same words before the command name: '
        '<python> "%s" <command>. Run each GS command by itself.' % os.path.abspath(__file__))
    out("Write everything the person reads in full, short sentences: at most 20 words for an instruction and 25 for a "
        "description, one idea in each, active voice, the same word for the same thing every time, no abbreviations, "
        "idioms or contractions. Explain a technical word in one sentence the first time you use it.")
    out(read_text(os.path.join(folder, args.name + ".md")).replace("${CLAUDE_PLUGIN_ROOT}", plugin_root()))


def cmd_map(args):
    project = load_project(required=False)
    at = STAGES.index(project.state["stage"]) if project else -1
    out("The seven steps, in order%s:" % (" (project: %s)" % project.state.get("project") if project else ""))
    for index, name in enumerate(STAGES):
        mark = "done" if index < at else ("here" if index == at else "    ")
        out("  %s  %-16s %s" % (mark, step(name), STAGE_PURPOSE[name]))
    out("You can type these three commands at any time:")
    out("        /gs:approve      Accept what Claude showed you.")
    out("        /gs:fix          Tell Claude that something is wrong.")
    out("        /gs:help         Find where you are, or ask what a word means.")
    out("You can also ask in your own words, for example: %s." % ASK_IN_WORDS)
    if project:
        out(*status_lines(project)[-2:])
    else:
        out("No project in this folder yet. NEXT: %s" % step("explore"))


def cmd_doctor(args):
    ready = True
    version = "%d.%d.%d" % sys.version_info[:3]
    out("Python: ready (%s)" % version)
    try:
        result = subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
        text = result.stdout.decode("utf-8", "replace").strip()
        out("Git: ready (%s)" % text.replace("git version ", "") if result.returncode == 0 else "Git: not ready")
        ready = ready and result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        out("Git: not ready (the git command was not found)")
        ready = False
    alive = read_json(os.path.join(plugin_data_dir(), "alive.json"))
    project = load_project(required=False)
    seen = [alive.get("at")]
    if project:
        seen += [project.runtime.get("prompt_hook_seen_at"), project.runtime.get("tool_hook_seen_at")]
    latest = min(seen, key=age_seconds)
    if age_seconds(latest) < HOOK_FRESH_S:
        out("Automatic reminders: on (last seen at %s)" % clock(latest))
    else:
        out("Automatic reminders: off on this computer. The guided steps still keep the order and the record.")
    if project:
        need = project.cfg.get("min_python")
        if need and sys.version_info[:2] < tuple(int(x) for x in need.split(".")[:2]) and not os.environ.get("GS_PYTHON"):
            out("Python version: not ready (this project needs %s or later)" % need)
            ready = False
        out("Project: %s, at %s" % (project.state.get("project"), STAGE_TITLES[project.state["stage"]]))
        if project.cfg.get("connectors"):
            out("Connected services this project uses: %s (each is tested by one small read-only call, not by this command)"
                % ", ".join(project.cfg["connectors"]))
    else:
        out("Project: none in this folder yet (begin one with %s)" % step("explore"))
    out("SETUP: READY" if ready else "SETUP: NOT READY")
    if not ready:
        raise SystemExit(1)


# -------------------------------------------------------------------- hooks

def hook_input():
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (ValueError, OSError):
        return {}


def hook_project(data):
    for start in (data.get("cwd"), os.environ.get("CLAUDE_PROJECT_DIR"), os.getcwd()):
        if start and os.path.isdir(start):
            root = find_root(start)
            if root:
                return Project(root)
    return None


def emit(payload):
    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()


def reminder(project, short=False):
    lines = status_lines(project)
    last = project.state["check"].get("last") or {}
    failing = bool(last) and not last.get("ok")
    if short:
        parts = lines[1:2] + lines[-1:]
        if failing:
            parts.insert(1, "the last check FAILED, so the current step is not done yet")
        return "gs: " + " | ".join(parts)
    order = ", ".join("%d %s" % (index + 1, STAGE_TITLES[name]) for index, name in enumerate(STAGES))
    rules = ("This folder is a gs project. The agreed order is: %s. Code is written after the person has approved the "
             "spec and the plan; only the person approves a gate, by typing /gs:approve; a step is done when its check "
             "passes. These are the working agreement, not locks: if the person asks to go another way, say in one "
             "sentence what is being skipped, then do as they ask. "
             "If the person asks for a change while a phase or the result is waiting for their decision, run the gs "
             "'revise' command first; if they say to stop the project, run the gs 'stop' command; to carry on a stopped "
             "project, the gs 'resume' command. If the person does not follow something, say it again in three plain "
             "sentences with an example from their own project. "
             "The person is not a programmer: you run every command yourself, and they never open a terminal or read "
             "code. Read and list files with the built-in file tools rather than shell commands, because every new shell "
             "command asks the person for permission. "
             "Write to the person in full, short sentences: at most 20 words for an instruction and 25 for a "
             "description, one idea in each, active voice, the same word for the same thing every time, and no "
             "abbreviations, idioms or contractions. Explain a technical word in one sentence the first time you use it. "
             "Report in two sentences and end on the one next command." % order)
    runner = LAUNCHER or '"%s"' % python_command()
    how = ('A gs command is run as: %s "%s" <command> (for example status, check, revise, stop), each by itself. '
           'Extra guides are printed by the command: guide <name>, for %s; use one when the person asks for that thing.'
           % (runner, os.path.abspath(__file__), ", ".join(GUIDES)))
    return "gs project status\n" + "\n".join(lines) + "\n" + rules + "\n" + how


def hook_session_start(data):
    try:
        write_json(os.path.join(plugin_data_dir(), "alive.json"),
                   {"at": now(), "session_id": data.get("session_id"), "python": sys.executable})
    except OSError:
        pass
    project = hook_project(data)
    if project:
        emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": reminder(project)}})


def hook_user_prompt(data):
    project = hook_project(data)
    if not project:
        return
    prompt = (data.get("prompt") or "").strip()
    project.runtime["prompt_hook_seen_at"] = now()
    project.runtime["advised"] = []
    project.save_runtime()
    match = re.match(r"^/gs:approve\b(.*)$|^approved?[.!]?$", prompt, re.IGNORECASE | re.DOTALL)
    if match and project.waiting():
        gate = gate_label(project.waiting())
        try:
            lines = approve_gate(project, (match.group(1) or "").strip(), typed_by_person=True)
            context = ("gs: the person typed their approval of %s and it is now recorded. %s Do not run the approve "
                       "command again. Tell the person in one sentence, then give the one next command."
                       % (gate, " ".join(lines)))
        except Problem as problem:
            context = ("gs: the person typed an approval of %s, but it could not be recorded: %s "
                       "Tell the person why in one sentence and what to do next." % (gate, problem))
    elif prompt.lower().startswith("/gs:"):
        context = reminder(project)
    else:
        context = reminder(project, short=True)
    emit({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}})


def edited_path(data):
    tool_input = data.get("tool_input") or {}
    return tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path")


def advise(project, event, key, for_claude, for_person=None):
    """Hooks never refuse anything. They tell Claude, and once per turn the person, what is out of order."""
    told = project.runtime.setdefault("advised", [])
    payload = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": "gs advice: " + for_claude}}
    if for_person and key not in told:
        payload["systemMessage"] = "gs heads-up: " + for_person
        told.append(key)
    project.save_runtime()
    emit(payload)


def hook_pre_tool(data):
    project = hook_project(data)
    file_path = edited_path(data)
    if not project or not file_path:
        return
    if not os.path.isabs(file_path):
        file_path = os.path.join(data.get("cwd") or project.root, file_path)
    rel = project.rel(file_path)
    if not rel:
        return
    project.runtime["tool_hook_seen_at"] = now()
    project.save_runtime()
    project.reopen_changed_gates()
    if matches_any(rel, project.protected_globs()):
        if rel.startswith(".gs/"):
            return advise(project, "PreToolUse", "record",
                          "%s is the project's own record of approvals and checks. It is normally changed only by the "
                          "gs commands (status, done, approve), so that the record stays true. If the person did not "
                          "ask for this edit, leave the file as it is." % rel,
                          "Claude is changing %s by hand. This file is the record of your approvals. Ask Claude why."
                          % rel)
        return advise(project, "PreToolUse", "answer-key",
                      "%s is part of the answer key or the check itself. A check that has been changed proves less, "
                      "and the verdict will name the changed file. If the person did not ask for exactly this, leave "
                      "it as it is: a new test goes in a new file under tests/, or the script is fixed instead." % rel,
                      "Claude is changing %s. This file is part of the automatic check, so the change makes the "
                      "check weaker. The final verdict will name this file." % rel)
    if not project.is_code(rel):
        return
    if not project.building_unlocked():
        missing = "spec" if not project.approved("spec") else "design and plan"
        back = step("define") if missing == "spec" else step("design")
        return advise(project, "PreToolUse", "early-code",
                      "the %s has not been approved by the person yet, and the agreed order is spec, then plan, then "
                      "code. Writing %s now is building before the decision. If the person has not asked for exactly "
                      "this, the helpful move is to stop, say where things stand, and give the next command (%s). "
                      "A throwaway under prototype/ is fine at any time." % (missing, rel, back),
                      "Claude is writing code (%s) before you approved the %s. The usual next step is %s."
                      % (rel, missing, back))
    waiting = project.waiting()
    if waiting and (waiting.startswith("phase:") or waiting == "result"):
        return advise(project, "PreToolUse", "waiting",
                      "the person has not yet decided on %s, so the code is expected to stay as shown to them. If they "
                      "asked for a change, the gs 'revise' command records that first; if they accepted, they type "
                      "/gs:approve." % gate_label(waiting),
                      "Claude is changing code while %s waits for your decision." % gate_label(waiting))


def capture_answer(project, data):
    """Save a connector answer exactly as returned, when the project's starter asks for that tool's answers.

    Copying a long answer by hand is slow and can change it, so the copy is made here, by code.
    Nothing is saved outside a project whose starter names the tool."""
    name = str(data.get("tool_name") or "").rsplit("__", 1)[-1]
    folder = project.cfg.get("capture_dir")
    if not folder or name not in (project.cfg.get("capture_tools") or []):
        return False
    answer = data.get("tool_response")
    if isinstance(answer, list):
        texts = [part.get("text") for part in answer if isinstance(part, dict) and part.get("type") == "text"]
        if len(texts) == 1:
            answer = texts[0]
    if isinstance(answer, str):
        try:
            answer = json.loads(answer)
        except ValueError:
            pass
    target = project.path(*folder.split("/"))
    os.makedirs(target, exist_ok=True)
    numbers = [int(item.split("-", 1)[0]) for item in os.listdir(target) if item.split("-", 1)[0].isdigit()]
    file_name = "%03d-%s.json" % (max(numbers or [0]) + 1, name)
    write_json(os.path.join(target, file_name),
               {"schema": "gs-answer/1", "tool": name, "input": data.get("tool_input") or {}, "answer": answer})
    emit({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
          "gs saved this %s answer exactly as returned, to %s/%s. It does not need to be copied or typed out again: "
          "the project's fetch tool builds the data files from the saved answers." % (name, folder, file_name)}})
    return True


def hook_post_tool(data):
    project = hook_project(data)
    if project and str(data.get("tool_name") or "").startswith("mcp__"):
        capture_answer(project, data)
        return
    file_path = edited_path(data)
    if not project or not file_path:
        return
    if not os.path.isabs(file_path):
        file_path = os.path.join(data.get("cwd") or project.root, file_path)
    rel = project.rel(file_path)
    if rel and project.is_code(rel):
        project.runtime["dirty"] = True
        project.save_runtime()


def hook_stop(data):
    """Runs the check when code changed, records the result, and tells the person if it fails. Never holds the turn."""
    project = hook_project(data)
    if not project or not project.runtime.get("dirty"):
        return
    if STAGES.index(project.state["stage"]) < STAGES.index("implement") or not project.building_unlocked():
        return
    if not check_command(project):
        return
    ok, summary, log_rel = run_check(project)
    if ok:
        return
    emit({"systemMessage": "gs heads-up: The automatic check fails on the files as they are now. This step is not "
                           "done yet. Tell Claude to continue, or type /gs:fix. The details are in %s." % log_rel})


HOOKS = {
    "session-start": hook_session_start,
    "user-prompt": hook_user_prompt,
    "pre-tool": hook_pre_tool,
    "post-tool": hook_post_tool,
    "stop": hook_stop,
}


def cmd_hook(args):
    """Hooks never break a session: any failure is logged and swallowed."""
    global LAUNCHER
    LAUNCHER = args.via if args.via in ("python", "python3", "py") else ""
    try:
        data = hook_input()
        if os.environ.get("GS_HOOK_DEBUG"):
            os.makedirs(plugin_data_dir(), exist_ok=True)
            with open(os.path.join(plugin_data_dir(), "hook-debug.jsonl"), "a", encoding="utf-8") as handle:
                handle.write(json.dumps({"at": now(), "event": args.event, "data": data}) + "\n")
        HOOKS[args.event](data)
    except SystemExit:
        raise
    except BaseException as error:  # noqa: B902 - a hook must not crash the session
        try:
            folder = plugin_data_dir()
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, "hook-errors.log"), "a", encoding="utf-8") as handle:
                handle.write("%s %s %r\n" % (now(), args.event, error))
        except OSError:
            pass
    raise SystemExit(0)


# --------------------------------------------------------------------- main

def build_parser():
    parser = argparse.ArgumentParser(prog="gs", description="State, gates and checks for a gs project.")
    sub = parser.add_subparsers(dest="command")
    sub.required = True
    p = sub.add_parser("init"); p.add_argument("--starter"); p.add_argument("--name"); p.set_defaults(func=cmd_init)
    p = sub.add_parser("status"); p.set_defaults(func=cmd_status)
    p = sub.add_parser("lint"); p.add_argument("what", choices=["spec", "plan"]); p.set_defaults(func=cmd_lint)
    p = sub.add_parser("done"); p.add_argument("stage", choices=STAGES + ["phase"]); p.set_defaults(func=cmd_done)
    p = sub.add_parser("approve"); p.add_argument("--note", default=""); p.set_defaults(func=cmd_approve)
    p = sub.add_parser("revise"); p.add_argument("--note", default=""); p.set_defaults(func=cmd_revise)
    p = sub.add_parser("stop"); p.add_argument("--note", default=""); p.set_defaults(func=cmd_stop)
    p = sub.add_parser("resume"); p.set_defaults(func=cmd_resume)
    p = sub.add_parser("check"); p.add_argument("--full", action="store_true"); p.add_argument("--quiet", action="store_true"); p.set_defaults(func=cmd_check)
    p = sub.add_parser("canary"); p.add_argument("file", nargs="?"); p.set_defaults(func=cmd_canary)
    p = sub.add_parser("verdict"); p.set_defaults(func=cmd_verdict)
    p = sub.add_parser("change"); p.add_argument("action", choices=["new"]); p.add_argument("title"); p.set_defaults(func=cmd_change)
    p = sub.add_parser("save"); p.add_argument("message"); p.set_defaults(func=cmd_save)
    p = sub.add_parser("catch-up"); p.add_argument("phase", nargs="?"); p.set_defaults(func=cmd_catch_up)
    p = sub.add_parser("doctor"); p.set_defaults(func=cmd_doctor)
    p = sub.add_parser("guide"); p.add_argument("name", nargs="?"); p.set_defaults(func=cmd_guide)
    p = sub.add_parser("map"); p.set_defaults(func=cmd_map)
    p = sub.add_parser("starters"); p.set_defaults(func=cmd_starters)
    p = sub.add_parser("hook"); p.add_argument("event", choices=sorted(HOOKS)); p.add_argument("--via", default=""); p.set_defaults(func=cmd_hook)
    return parser


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except Problem as problem:
        out(str(problem))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
