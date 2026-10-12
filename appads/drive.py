from __future__ import annotations

import re
import zipfile
from xml.etree import ElementTree

from .common import Quit, default_mode, input_folder, normalize, print_summary, raw_lines, update_network, update_raw
from .config import RAW
from .model import Parsed, combine, parse_text, warn
from .names import resolve

READABLE = {".txt", ".docx"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"   # Word XML namespace


def read_docx(path):
    """Text of a Word document, one paragraph per line (standard library only)."""
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    lines = []
    for paragraph in root.iter(f"{W}p"):
        text = ""
        for node in paragraph.iter():
            if node.tag == f"{W}t":
                text += node.text or ""
            elif node.tag == f"{W}tab":
                text += " "
            elif node.tag in (f"{W}br", f"{W}cr"):
                text += "\n"
        lines.append(text)
    return "\n".join(lines)


def read_text(path):
    """File content; an unreadable file reads as empty (and is reported)."""
    try:
        if path.suffix.lower() == ".docx":
            return read_docx(path)
        return path.read_text(encoding="utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError):
        warn(f"{path.name}: cannot read the file, skipped")
        return ""


def base_name(path):
    """Network name = first word of the file name: 'YandexAds CASAI.docx' -> 'YandexAds'."""
    return re.split(r"[\s_]+", path.stem.strip(" _"))[0]


def collect(folder):
    """Returns ({network name key: [paths]}, [files of unsupported types])."""
    groups, unsupported = {}, []
    for path in sorted(folder.rglob("*"), key=lambda p: p.name.lower()):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in READABLE:
            unsupported.append(path)
            continue
        groups.setdefault(normalize(base_name(path)), []).append(path)
    return groups, unsupported


def run(args, root):
    groups, unsupported = collect(input_folder(args.folder, root))
    result = {"updated": [], "unchanged": [], "declined": [], "empty": [], "not found": []}

    try:
        for paths in groups.values():
            title = base_name(paths[0])
            texts = [read_text(p) for p in paths]
            raw = normalize(title) in {normalize(n) for n in RAW}   # RAW files are not validated
            print(f"\n=== {title}")
            if raw:
                incoming = Parsed()
                counts = [len(raw_lines([t])) for t in texts]
            else:
                parts = [parse_text(t, p.name) for p, t in zip(paths, texts)]
                incoming = combine(parts)
                counts = [len(part.records) + len(part.variables) for part in parts]
            print("    " + ", ".join(f"{p.name}: {c} lines" if c else f"{p.name}: empty"
                                     for p, c in zip(paths, counts)))

            if not any(counts):
                warn(f"{title}: no lines, skipped")
                result["empty"].append(title)
                continue
            path = resolve(root, title, args.yes)
            if path is None:
                result["not found"].append(title)
                continue
            if path.stem in RAW:
                status = update_raw(path, texts, args.yes)
            else:
                status = update_network(root, path, incoming, default_mode(path.stem), args.yes)
            result[status].append(path.stem)
    except Quit:
        print("\nStopped. Updates applied so far are kept.")

    extra = [f"unsupported files ({', '.join(sorted(READABLE))} only): " + ", ".join(p.name for p in unsupported)]
    print_summary(result, extra if unsupported else ())
    return 0