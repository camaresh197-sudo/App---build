#!/usr/bin/env python3
"""Session checklist checker for Wren/Greg (docs/AGENT_PROTOCOL.md).

Checks the parts of the end-of-session checklist a script can see. It cannot judge
whether a finding is real or a review is honest; it only checks that the pieces exist.

  python3 tools/session_check.py                 # full end-of-session check for your agent
  python3 tools/session_check.py --set-agent greg # once per session: record who is running
  python3 tools/session_check.py --agent greg    # force one agent (default: auto)
  python3 tools/session_check.py --bank-only     # mid-session: bank has a record dated today
  python3 tools/session_check.py --hook          # Stop hook (reads JSON on stdin); same for both agents

Agent resolution (default --agent auto): $AGENT env, then .claude/.agent (written by
--set-agent, gitignored), then wren. So both agents and the hook run the same command.

Exit 0 = pass, 1 = fail. In --hook mode a failure prints {"decision":"block",...} and exits 0.
Hook rules: a reply containing a line starting "Found:" needs a bank record dated today;
a last user message that ends the session (end session, write the handoff, goodbye...) needs the full checklist.
Dates use America/New_York (the user's zone); override with --date YYYY-MM-DD.
"""
import argparse, json, os, re, subprocess, sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANKS = {"wren": "docs/findings/WREN.md", "greg": "docs/FINDINGS.md"}
END_RE = re.compile(r"end (the |this )?session|session (is )?(over|done|ending)|write (to )?(the )?hand ?off|wrap (it )?up|goodbye|good night", re.I)


def today(override=None):
    if override:
        return override
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


def read(rel):
    try:
        return open(os.path.join(ROOT, rel), encoding="utf-8").read()
    except OSError:
        return ""


def git(*a):
    try:
        return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=30).stdout.strip()
    except Exception:
        return ""


def log_entries(handoff, name):
    """Log entries signed by `name`, newest first: (version, date, text)."""
    out = []
    in_log = False
    cur = None
    for line in handoff.splitlines():
        if line.startswith("## Log"):
            in_log = True
            continue
        if in_log and line.startswith("## "):
            break
        if not in_log:
            continue
        if line.startswith("- **"):
            if cur:
                out.append(cur)
            m = re.match(r"- \*\*" + name + r" v(\d+) .*?\), (\d{4}-\d\d-\d\d)", line, re.I)
            cur = {"v": int(m.group(1)), "date": m.group(2), "text": line} if m else None
        elif cur is not None:
            cur["text"] += "\n" + line
    if cur:
        out.append(cur)
    return out


CACHE = os.path.join(ROOT, ".claude", ".session_version")
AGENT_FILE = os.path.join(ROOT, ".claude", ".agent")


def resolve_agent(arg):
    """auto -> $AGENT, then .claude/.agent, then wren."""
    if arg in BANKS:
        return arg
    env = os.environ.get("AGENT", "").strip().lower()
    if env in BANKS:
        return env
    try:
        with open(AGENT_FILE, encoding="utf-8") as f:
            who = f.read().strip().lower()
        if who in BANKS:
            return who
    except OSError:
        pass
    return "wren"


def set_agent(who):
    os.makedirs(os.path.dirname(AGENT_FILE), exist_ok=True)
    with open(AGENT_FILE, "w", encoding="utf-8") as f:
        f.write(who + "\n")
    print("agent marker: %s (%s)" % (who, BANKS[who]))


def session_version(entries, date, session_id):
    """This session's number. Cached per session so writing the Log entry does not bump it:
    first look in a session starts at highest+1 and is remembered (.claude/.session_version, gitignored)."""
    try:
        c = json.load(open(CACHE))
    except (OSError, ValueError):
        c = {}
    fresh = (session_id and c.get("session") == session_id) or (not session_id and c.get("date") == date)
    if fresh and isinstance(c.get("version"), int):
        return c["version"]
    v = (max(e["v"] for e in entries) + 1) if entries else 1
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        json.dump({"session": session_id, "date": date, "version": v}, open(CACHE, "w"))
    except OSError:
        pass
    return v


def bank_records(bank_text):
    recs = []
    for line in bank_text.splitlines():
        m = re.match(r"^[WS](\d{3})\|(\d{4}-\d\d-\d\d)\|", line)
        if m:
            recs.append((int(m.group(1)), m.group(2)))
    return recs


def check_bank(agent, date, res):
    bank = BANKS[agent]
    recs = bank_records(read(bank))
    ids = [r[0] for r in recs]
    res.append(("Findings bank has a record dated %s (%s)" % (date, bank),
                any(d == date for _, d in recs),
                "write one now (next id W%03d); one dense record per major finding, never delete" % ((max(ids) if ids else 0) + 1)))
    res.append(("Findings bank ids unique and ascending", ids == sorted(set(ids)), "fix duplicate or out-of-order ids"))


def check_full(agent, date, version, res, session_id=None):
    name = agent.capitalize()
    handoff = read("HANDOFF.md")
    entries = log_entries(handoff, name)
    if version is None:
        version = session_version(entries, date, session_id)
    res.append(("Version this session: %s v%d" % (name, version), True, ""))
    mine = [e for e in entries if e["v"] == version]
    res.append(("1. HANDOFF.md Log entry signed '%s v%d', dated %s" % (name, version, date),
                bool(mine) and mine[0]["date"] == date, "add the entry (newest first, max 10 lines) with the date"))
    if mine:
        t = mine[0]["text"]
        m = re.search(r"\*\*Complaints:\*\*(.*?)(\*\*Review of the user:\*\*|\Z)", t, re.S)
        items = re.findall(r"\((\d)\)\s*(.+?)(?=\s*\(\d\)\s|\Z)", re.sub(r"\s+", " ", m.group(1)).strip()) if m else []
        res.append(("1. Log entry has exactly three complaints", len(items) == 3, "end the entry with (1) (2) (3) complaints"))
        bad = [i for i, c in items if not 10 <= len(c.split()) <= 15]
        res.append(("1. Each complaint is 10-15 words (rule in AGENT_PROTOCOL.md)", not bad,
                    "complaint(s) %s outside 10-15 words" % ",".join(bad)))
        res.append(("1. Log entry ends with 'Review of the user:'", "**Review of the user:**" in t, "add the review line"))
    p = read("PERSONALITIES.md")
    res.append(("2. PERSONALITIES.md has an 'As of %s (%s v%d' section" % (date, name, version),
                ("As of %s (%s v%d" % (date, name, version)) in p, "add your dated habits/strengths/rule section"))
    res.append(("2. PERSONALITIES.md Progress log row for %s v%d" % (name, version),
                re.search(r"^\| %s \| %s v%d \|" % (date, name, version), p, re.M) is not None, "add one Progress log row"))
    res.append(("2. Sliders heading names %s v%d" % (name, version),
                re.search(r"^### %s's sliders.*%s v%d" % (name, name, version), p, re.M) is not None,
                "update your sliders table and its heading"))
    res.append(("2. Coaching notes updated this session",
                re.search(r"%s v%d coaching|coaching notes.*%s v%d" % (name, version, name, version), p, re.I | re.S) is not None,
                "update coaching notes (max 3) and mention the version"))
    check_bank(agent, date, res)
    claimed = re.search(r"## Claimed\n\|.*\n\|.*\n((?:\|.*\n?)*)", handoff)
    rows = [l for l in (claimed.group(1).splitlines() if claimed else []) if name.lower() in l.lower()]
    res.append(("Claimed table has no %s row left" % name, not rows, "remove your Claimed row once pushed"))
    dirty = [l for l in git("status", "--porcelain").splitlines() if l.strip() and not l.startswith("??")]
    res.append(("4. No uncommitted tracked changes", not dirty, "commit: %s" % "; ".join(dirty[:3])))
    ahead = git("rev-list", "--count", "origin/godot..HEAD")
    res.append(("4. Nothing unpushed on this branch vs origin/godot", ahead in ("", "0") or ahead == "0",
                "%s commit(s) unpushed" % ahead))
    trailer = "%s-Version: %d" % (name, version)
    res.append(("4. A recent commit carries '%s'" % trailer, trailer in git("log", "-15", "--format=%B"), "add the trailer to your commit"))


def manual(agent):
    return [
        "Not checkable by script, do and say them: sheet tabs updated (%s sliders, %s change log), step 3 lessons, step 5 run id or 'no build triggered',"
        % (agent.capitalize(), agent.capitalize()),
        "step 6 chat post (goodbye, review, three complaints, user review, sliders table, csv attached), step 7 name what is not saved.",
    ]


def report(res, agent, as_text=True):
    fails = [r for r in res if not r[1]]
    lines = ["[%s] %s%s" % ("ok" if ok else "FAIL", label, "" if ok else "  -> " + hint) for label, ok, hint in res]
    return fails, "\n".join(lines)


def last_texts(path):
    """(last user text, last assistant text) from a Claude Code transcript jsonl; ('','') if unreadable."""
    user = asst = ""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                msg = o.get("message") or {}
                role = msg.get("role") or o.get("type")
                c = msg.get("content")
                if isinstance(c, list):
                    c = " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
                if not isinstance(c, str) or not c.strip():
                    continue
                if role == "user" and not c.lstrip().startswith("<"):
                    user = c
                elif role == "assistant":
                    asst = c
    except OSError:
        pass
    return user, asst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="auto", choices=["auto", "wren", "greg"])
    ap.add_argument("--set-agent", choices=["wren", "greg"])
    ap.add_argument("--version", type=int)
    ap.add_argument("--date")
    ap.add_argument("--bank-only", action="store_true")
    ap.add_argument("--hook", action="store_true")
    a = ap.parse_args()
    if a.set_agent:
        set_agent(a.set_agent)
        return 0
    agent = resolve_agent(a.agent)
    date = today(a.date)
    res = []

    if a.hook:
        try:
            data = json.load(sys.stdin)
        except ValueError:
            data = {}
        if data.get("stop_hook_active"):
            return 0
        user, asst = last_texts(data.get("transcript_path", ""))
        if re.search(r"^\s*\**Found\**:", asst, re.M):
            check_bank(agent, date, res)
        if END_RE.search(user):
            check_full(agent, date, a.version, res, data.get("session_id"))
        fails, text = report(res, agent)
        if fails:
            print(json.dumps({"decision": "block", "reason":
                              "Session checklist (tools/session_check.py) failed. Fix these, then finish:\n" + text + "\n" + "\n".join(manual(agent))}))
        return 0

    if a.bank_only:
        check_bank(agent, date, res)
    else:
        check_full(agent, date, a.version, res)
    fails, text = report(res, agent)
    print(text)
    if not a.bank_only:
        print("\n" + "\n".join(manual(agent)))
    print("\n%d check(s) failed." % len(fails) if fails else "\nAll scripted checks passed.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
