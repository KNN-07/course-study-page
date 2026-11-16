#!/usr/bin/env python3
"""Inventory a course folder and extract its text so an agent can read it.

Usage:  python scan_materials.py <course-folder> [--out DIR] [--json]

Writes into <course-folder>/.study/ (or --out):
  manifest.json        one entry per file: kind, role guess, status, size, headings, change state
  outline.md           a readable digest of the manifest (read this first)
  extracted/<path>.txt plain text per readable file, with "--- Page N ---" / "--- Slide N ---" markers

Standard library only. PDFs use pypdf / PyPDF2 / PyMuPDF / pdfminer.six / the
`pdftotext` binary, whichever is present. Anything that cannot be turned into
text here is reported with status "needs_native_read" so the agent opens it
with its own file or vision tools instead of skipping it silently.
"""
from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SKIP_DIRS = {".git", ".study", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode",
             ".claude", ".codex", ".agents", ".agent", ".opencode", ".gemini", ".cursor", "__MACOSX"}
SKIP_FILES = {"course.json", "study.html", ".ds_store", "thumbs.db", "desktop.ini"}

TEXT_EXT = {".md", ".markdown", ".txt", ".rst", ".tex", ".org", ".adoc", ".csv", ".tsv", ".json",
            ".yaml", ".yml", ".bib", ".typ", ".qmd", ".rmd"}
CODE_EXT = {".py", ".java", ".c", ".h", ".cpp", ".hpp", ".cc", ".cs", ".js", ".ts", ".jsx", ".tsx",
            ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".m", ".r", ".jl", ".sql", ".sh",
            ".ps1", ".ml", ".mli", ".hs", ".lisp", ".clj", ".pl", ".v", ".sv", ".vhd", ".asm", ".s"}
SUB_EXT = {".srt", ".vtt"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".svg"}
AV_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mp4", ".mov", ".mkv", ".avi", ".webm"}
LEGACY_EXT = {".doc", ".ppt", ".xls", ".rtf", ".pages", ".key", ".numbers", ".epub", ".djvu"}
ARCHIVE_EXT = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz"}

ROLE_HINTS = [
    ("syllabus", r"syllabus|outline|schedule|course[-_ ]?info|handbook|module[-_ ]?guide|overview"),
    ("solution", r"solution|soln|answers?|answer[-_ ]?key|marking|mark[-_ ]?scheme|rubric"),
    ("exam", r"exam|midterm|mid[-_ ]?term|final|quiz|test|past[-_ ]?paper|mock"),
    ("assignment", r"assignment|homework|hw\d*|problem[-_ ]?set|pset|ps\d+|worksheet|tutorial|tut\d+|exercise|lab\d*|practical|coursework"),
    ("lecture", r"lecture|lec\d*|slides?|week[-_ ]?\d+|wk\d+|session|unit[-_ ]?\d+|chapter|ch\d+|topic|class\d*"),
    ("notes", r"notes?|summary|cheat|revision|review|study[-_ ]?guide|formula"),
    ("reading", r"reading|paper|article|textbook|book|reference"),
]


def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def read_text_file(p: Path) -> str:
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return raw.decode("utf-8", errors="replace")


class _Stripper(html.parser.HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "pre", "table"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
        elif tag in ("h1", "h2", "h3", "h4"):
            self.out.append("\n" + "#" * int(tag[1]) + " ")
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_to_text(s: str) -> str:
    st = _Stripper()
    st.feed(s)
    return re.sub(r"\n{3,}", "\n\n", "".join(st.out)).strip()


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def xml_paragraphs(data: bytes, para_tag: str = "p", text_tag: str = "t"):
    """Yield (style, text) for each paragraph element in an OOXML/ODF part."""
    root = ET.fromstring(data)
    for el in root.iter():
        if local(el.tag) != para_tag:
            continue
        style = ""
        parts = []
        for sub in el.iter():
            name = local(sub.tag)
            if name == "pStyle":
                style = next((v for k, v in sub.attrib.items() if local(k) == "val"), "")
            elif name == text_tag and sub.text:
                parts.append(sub.text)
            elif name in ("tab",):
                parts.append("\t")
            elif name in ("br", "cr"):
                parts.append("\n")
        text = "".join(parts).strip()
        if text:
            yield style, text


def extract_docx(p: Path):
    out = []
    with zipfile.ZipFile(p) as z:
        for style, text in xml_paragraphs(z.read("word/document.xml")):
            m = re.match(r"(?i)heading\s*(\d)", style or "")
            if m:
                out.append("\n" + "#" * int(m.group(1)) + " " + text)
            elif (style or "").lower() == "title":
                out.append("\n# " + text)
            else:
                out.append(text)
    return "\n".join(out).strip(), None


def extract_pptx(p: Path):
    out = []
    with zipfile.ZipFile(p) as z:
        names = z.namelist()
        slides = sorted((n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)), key=natural_key)
        for i, name in enumerate(slides, 1):
            lines = [t for _, t in xml_paragraphs(z.read(name))]
            out.append(f"--- Slide {i} ---")
            if lines:
                out.append("# " + lines[0])
                out.extend(lines[1:])
            num = re.search(r"(\d+)\.xml$", name).group(1)
            note = f"ppt/notesSlides/notesSlide{num}.xml"
            if note in names:
                notes = [t for _, t in xml_paragraphs(z.read(note)) if not t.strip().isdigit()]
                if notes:
                    out.append("[Speaker notes] " + " ".join(notes))
            out.append("")
    return "\n".join(out).strip(), len(slides)


def extract_xlsx(p: Path, max_rows: int = 400):
    out = []
    with zipfile.ZipFile(p) as z:
        names = z.namelist()
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root:
                shared.append("".join(t.text or "" for t in si.iter() if local(t.tag) == "t"))
        sheets = sorted((n for n in names if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)), key=natural_key)
        for i, name in enumerate(sheets, 1):
            out.append(f"--- Sheet {i} ---")
            root = ET.fromstring(z.read(name))
            rows = 0
            for row in root.iter():
                if local(row.tag) != "row":
                    continue
                cells = []
                for c in row:
                    v = next((x.text or "" for x in c.iter() if local(x.tag) in ("v", "t")), "")
                    if c.attrib.get("t") == "s" and v.isdigit() and int(v) < len(shared):
                        v = shared[int(v)]
                    cells.append(v.strip())
                if any(cells):
                    out.append(" | ".join(cells))
                    rows += 1
                if rows >= max_rows:
                    out.append(f"[truncated after {max_rows} rows]")
                    break
    return "\n".join(out).strip(), len(sheets)


def extract_odf(p: Path):
    with zipfile.ZipFile(p) as z:
        root = ET.fromstring(z.read("content.xml"))
    out = []
    for el in root.iter():
        name = local(el.tag)
        if name in ("p", "h"):
            text = "".join(el.itertext()).strip()
            if text:
                out.append(("# " if name == "h" else "") + text)
    return "\n".join(out), None


def extract_ipynb(p: Path):
    nb = json.loads(read_text_file(p))
    out = []
    for cell in nb.get("cells", []):
        src = cell.get("source", "")
        src = "".join(src) if isinstance(src, list) else str(src)
        if cell.get("cell_type") == "markdown":
            out.append(src)
        elif cell.get("cell_type") == "code":
            out.append("```\n" + src + "\n```")
            for o in cell.get("outputs", []):
                txt = o.get("text") or (o.get("data") or {}).get("text/plain") or ""
                txt = "".join(txt) if isinstance(txt, list) else str(txt)
                if txt.strip():
                    out.append("[Output]\n" + txt.strip()[:2000])
    return "\n\n".join(out), len(nb.get("cells", []))


def extract_subtitles(p: Path):
    lines = []
    for line in read_text_file(p).splitlines():
        s = line.strip()
        if not s or s.isdigit() or "-->" in s or s.upper().startswith("WEBVTT"):
            continue
        s = re.sub(r"<[^>]+>", "", s)
        if not lines or lines[-1] != s:
            lines.append(s)
    return " ".join(lines), None


def extract_pdf(p: Path):
    """Return (text, pages, engine) or (None, pages, reason)."""
    errors = []
    for mod in ("pypdf", "PyPDF2"):
        try:
            lib = __import__(mod)
            reader = lib.PdfReader(str(p))
            pages = []
            for i, page in enumerate(reader.pages, 1):
                pages.append(f"--- Page {i} ---\n" + (page.extract_text() or "").strip())
            return "\n\n".join(pages), len(pages), mod
        except ImportError:
            continue
        except Exception as e:  # corrupt or encrypted file: try the next engine
            errors.append(f"{mod}: {e}")
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(p))
        pages = [f"--- Page {i} ---\n" + pg.get_text().strip() for i, pg in enumerate(doc, 1)]
        return "\n\n".join(pages), len(pages), "pymupdf"
    except ImportError:
        pass
    except Exception as e:
        errors.append(f"pymupdf: {e}")
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(str(p)) or ""
        chunks = text.split("\f")
        pages = [f"--- Page {i} ---\n" + c.strip() for i, c in enumerate(chunks, 1) if c.strip()]
        return "\n\n".join(pages), len(pages), "pdfminer"
    except ImportError:
        pass
    except Exception as e:
        errors.append(f"pdfminer: {e}")
    exe = shutil.which("pdftotext")
    if exe:
        try:
            res = subprocess.run([exe, "-layout", "-enc", "UTF-8", str(p), "-"], capture_output=True, timeout=180)
            if res.returncode == 0:
                chunks = res.stdout.decode("utf-8", errors="replace").split("\f")
                pages = [f"--- Page {i} ---\n" + c.strip() for i, c in enumerate(chunks, 1) if c.strip()]
                return "\n\n".join(pages), len(pages), "pdftotext"
            errors.append("pdftotext: exit %d" % res.returncode)
        except Exception as e:
            errors.append(f"pdftotext: {e}")
    reason = "; ".join(errors) if errors else "no PDF text engine installed (pip install pypdf)"
    return None, None, reason


def guess_role(rel: str, kind: str) -> str:
    low = rel.lower()
    for role, pat in ROLE_HINTS:
        if re.search(r"(?<![a-z])(" + pat + r")(?![a-z])", low):
            return role
    return {"code": "code", "data": "data", "image": "figure"}.get(kind, "other")


def headings_of(text: str, limit: int = 40):
    heads = []
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^(#{1,4})\s+(.+)$", s) or re.match(r"^\\(?:chapter|section|subsection)\*?\{(.+?)\}", s)
        if m:
            h = m.group(m.lastindex).strip()
            if h and h not in heads:
                heads.append(h[:120])
        if len(heads) >= limit:
            break
    return heads


def scan(root: Path, out: Path):
    prev = {}
    mf = out / "manifest.json"
    if mf.exists():
        try:
            prev = {f["path"]: f for f in json.loads(mf.read_text(encoding="utf-8")).get("files", [])}
        except Exception:
            prev = {}
    ex_dir = out / "extracted"
    ex_dir.mkdir(parents=True, exist_ok=True)
    out_res = out.resolve()
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted((d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")), key=natural_key)
        if Path(dirpath).resolve() == out_res:
            dirnames[:] = []
            continue
        for fn in sorted(filenames, key=natural_key):
            if fn.lower() in SKIP_FILES or fn.startswith("~$") or fn.startswith("."):
                continue
            files.append(Path(dirpath) / fn)

    entries = []
    for p in files:
        rel = p.relative_to(root).as_posix()
        ext = p.suffix.lower()
        raw = p.read_bytes()
        entry = {"path": rel, "ext": ext, "bytes": len(raw), "sha1": hashlib.sha1(raw).hexdigest()}
        text, units, note, kind, status = None, None, "", "other", "ok"
        try:
            if ext in TEXT_EXT:
                kind = "data" if ext in (".csv", ".tsv", ".json", ".yaml", ".yml") else "text"
                text = read_text_file(p)
            elif ext in CODE_EXT:
                kind, text = "code", read_text_file(p)
            elif ext in (".html", ".htm"):
                kind, text = "text", html_to_text(read_text_file(p))
            elif ext in SUB_EXT:
                kind = "transcript"
                text, units = extract_subtitles(p)
            elif ext == ".ipynb":
                kind = "notebook"
                text, units = extract_ipynb(p)
            elif ext == ".docx":
                kind = "document"
                text, units = extract_docx(p)
            elif ext == ".pptx":
                kind = "slides"
                text, units = extract_pptx(p)
            elif ext == ".xlsx":
                kind = "data"
                text, units = extract_xlsx(p)
            elif ext in (".odt", ".odp"):
                kind = "document" if ext == ".odt" else "slides"
                text, units = extract_odf(p)
            elif ext == ".pdf":
                kind = "pdf"
                text, units, engine = extract_pdf(p)
                if text is None:
                    status, note = "needs_native_read", engine
                else:
                    body = re.sub(r"--- Page \d+ ---", "", text)
                    if units and len(body.strip()) / max(1, units) < 60:
                        status, text = "needs_native_read", None
                        note = "almost no text layer (scanned or image-only PDF): read it with a PDF or vision tool"
                    else:
                        note = "engine: " + engine
            elif ext in IMG_EXT:
                kind, status, note = "image", "needs_native_read", "image: open it with a vision tool if it carries content"
            elif ext in AV_EXT:
                kind, status, note = "media", "skipped", "audio/video: needs a transcript (.srt, .vtt or .txt beside it)"
            elif ext in LEGACY_EXT:
                kind, status, note = "document", "needs_conversion", "legacy or packaged format: convert to .docx/.pptx/.pdf, or read natively"
            elif ext in ARCHIVE_EXT:
                kind, status, note = "archive", "skipped", "archive: unpack it and scan again"
            else:
                status, note = "skipped", "unrecognised type"
        except Exception as e:  # one bad file must not stop the scan
            status, text, note = "error", None, f"{type(e).__name__}: {e}"

        entry.update(kind=kind, role=guess_role(rel, kind), status=status)
        if units:
            entry["units"] = units
        if note:
            entry["note"] = note
        if text is not None:
            text = text.replace("\r\n", "\n").replace("\x00", "")
            if not text.strip():
                entry["status"], entry["note"] = "empty", "no text found"
            else:
                target = ex_dir / (rel + ".txt")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
                entry["extracted"] = target.relative_to(out).as_posix()
                entry["chars"] = len(text)
                entry["words"] = len(text.split())
                heads = headings_of(text)
                if heads:
                    entry["headings"] = heads
        old = prev.get(rel)
        entry["change"] = "new" if not old else ("unchanged" if old.get("sha1") == entry["sha1"] else "changed")
        entries.append(entry)

    removed = sorted(set(prev) - {e["path"] for e in entries})
    totals = {
        "files": len(entries),
        "readable": sum(1 for e in entries if e.get("extracted")),
        "needs_attention": sum(1 for e in entries if e["status"] in ("needs_native_read", "needs_conversion", "error")),
        "skipped": sum(1 for e in entries if e["status"] in ("skipped", "empty")),
        "words": sum(e.get("words", 0) for e in entries),
        "changed": sum(1 for e in entries if e["change"] != "unchanged") + len(removed),
    }
    manifest = {"schema": 1, "root": str(root), "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "totals": totals, "removed": removed, "files": entries}
    mf.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "outline.md").write_text(outline(manifest), encoding="utf-8")
    return manifest


def outline(man) -> str:
    t = man["totals"]
    lines = ["# Course materials outline", "",
             f"{t['files']} files, {t['readable']} readable as text (~{t['words']:,} words), "
             f"{t['needs_attention']} need attention, {t['skipped']} skipped.", ""]
    attention = [e for e in man["files"] if e["status"] in ("needs_native_read", "needs_conversion", "error")]
    if attention:
        lines += ["## Read these yourself (no text could be extracted)", ""]
        lines += [f"- `{e['path']}`: {e.get('note', e['status'])}" for e in attention] + [""]
    if man["removed"]:
        lines += ["## Removed since the last scan", ""] + [f"- `{p}`" for p in man["removed"]] + [""]
    by_role = {}
    for e in man["files"]:
        by_role.setdefault(e["role"], []).append(e)
    order = ["syllabus", "lecture", "notes", "reading", "assignment", "exam", "solution", "code", "data", "figure", "other"]
    for role in order + sorted(set(by_role) - set(order)):
        if role not in by_role:
            continue
        lines += [f"## {role.capitalize()} ({len(by_role[role])})", ""]
        for e in by_role[role]:
            bits = [e["kind"]]
            if e.get("units"):
                bits.append(f"{e['units']} {'slides' if e['kind'] == 'slides' else 'pages' if e['kind'] == 'pdf' else 'units'}")
            if e.get("words"):
                bits.append(f"{e['words']:,} words")
            if e["status"] != "ok":
                bits.append(e["status"])
            if e["change"] != "unchanged":
                bits.append(e["change"])
            lines.append(f"- `{e['path']}` ({', '.join(bits)})" + (f" -> `{e['extracted']}`" if e.get("extracted") else ""))
            for h in e.get("headings", [])[:12]:
                lines.append(f"  - {h}")
        lines.append("")
    lines += ["Role labels are guesses from file names. Check them against the content.", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Inventory a course folder and extract readable text.")
    ap.add_argument("folder", help="folder holding the course materials")
    ap.add_argument("--out", help="output folder (default: <folder>/.study)")
    ap.add_argument("--json", action="store_true", help="print the manifest as JSON instead of a summary")
    args = ap.parse_args(argv)
    root = Path(args.folder).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a folder: {root}", file=sys.stderr)
        return 2
    out = Path(args.out).expanduser().resolve() if args.out else root / ".study"
    man = scan(root, out)
    if args.json:
        print(json.dumps(man, indent=2, ensure_ascii=False))
        return 0
    t = man["totals"]
    print(f"Scanned {root}")
    print(f"  {t['files']} files | {t['readable']} extracted (~{t['words']:,} words) | "
          f"{t['needs_attention']} need attention | {t['skipped']} skipped | {t['changed']} changed since last scan")
    for e in man["files"]:
        flag = {"ok": " ", "needs_native_read": "!", "needs_conversion": "!", "error": "x"}.get(e["status"], "-")
        size = f"{e.get('words', 0):>7,}w" if e.get("words") else " " * 8
        print(f"  {flag} {e['role']:<10} {size}  {e['path']}" + (f"   [{e.get('note', e['status'])}]" if e["status"] != "ok" else ""))
    print(f"\nManifest: {out / 'manifest.json'}")
    print(f"Outline:  {out / 'outline.md'}  (read this first)")
    if t["files"] == 0:
        print("\nNo files found. Check the folder path.")
    elif t["needs_attention"]:
        print("\nFiles marked ! or x have no extracted text. Open each one with your own file or vision tools before authoring.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
