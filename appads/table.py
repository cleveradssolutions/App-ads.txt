from __future__ import annotations

import csv

from .common import Quit, input_folder, normalize, print_summary, update_network
from .config import RAW
from .model import CERTS, Parsed, Record, combine, parse_line, warn
from .names import clean_name, resolve

DELIMITERS = {".tsv": "\t", ".csv": ","}


def read_tables(folder):
    """Returns {name key: (name as written, [entries])} in table order."""
    files = sorted((p for p in folder.rglob("*") if p.suffix.lower() in DELIMITERS), key=lambda p: p.name.lower())
    if not files:
        raise SystemExit(f"No .tsv/.csv tables in {folder}")
    groups = {}
    for path in files:
        print(f"Reading {path.name}")
        with path.open(encoding="utf-8-sig", newline="") as f:
            for number, row in enumerate(csv.reader(f, delimiter=DELIMITERS[path.suffix.lower()]), 1):
                cells = [c.strip() for c in row]
                if not any(cells):
                    continue
                name, line = cells[0], ", ".join(c for c in cells[1:] if c)
                if number == 1 and "," not in line and "=" not in line:
                    continue   # header row
                source = f"{path.name}:{number}"
                if not name or not line:
                    warn(f"{source}: empty partner name or line, skipped", ",".join(cells))
                    continue
                entry = parse_line(line, source)
                if entry is not None:
                    key = normalize(clean_name(name)) or normalize(name)
                    groups.setdefault(key, (name.strip(), []))[1].append(entry)
    return groups


def to_parsed(entries):
    return combine([Parsed(variables=[e for e in entries if not isinstance(e, Record)],
                           records=[e for e in entries if isinstance(e, Record)])])


def run(args, root):
    removing = args.action == "remove"
    CERTS.learn = not removing   # lines being removed must not teach new certification ids
    groups = read_tables(input_folder(args.folder, root))
    result = {"updated": [], "unchanged": [], "declined": [], "not found": []}

    try:
        # 1. names -> networks
        targets = {}
        for name, entries in groups.values():
            path = resolve(root, name, args.yes, allow_create=not removing)
            if path is None:
                result["not found"].append(name)
                continue
            names, collected = targets.setdefault(path, ([], []))
            names.append(name)
            collected.extend(entries)

        # 2. one update per network
        for path, (names, entries) in sorted(targets.items(), key=lambda t: t[0].stem.lower()):
            print(f"\n=== {path.stem}  (from: {', '.join(names)}, {len(entries)} lines)")
            if path.stem in RAW:
                warn(f"{path.stem} is copied as-is and updated only from a file (drive/update), skipped")
                result["declined"].append(path.stem)
                continue
            status = update_network(root, path, to_parsed(entries), "remove" if removing else "merge", args.yes)
            result[status].append(path.stem)
    except Quit:
        print("\nStopped. Updates applied so far are kept.")

    print_summary(result)
    return 0