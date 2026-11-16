#!/usr/bin/env python3
"""Build the single-file interactive study page from a course.json.

Usage:  python build_page.py <course.json> [-o study.html] [--template FILE] [--force]

Validates first (errors stop the build unless --force), gives every item a
stable id derived from its content so saved progress survives a rebuild, then
injects the data into assets/template.html. The output is one self-contained
HTML file: open it in a browser, or publish it wherever the agent can host a
page. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from validate_course import coverage, iter_figures, validate  # noqa: E402

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
        ".webp": "image/webp", ".svg": "image/svg+xml"}
FIG_MAX = 700_000      # one picture
FIG_TOTAL = 9_000_000  # all pictures; hosted pages are usually capped around 16 MB


def embed_figures(data: dict, base: Path):
    """Inline every local figure as a data URI so the page stays one file."""
    import base64
    problems, total, cache = [], 0, {}
    for loc, f in iter_figures(data):
        src = str(f.get("src") or "")
        if not src or src.startswith(("data:image/", "https://")):
            continue
        p = (base / src).resolve()
        if src not in cache:
            try:
                raw = p.read_bytes()
            except OSError as e:
                problems.append(f"{loc}: cannot read {src}: {e}")
                continue
            if len(raw) > FIG_MAX:
                problems.append(f"{loc}: {src} is {len(raw) // 1024} KB. Downscale or crop it below {FIG_MAX // 1000} KB")
                continue
            total += len(raw)
            cache[src] = f"data:{MIME.get(p.suffix.lower(), 'image/png')};base64," + base64.b64encode(raw).decode("ascii")
        f["src"] = cache[src]
    if total > FIG_TOTAL:
        problems.append(f"figures total {total // 1_000_000} MB. Keep the page under {FIG_TOTAL // 1_000_000} MB of pictures")
    return problems

KATEX = ('<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>\n'
         '<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js" '
         'onload="window.__render&&window.__render()"></script>')
PREFIX = {"quiz": "q", "fill": "f", "flashcards": "c", "worked": "w", "explain": "x", "diagnostic": "d", "integrative": "i"}
KEY_FIELD = {"quiz": "q", "fill": "prompt", "flashcards": "front", "worked": "title", "explain": "prompt",
             "diagnostic": "q", "integrative": "prompt"}


def h8(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def assign_ids(data: dict) -> None:
    used = set()
    for lst, pre in PREFIX.items():
        for it in data.get(lst) or []:
            if it.get("id"):
                used.add(str(it["id"]))
    for lst, pre in PREFIX.items():
        for it in data.get(lst) or []:
            if it.get("id"):
                it["id"] = str(it["id"])
                continue
            base = pre + "-" + h8(re.sub(r"\s+", " ", str(it.get(KEY_FIELD[lst], ""))).strip().lower())
            cand, k = base, 2
            while cand in used:
                cand, k = f"{base}-{k}", k + 1
            used.add(cand)
            it["id"] = cand


MATH = re.compile(r"\$\$.+?\$\$|\$[^\s$]\$|\$[^\s$][^$\n]*?[^\s$]\$|\\\(.+?\\\)|\\\[.+?\\\]", re.S)


def has_math(node, key: str = "") -> bool:
    """True when any displayed string holds TeX delimiters. Answer patterns are not displayed."""
    if key == "accept":
        return False
    if isinstance(node, str):
        return bool(MATH.search(node))
    if isinstance(node, dict):
        return any(has_math(v, k) for k, v in node.items())
    if isinstance(node, list):
        return any(has_math(v, key) for v in node)
    return False


def short_title(course: dict) -> str:
    code = str(course.get("code") or "").strip()
    if code and not code.startswith("["):
        return (code + " study page")[:60]
    words = re.sub(r"[:\-–—|].*$", "", str(course.get("title") or "Course")).split()
    return " ".join(words[:3]) + (" study page" if len(words) <= 2 else "")


def build(course_path: Path, out_path: Path, template_path: Path, force: bool = False) -> int:
    data = json.loads(course_path.read_text(encoding="utf-8-sig"))
    manifest = None
    mp = course_path.parent / ".study" / "manifest.json"
    if mp.exists():
        try:
            manifest = json.loads(mp.read_text(encoding="utf-8"))
        except Exception:
            manifest = None
    errors, warnings, stats = validate(data, manifest, course_path.parent)
    uncovered = coverage(data, manifest)
    if not errors:
        errors += embed_figures(data, course_path.parent)
    for e in errors:
        print("ERROR  " + e)
    if errors and not force:
        print(f"\nBuild stopped: {len(errors)} error(s). Fix course.json and run again.")
        return 1

    course = data.setdefault("course", {})
    for m in data.get("modules") or []:
        if not str(m.get("short") or "").strip():
            m["short"] = str(m.get("title", ""))[:22]
    assign_ids(data)
    if not data.get("id"):
        slug = re.sub(r"[^a-z0-9]+", "-", str(course.get("title", "course")).lower()).strip("-")[:40]
        data["id"] = f"{slug}-{h8(str(course.get('title')) + '|' + str(course.get('code')))}"
    if manifest and not data.get("sources"):
        data["sources"] = [f["path"] for f in manifest.get("files", []) if f.get("extracted") or f.get("status") == "needs_native_read"][:60]
    if uncovered:
        data["coverage"] = {"uncovered": uncovered}
    else:
        data.pop("coverage", None)
    data["built"] = time.strftime("%Y-%m-%d")
    if "math" not in course:
        course["math"] = has_math(data)

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    lang = re.sub(r"[^A-Za-z-]", "", str(course.get("lang") or "en")) or "en"
    html = template_path.read_text(encoding="utf-8")
    for token in ("__COURSE_JSON__", "__TITLE__", "__LANG__", "__HEAD_EXTRA__"):
        if token not in html:
            print(f"error: template is missing {token}")
            return 2
    title = short_title(course).replace("&", "&amp;").replace("<", "&lt;")
    html = (html.replace("__TITLE__", title).replace("__LANG__", lang)
                .replace("__HEAD_EXTRA__", KATEX if course["math"] else "")
                .replace("__COURSE_JSON__", payload))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    print(f"Built {out_path}  ({out_path.stat().st_size / 1024:.0f} KB)")
    print("  " + ", ".join(f"{k} {v}" for k, v in stats.items()) + (", math on" if course["math"] else ""))
    if uncovered:
        print(f"  {len(uncovered)} course file(s) not covered. The page tells the student which.")
    if warnings:
        print(f"  {len(warnings)} warning(s). Run validate_course.py to see them.")
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Build the interactive study page.")
    ap.add_argument("course", help="path to course.json")
    ap.add_argument("-o", "--out", help="output HTML (default: study.html beside course.json)")
    ap.add_argument("--template", default=str(HERE.parent / "assets" / "template.html"))
    ap.add_argument("--force", action="store_true", help="build even when validation reports errors")
    args = ap.parse_args(argv)
    course_path = Path(args.course).expanduser().resolve()
    if not course_path.is_file():
        print(f"error: no such file: {course_path}", file=sys.stderr)
        return 2
    out = Path(args.out).expanduser().resolve() if args.out else course_path.parent / "study.html"
    try:
        return build(course_path, out, Path(args.template), args.force)
    except json.JSONDecodeError as e:
        print(f"error: {course_path} is not valid JSON: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
