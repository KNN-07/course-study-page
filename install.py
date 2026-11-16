#!/usr/bin/env python3
"""Copy the course-study-page skill into an agent's skills folder.

  python install.py --agent claude                 # user-wide, for Claude Code
  python install.py --agent codex --scope project  # into the current project
  python install.py --agent all                    # every known user-wide location
  python install.py --dest /some/skills/dir        # anywhere else

Skill folder locations change between agent versions. If your agent does not
pick the skill up, check its documentation and use --dest.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL = "course-study-page"
HOME = Path.home()
# agent: (user-wide skills dir, project-relative skills dir)
TARGETS = {
    "claude": (HOME / ".claude" / "skills", Path(".claude") / "skills"),
    "codex": (HOME / ".codex" / "skills", Path(".agents") / "skills"),
    "opencode": (HOME / ".config" / "opencode" / "skills", Path(".opencode") / "skills"),
    "antigravity": (HOME / ".gemini" / "antigravity" / "skills", Path(".agent") / "skills"),
    "gemini": (HOME / ".gemini" / "skills", Path(".gemini") / "skills"),
    "cursor": (HOME / ".cursor" / "skills", Path(".cursor") / "skills"),
    "agents": (HOME / ".agents" / "skills", Path(".agents") / "skills"),
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Install the course-study-page skill.")
    ap.add_argument("--agent", choices=sorted(TARGETS) + ["all"], help="which agent to install for")
    ap.add_argument("--scope", choices=["user", "project"], default="user")
    ap.add_argument("--project", default=".", help="project folder for --scope project")
    ap.add_argument("--dest", help="explicit skills directory (overrides --agent)")
    args = ap.parse_args()
    src = Path(__file__).resolve().parent / SKILL
    if not (src / "SKILL.md").is_file():
        print(f"error: {src} does not contain SKILL.md", file=sys.stderr)
        return 2
    if args.dest:
        dests = [Path(args.dest).expanduser()]
    elif args.agent:
        names = sorted(TARGETS) if args.agent == "all" else [args.agent]
        idx = 0 if args.scope == "user" else 1
        base = Path(args.project).expanduser().resolve() if args.scope == "project" else Path()
        dests = list(dict.fromkeys(base / TARGETS[n][idx] for n in names))
    else:
        ap.error("give --agent or --dest")
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "study.example.html")
    for d in dests:
        target = d / SKILL
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src, target, ignore=ignore)
        print(f"installed -> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
