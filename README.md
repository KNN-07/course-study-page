# course-study-page

An agent skill that scans a folder of course materials and builds one interactive study page
from it. The page teaches the Socratic way: it asks before it tells, answers a wrong choice
with a narrower question, and only raises a level after clean, repeated, spaced performance.

The teaching rules are adapted from Jane Street's
[socratic-tutor](https://github.com/janestreet/agent_skills/blob/master/socratic-tutor/SKILL.md)
skill (MIT): diagnostic placement, a skill map with levels 0-5, one question at a time,
strict evaluation, spaced review, no flattery, and a final mixed assessment. That skill
tutors in conversation. This one bakes the same method into a page the student keeps.

## What you get

`study.html`, a single file that opens in any browser:

- course overview with a skill map and a "do this next" card
- a diagnostic that places each module before anything is taught
- module pages you can actually learn from: predict-first primer, summary, a full lesson in
  sections with worked examples and check-yourself questions, key ideas (with a
  hide-definitions self-test), reference tables, pitfalls
- practice, one item at a time: quiz with per-option probes, short answer, flashcards,
  step-by-step worked problems, teach-back against a rubric
- a spaced review queue across modules
- a final assessment that unlocks when every module is at target, plus a mock
- cheat sheet, progress view, save and restore codes, and a hand-off block for live tutoring
- answer options shuffled on every showing, so positions cannot be memorised
- an exam date that compresses the review schedule and sets a daily target
- diagrams from your slides embedded in the page
- a source line on every question, a flag button, and a list of course files the page does
  not cover
- ready-made requests to paste back to your agent: more questions on weak modules, a check
  of flagged questions, and strict marking of a written answer
- search, personal notes, keyboard shortcuts, backup download and Anki export

See `course-study-page/examples/study.example.html` for a built example.

## Install

The skill follows the open Agent Skills layout (`SKILL.md` plus `scripts/`, `references/`,
`assets/`), so any agent that loads skills can use it.

```bash
python install.py --agent claude
```

| Agent | `--agent` | User-wide folder | Project folder |
|---|---|---|---|
| Claude Code | `claude` | `~/.claude/skills` | `.claude/skills` |
| Codex | `codex` | `~/.codex/skills` | `.agents/skills` |
| OpenCode | `opencode` | `~/.config/opencode/skills` | `.opencode/skills` |
| Antigravity | `antigravity` | `~/.gemini/antigravity/skills` | `.agent/skills` |
| Gemini CLI | `gemini` | `~/.gemini/skills` | `.gemini/skills` |
| Cursor | `cursor` | `~/.cursor/skills` | `.cursor/skills` |
| Generic | `agents` | `~/.agents/skills` | `.agents/skills` |

Add `--scope project` to install into the current project, or `--dest <dir>` for any other
location. These folders have moved between agent versions, so if the skill does not show up,
check your agent's documentation and use `--dest`. You can also copy the
`course-study-page` folder by hand.

Requirements: Python 3.8+. No packages are needed. `pip install pypdf` improves PDF
extraction.

## Use

Open your agent in (or point it at) the course folder and ask:

> Build a study page from this course folder.

The agent scans the folder, reads the materials, writes `course.json`, validates it and
builds `study.html`. You can also run the steps yourself:

```bash
python course-study-page/scripts/scan_materials.py path/to/course
```

```bash
python course-study-page/scripts/validate_course.py path/to/course/course.json
```

```bash
python course-study-page/scripts/build_page.py path/to/course/course.json
```

## Layout

```
course-study-page/
  SKILL.md                       workflow the agent follows
  scripts/scan_materials.py      inventory + text extraction (pdf, pptx, docx, xlsx, ipynb, md, code, ...)
  scripts/validate_course.py     schema and question-quality checks
  scripts/build_page.py          course.json + template -> study.html
  assets/template.html           the page: layout, mastery model, review scheduling
  references/schema.md           every field of course.json
  references/question-craft.md   how to write Socratic items and probes
  references/mastery-model.md    credit, levels, review intervals, final assessment
  examples/course.example.json   a complete small course
install.py                       copies the skill into an agent's skills folder
```

## Licence

MIT.
