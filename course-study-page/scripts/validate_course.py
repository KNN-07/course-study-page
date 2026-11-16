#!/usr/bin/env python3
"""Check a course.json against the schema and the question-quality rules.

Usage:  python validate_course.py <course.json> [--manifest .study/manifest.json] [--json] [--strict]

Errors block the build. Warnings point at weak pedagogy (too much recall, no
probes, a module nobody can reach level 5 in) and should be fixed or consciously
accepted. --strict turns warnings into a failing exit code.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

KINDS = {"predict", "explain", "flaw", "apply", "connect", "recall"}
ITEM_LISTS = ("diagnostic", "flashcards", "quiz", "fill", "worked", "explain", "integrative")
PLACEHOLDER = re.compile(r"lorem ipsum|\bTODO\b|\bTBD\b|\bFIXME\b|\bxxx\b", re.I)


def _s(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


FIG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
COVER_ROLES = {"lecture", "notes", "reading", "assignment", "exam"}


def iter_figures(node, path="course"):
    """Yield (location, figure dict) for every `figure` object and `figures` list in the data."""
    if isinstance(node, dict):
        for k, v in node.items():
            here = f"{path}.{k}"
            if k == "figure" and isinstance(v, dict):
                yield here, v
            elif k == "figures" and isinstance(v, list):
                for i, f in enumerate(v):
                    if isinstance(f, dict):
                        yield f"{here}[{i}]", f
            else:
                yield from iter_figures(v, here)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from iter_figures(v, f"{path}[{i}]")


def coverage(data, manifest):
    """Course files of a teaching role that no module source and no item src mentions."""
    if not manifest:
        return []
    cited = []
    for m in data.get("modules") or []:
        if isinstance(m, dict):
            cited.append(str(m.get("source") or ""))
    for lst in ITEM_LISTS:
        for it in data.get(lst) or []:
            if isinstance(it, dict):
                cited.append(str(it.get("src") or ""))
    blob = " ".join(cited).lower()
    out = []
    for f in manifest.get("files", []):
        if f.get("role") not in COVER_ROLES or not (f.get("extracted") or f.get("status") == "needs_native_read"):
            continue
        name = Path(f["path"]).name.lower()
        stem = Path(name).stem
        if name not in blob and not (len(stem) > 2 and stem in blob):
            out.append(f["path"])
    return out


def validate(data, manifest=None, base=None):
    errors, warnings = [], []
    E, W = errors.append, warnings.append
    if not isinstance(data, dict):
        return ["top level must be a JSON object"], [], {}

    for loc, f in iter_figures(data):
        src = f.get("src")
        if not _s(src):
            E(f"{loc}.src: required")
            continue
        if not _s(f.get("alt")):
            E(f"{loc}.alt: describe the picture for students who cannot see it")
        if src.startswith(("data:image/", "https://")):
            continue
        if Path(src).suffix.lower() not in FIG_EXT:
            E(f"{loc}.src: '{src}' is not a png, jpg, gif, webp or svg")
        elif base is not None and not (Path(base) / src).is_file():
            E(f"{loc}.src: file not found: {src} (paths are relative to course.json)")

    course = data.get("course")
    if not isinstance(course, dict):
        E("course: missing object")
        course = {}
    if not _s(course.get("title")):
        E("course.title: required")
    if not _s(course.get("overview")):
        W("course.overview: missing")
    if len(course.get("objectives") or []) < 2:
        W("course.objectives: give at least 2 things the student should be able to do")
    tl = course.get("target_level", 4)
    if not isinstance(tl, int) or not 1 <= tl <= 5:
        E("course.target_level: must be an integer 1-5 (default 4)")
    if course.get("exam_date") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(course["exam_date"])):
        E("course.exam_date: must be YYYY-MM-DD (omit it if unknown; the student can set it on the page)")
    if course.get("accent") and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(course["accent"])):
        E("course.accent: must be a #RRGGBB colour")

    modules = data.get("modules")
    if not isinstance(modules, list) or not modules:
        E("modules: need a non-empty list")
        modules = []
    n = len(modules)
    if n and not 4 <= n <= 10:
        W(f"modules: {n} modules. Aim for 4-10 concrete subskills (fewer only for a narrow topic)")
    for i, m in enumerate(modules):
        p = f"modules[{i}]"
        if not isinstance(m, dict):
            E(f"{p}: must be an object")
            continue
        if not _s(m.get("title")):
            E(f"{p}.title: required")
        if not _s(m.get("summary")):
            E(f"{p}.summary: required")
        if _s(m.get("short")) and len(m["short"]) > 22:
            W(f"{p}.short: '{m['short']}' is long for a tag. Keep it under 22 characters")
        if not _s(m.get("source")):
            W(f"{p}.source: say which file(s) and pages or slides this module came from")
        pr = m.get("primer")
        if not (isinstance(pr, dict) and _s(pr.get("q")) and _s(pr.get("a"))):
            W(f"{p}.primer: add a predict-first question {{q, a}} shown before the summary")
        reading = m.get("reading")
        if reading is not None and not isinstance(reading, list):
            E(f"{p}.reading: must be a list of sections {{heading, body}}")
            reading = []
        rwords = 0
        for j, sec in enumerate(reading or []):
            if not (isinstance(sec, dict) and _s(sec.get("body"))):
                E(f"{p}.reading[{j}].body: required")
                continue
            rwords += len(sec["body"].split())
            ck = sec.get("check")
            if ck is not None and not (isinstance(ck, dict) and _s(ck.get("q")) and _s(ck.get("a"))):
                E(f"{p}.reading[{j}].check: needs q and a")
        if not reading:
            W(f"{p}.reading: no lesson. The module page should be something to learn from, not only key-idea cards")
        elif rwords < 250:
            W(f"{p}.reading: {rwords} words. A lesson usually needs 400-1200 to explain the module properly")
        elif not any(isinstance(sec, dict) and sec.get("check") for sec in reading):
            W(f"{p}.reading: no section has a 'check' question. Add one or two so the reading is not passive")
        cons = m.get("concepts") or []
        if len(cons) < 2:
            W(f"{p}.concepts: fewer than 2 key ideas")
        for j, c in enumerate(cons):
            if not (isinstance(c, dict) and _s(c.get("term")) and _s(c.get("def"))):
                E(f"{p}.concepts[{j}]: needs term and def")
        tables = list(m.get("tables") or []) + ([m["table"]] if m.get("table") else [])
        for j, t in enumerate(tables):
            heads = (t or {}).get("headers") or []
            if not heads:
                E(f"{p} table {j}: headers required")
            for r, row in enumerate((t or {}).get("rows") or []):
                if not isinstance(row, list) or len(row) != len(heads):
                    E(f"{p} table {j} row {r}: has {len(row) if isinstance(row, list) else '?'} cells, expected {len(heads)}")
        if not m.get("pitfalls"):
            W(f"{p}.pitfalls: list at least one common mistake")
        if len(m.get("sheet") or []) < 2:
            W(f"{p}.sheet: fewer than 2 cheat-sheet lines")
        for j, x in enumerate(m.get("sheet") or []):
            if not (isinstance(x, dict) and _s(x.get("k")) and _s(x.get("v"))):
                E(f"{p}.sheet[{j}]: needs k and v")
        if manifest and _s(m.get("source")):
            names = [Path(f["path"]).name.lower() for f in manifest.get("files", [])]
            stems = [Path(x).stem for x in names]
            src = m["source"].lower()
            if not any(nm in src or st in src for nm, st in zip(names, stems) if len(st) > 2):
                W(f"{p}.source: '{m['source']}' names no file from the scan manifest")

    seen_ids, seen_text = {}, {}
    per_mod = {i: Counter() for i in range(n)}
    hard = Counter()

    def common(lst, idx, it, needs_m=True):
        p = f"{lst}[{idx}]"
        if not isinstance(it, dict):
            E(f"{p}: must be an object")
            return None
        if "id" in it:
            if not _s(it["id"]):
                E(f"{p}.id: must be a non-empty string when given")
            elif it["id"] in seen_ids:
                E(f"{p}.id: duplicate of {seen_ids[it['id']]}")
            else:
                seen_ids[it["id"]] = p
        if needs_m:
            mi = it.get("m")
            if not isinstance(mi, int) or isinstance(mi, bool) or not 0 <= mi < n:
                E(f"{p}.m: must be a module index 0-{max(0, n - 1)}")
                return None
            per_mod[mi][lst] += 1
        d = it.get("difficulty")
        if d is not None and d not in (1, 2, 3):
            E(f"{p}.difficulty: must be 1 (core), 2 (standard) or 3 (hard)")
        elif d is None and lst in ("quiz", "fill", "worked", "diagnostic"):
            W(f"{p}.difficulty: missing, treated as 2")
        if d == 3 and needs_m and lst in ("quiz", "fill", "worked", "flashcards"):
            hard[it["m"]] += 1
        key = (lst, re.sub(r"\s+", " ", str(it.get("q") or it.get("prompt") or it.get("front") or it.get("title") or "")).strip().lower())
        if key[1]:
            if key in seen_text:
                W(f"{p}: same wording as {seen_text[key]}")
            seen_text[key] = p
        for field in ("q", "prompt", "front", "back", "title", "why", "answer"):
            if isinstance(it.get(field), str) and PLACEHOLDER.search(it[field]):
                W(f"{p}.{field}: looks like placeholder text")
        return p

    def check_mcq(lst):
        positions, longest, kinds = Counter(), 0, Counter()
        items = data.get(lst) or []
        for i, q in enumerate(items):
            p = common(lst, i, q)
            if not p:
                continue
            if not _s(q.get("q")):
                E(f"{p}.q: required")
            opts = q.get("options")
            if not isinstance(opts, list) or not 2 <= len(opts) <= 6 or not all(_s(o) for o in opts):
                E(f"{p}.options: need 2-6 non-empty strings")
                continue
            if len({o.strip().lower() for o in opts}) != len(opts):
                E(f"{p}.options: duplicate options")
            a = q.get("answer")
            if not isinstance(a, int) or isinstance(a, bool) or not 0 <= a < len(opts):
                E(f"{p}.answer: must be the 0-based index of the correct option")
                continue
            if not _s(q.get("why")):
                E(f"{p}.why: explain why the answer is right and why the tempting options are not")
            positions[a] += 1
            if len(opts[a]) == max(len(o) for o in opts) and len({len(o) for o in opts}) > 1:
                longest += 1
            if any(re.search(r"all of the above|none of the above", o, re.I) for o in opts):
                W(f"{p}.options: avoid 'all/none of the above'")
            if lst == "quiz":
                k = q.get("kind")
                if k not in KINDS:
                    W(f"{p}.kind: set one of {sorted(KINDS)}")
                else:
                    kinds[k] += 1
                probes = q.get("probes")
                if probes is not None:
                    if not isinstance(probes, dict):
                        E(f"{p}.probes: must map a wrong option index to a narrower question")
                    else:
                        for k2, v in probes.items():
                            if not str(k2).isdigit() or not 0 <= int(k2) < len(opts) or int(k2) == a or not _s(v):
                                E(f"{p}.probes['{k2}']: key must be a wrong option index, value a question")
                if not probes and not _s(q.get("probe")):
                    W(f"{p}: no probe. Add 'probes' (per wrong option) or 'probe' so a miss gets a narrower question, not the answer")
                texts = list((probes or {}).values()) + [q.get("probe") or ""]
                correct = opts[a].strip().lower()
                if len(correct) > 3 and any(correct in str(t).lower() for t in texts):
                    W(f"{p}: a probe contains the correct option text. Probes must not give the answer away")
                df = q.get("defend")
                if df is not None and not (isinstance(df, dict) and _s(df.get("q")) and _s(df.get("a"))):
                    E(f"{p}.defend: needs q (the challenge) and a (the defence)")
        total = sum(positions.values())
        if total >= 8:
            pos, c = positions.most_common(1)[0]
            if c / total > 0.45:
                W(f"{lst}: the correct answer is option {'ABCDEF'[pos]} in {c} of {total} questions. Spread it out")
            if longest / total > 0.6:
                W(f"{lst}: the correct option is the longest one in {longest} of {total} questions. That is a tell")
        if lst == "quiz" and total >= 6 and kinds.get("recall", 0) / total > 0.4:
            W(f"quiz: {kinds['recall']} of {total} questions are plain recall. Prefer predict, explain, flaw, apply and connect")
        if lst == "quiz" and total >= 8 and not kinds.get("flaw"):
            W("quiz: no 'flaw' questions. Add some that ask the student to find the error in a plausible claim")
        return items

    check_mcq("quiz")
    diag = check_mcq("diagnostic")

    for i, c in enumerate(data.get("flashcards") or []):
        p = common("flashcards", i, c)
        if p:
            if not _s(c.get("front")) or not _s(c.get("back")):
                E(f"{p}: needs front and back")
            elif len(c["back"]) > 320:
                W(f"{p}.back: {len(c['back'])} characters. One idea per card")

    for i, f in enumerate(data.get("fill") or []):
        p = common("fill", i, f)
        if not p:
            continue
        if not _s(f.get("prompt")):
            E(f"{p}.prompt: required")
        if not _s(f.get("answer")):
            E(f"{p}.answer: the display answer is required")
        acc = f.get("accept")
        if not isinstance(acc, list) or not acc or not all(_s(a) for a in acc):
            E(f"{p}.accept: need a non-empty list of accepted answers")
        else:
            for a in acc:
                if a.startswith("re:"):
                    try:
                        re.compile(a[3:])
                    except re.error as e:
                        E(f"{p}.accept: bad regex '{a}': {e}")
                elif a.startswith("num:"):
                    if not re.fullmatch(r"num:-?\d+(\.\d+)?(±\d+(\.\d+)?)?", a):
                        E(f"{p}.accept: '{a}' should look like num:3.14 or num:3.14±0.01")
            if len(acc) == 1 and not acc[0].startswith(("re:", "num:")) and len(acc[0]) > 12:
                W(f"{p}.accept: one long exact string. Add the variants a student would reasonably type")
        if not _s(f.get("hint")):
            W(f"{p}.hint: missing")

    for i, w in enumerate(data.get("worked") or []):
        p = common("worked", i, w)
        if not p:
            continue
        if not _s(w.get("title")):
            E(f"{p}.title: required (state the problem)")
        steps = w.get("steps")
        if not isinstance(steps, list) or len(steps) < 2:
            E(f"{p}.steps: need at least 2 steps")
            continue
        for j, s in enumerate(steps):
            if not (isinstance(s, dict) and _s(s.get("text"))):
                E(f"{p}.steps[{j}].text: required")
            elif not _s(s.get("why")):
                W(f"{p}.steps[{j}].why: name the rule or reason for the step")
        if not any(isinstance(s, dict) and _s(s.get("ask")) for s in steps):
            W(f"{p}: no step has an 'ask'. Add the question a tutor would pose before revealing the step")

    def check_rubric(lst, needs_m):
        for i, x in enumerate(data.get(lst) or []):
            p = common(lst, i, x, needs_m=needs_m)
            if not p:
                continue
            if not _s(x.get("prompt")):
                E(f"{p}.prompt: required")
            rub = x.get("rubric")
            if not isinstance(rub, list) or len(rub) < 2 or not all(_s(r) for r in rub):
                E(f"{p}.rubric: need at least 2 checkable points")
            if lst == "integrative":
                ms = x.get("modules") or []
                if any(not isinstance(v, int) or not 0 <= v < n for v in ms):
                    E(f"{p}.modules: indexes out of range")
                elif len(set(ms)) < 2:
                    W(f"{p}.modules: an integrative problem should combine at least 2 modules")

    check_rubric("explain", True)
    check_rubric("integrative", False)

    if not data.get("integrative"):
        W("integrative: none. The final assessment needs at least one problem that combines modules")
    if len(diag) < min(3, n):
        W(f"diagnostic: {len(diag)} questions. Write 3-5 for a short course, or one per module, spanning easy to hard")
    elif diag and len({q.get('difficulty', 2) for q in diag if isinstance(q, dict)}) < 2:
        W("diagnostic: all questions share one difficulty. Span easy to hard")

    for i in range(n):
        c, name = per_mod[i], f"module {i} ({modules[i].get('title', '?') if isinstance(modules[i], dict) else '?'})"
        if c["quiz"] + c["fill"] == 0:
            E(f"{name}: no quiz or fill items, so the final assessment cannot test it")
        if c["quiz"] < 3:
            W(f"{name}: {c['quiz']} quiz questions (aim for 3+)")
        if c["fill"] < 1:
            W(f"{name}: no short-answer item (free recall is the 'unprompted' check)")
        if c["flashcards"] < 3:
            W(f"{name}: {c['flashcards']} flashcards (aim for 3+)")
        if c["worked"] < 1:
            W(f"{name}: no worked problem. Level 4 then rests on quiz and recall only")
        if c["explain"] < 1 and hard[i] < 1:
            E(f"{name}: no hard (difficulty 3) item and no teach-back, so level 5 can never be reached")
        elif c["explain"] < 1:
            W(f"{name}: no teach-back ('explain') item")
        elif hard[i] < 1:
            W(f"{name}: no difficulty-3 item (an edge case or adversarial question)")
        if c["diagnostic"] < 1 and diag:
            W(f"{name}: no diagnostic question, so it always starts at level 0")

    practice = [it for lst in ("quiz", "fill", "worked") for it in (data.get(lst) or []) if isinstance(it, dict)]
    no_src = sum(1 for it in practice if not _s(it.get("src")))
    if practice and no_src:
        W(f"{no_src} of {len(practice)} quiz, fill and worked items have no 'src'. "
          "Say where each one comes from (file and page or slide) so the student can check it")
    missed = coverage(data, manifest)
    for p2 in missed[:20]:
        W(f"coverage: '{p2}' is not cited by any module source or item src. Cover it, or tell the user it was left out")
    if len(missed) > 20:
        W(f"coverage: and {len(missed) - 20} more uncited files")

    stats = {"modules": n}
    stats.update({k: len(data.get(k) or []) for k in ITEM_LISTS})
    stats["figures"] = sum(1 for _ in iter_figures(data))
    return errors, warnings, stats


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Validate a course.json for the study page.")
    ap.add_argument("course")
    ap.add_argument("--manifest", help="scan manifest, to check that module sources name real files")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    args = ap.parse_args(argv)
    path = Path(args.course)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: cannot read {path}: {e}", file=sys.stderr)
        return 2
    manifest = None
    mp = Path(args.manifest) if args.manifest else path.parent / ".study" / "manifest.json"
    if mp.exists():
        try:
            manifest = json.loads(mp.read_text(encoding="utf-8"))
        except Exception:
            manifest = None
    errors, warnings, stats = validate(data, manifest, path.parent)
    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings, "stats": stats}, indent=2, ensure_ascii=False))
    else:
        print("Counts: " + ", ".join(f"{k} {v}" for k, v in stats.items()))
        for e in errors:
            print("ERROR  " + e)
        for w in warnings:
            print("warn   " + w)
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)." + ("" if errors or warnings else " Ready to build."))
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
