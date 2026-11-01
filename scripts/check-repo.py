#!/usr/bin/env python3
"""Repo checks: broken links and anchors, dash and banned-word lint, private-data scan, script syntax.
Run from anywhere: python3 scripts/check-repo.py   Exit 1 if anything fails. Standard library only."""
import py_compile, re, subprocess, sys, tempfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "backups", "notes", "doorbell-files"}
VERBATIM = {"examples/halloween-2026/SPEC.md"}          # the original spec, kept as written
NO_LINT = ("docs/reference/data/",)                       # raw lists from the firmware
BANNED = "delve leverage leverages leveraged utilize utilizes foster bolster underscore unveil streamline robust comprehensive pivotal seamless seamlessly significantly extremely truly furthermore moreover".split()
PRIVATE = [
    ("private IPv4 address", r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b"),
    ("MAC address", r"\b[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}\b"),
    ("SSH fingerprint", r"SHA256:[A-Za-z0-9+/]{20,}"),
    ("password hash", r"\$[56y]\$[./A-Za-z0-9$]{12,}"),
    ("home path", r"/Users/[a-z]"),
    ("computer name", r"hosts-macbook"),
    ("private key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
errors = []

def files(*suffixes):
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT)
        if p.is_file() and not (set(rel.parts) & SKIP_DIRS) and (not suffixes or p.suffix in suffixes):
            yield p

def rel(p): return str(p.relative_to(ROOT))
def err(p, line, msg): errors.append(f"{rel(p)}:{line}: {msg}")

def slug(h):
    h = re.sub(r"[`*_]", "", h.strip().lower())
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", h))

def split_md(text):
    """yield (lineno, line, in_code) for markdown lines"""
    fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fence = not fence
            yield n, line, True
        else:
            yield n, line, fence

def anchors(p):
    out = set()
    for _, line, code in split_md(p.read_text()):
        m = re.match(r"#{1,6}\s+(.*)", line)
        if m and not code:
            out.add(slug(m.group(1)))
    return out

def check_links():
    for p in files(".md"):
        for n, line, code in split_md(p.read_text()):
            if code: continue
            for m in re.finditer(r"\[[^\]]*\]\(([^)\s]+)\)", re.sub(r"`[^`]*`", "", line)):
                t = m.group(1)
                if re.match(r"[a-z]+:", t): continue
                path, _, frag = t.partition("#")
                dest = (p.parent / unquote(path)).resolve() if path else p
                if not dest.exists():
                    err(p, n, f"broken link {t}")
                elif frag and dest.suffix == ".md" and slug(unquote(frag)) not in anchors(dest):
                    err(p, n, f"broken anchor {t}")

def check_prose():
    for p in files(".md"):
        r = rel(p)
        if r in VERBATIM or r.startswith(NO_LINT): continue
        for n, line, code in split_md(p.read_text()):
            if "—" in line or "–" in line:
                err(p, n, "em or en dash")
            if code: continue
            prose = re.sub(r"`[^`]*`|\]\([^)]*\)", "", line).lower()
            for w in BANNED:
                if re.search(rf"\b{w}\b", prose):
                    err(p, n, f"banned word '{w}'")

def check_private():
    self = Path(__file__).resolve()
    for p in files():
        if p.resolve() == self or p.suffix in {".png", ".gif", ".ogg", ".wav", ".mp3", ".anim"}: continue
        try: text = p.read_text()
        except UnicodeDecodeError: continue
        for n, line in enumerate(text.splitlines(), 1):
            for name, rx in PRIVATE:
                if re.search(rx, line):
                    err(p, n, f"possible {name}")

def check_scripts():
    for p in files(".sh"):
        shell = "bash" if "bash" in p.read_text().split("\n", 1)[0] else "sh"
        if subprocess.run([shell, "-n", str(p)], capture_output=True).returncode:
            err(p, 1, f"{shell} -n syntax error")
    for p in files(".py"):
        try: py_compile.compile(str(p), cfile=tempfile.mkstemp()[1], doraise=True)
        except py_compile.PyCompileError as e: err(p, 1, f"python syntax error: {e.msg}")

for check in (check_links, check_prose, check_private, check_scripts):
    check()
print("\n".join(errors) or "all checks passed")
sys.exit(1 if errors else 0)
