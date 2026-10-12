from __future__ import annotations

import shutil

from .common import (DIRS, Quit, all_files, ask, confirm, default_mode, is_generated, load_heads, normalize,
                     parse_domains, save_heads, set_head, update_network, update_raw)
from .config import DRIVE_DIR, GENERATED, HEADS_FILE, RAW, RELEASE_NETWORKS, TABLES_DIR, TEMP_FILE
from .model import build, read_file, to_lines, warn, write_file
from .names import match_network, resolve


def refuse_generated(name):
    if is_generated(name):
        raise SystemExit(f"{name} is built by `release` and is not edited by hand.")


def ask_mode(path, yes):
    """Update mode when neither -m nor -f is given."""
    if not path.exists():
        return "force"          # a new network: both modes give the same result
    if yes:
        raise SystemExit("With -y pass the mode: -f (force) or -m (merge).")
    hint = " (usually m for this network)" if default_mode(path.stem) == "merge" else ""
    while True:
        answer = ask(f"Mode{hint}: [f] force - remove lines missing from the update / "
                     f"[m] merge - keep existing lines / [q] quit: ").lower()
        if answer == "q":
            raise Quit
        if answer in ("f", "m"):
            return "force" if answer == "f" else "merge"


def cmd_update(args, root):
    refuse_generated(args.name)
    source = root / TEMP_FILE
    if not source.exists():
        raise SystemExit(f"{TEMP_FILE} not found. Create it with: python3 -m appads init")
    try:
        path = resolve(root, args.name, args.yes)
        if path is None:
            print("Cancelled.")
            return 1
        if path.stem in RAW:   # copied as-is, the mode does not matter
            update_raw(path, [source.read_text(encoding="utf-8", errors="replace")], args.yes)
            return 0

        incoming = read_file(source, source.name)
        if incoming.empty:
            raise SystemExit(f"No valid lines in {TEMP_FILE}.")
        mode = "force" if args.force else "merge" if args.merge else ask_mode(path, args.yes)
        status = update_network(root, path, incoming, mode, args.yes)
    except Quit:
        status = "declined"
    if status == "updated":
        print(f"Updated {path.relative_to(root)}.")
    elif status == "declined":
        print("Cancelled.")
    return 1 if status == "declined" else 0


def cmd_remove(args, root):
    refuse_generated(args.name)
    heads = load_heads(root)
    try:
        path = match_network(root, args.name)
        if path is None:
            # the file may be deleted by hand already: offer to clean networks.json only
            names = [n for n in heads if normalize(n) == normalize(args.name)]
            if names:
                if not confirm(f"{names[0]} has no file. Remove it from {HEADS_FILE}?", args.yes):
                    print("Cancelled.")
                    return 1
                heads.pop(names[0])
                save_heads(root, heads)
                print(f"Removed {names[0]} from {HEADS_FILE}.")
                return 0
            path = resolve(root, args.name, args.yes, allow_create=False)
            if path is None:
                print("Cancelled.")
                return 1
        lines = len(read_file(path).lines)
        if not confirm(f"Delete {path.relative_to(root)} ({lines} lines) and its entry in {HEADS_FILE}?", args.yes):
            print("Cancelled.")
            return 1
    except Quit:
        print("Cancelled.")
        return 1

    path.unlink()
    if heads.pop(path.stem, None) is not None:
        save_heads(root, heads)
    print(f"Deleted {path.relative_to(root)}.")
    if path.parent.name == DIRS["n"] and path.stem in RELEASE_NETWORKS:
        print("  Note: remove it from RELEASE_NETWORKS in appads/config.py, otherwise release stops.")
    return 0


def reorder(root, paths, yes):
    """Sorts the given files by the current rules; asks once for all of them."""
    heads = load_heads(root)
    pending, no_heads = [], []
    for path in paths:
        if path.stem not in heads:
            no_heads.append(path.stem)
        parsed = read_file(path)
        variables, records = build(parsed, parsed, heads.get(path.stem, []), "merge")
        if to_lines(variables, records) != parsed.lines:
            pending.append((path, parsed, variables, records))

    if no_heads:
        print(f"Not in {HEADS_FILE} (sorted without head domain): {', '.join(no_heads)}")
    if not pending:
        print("All files are in order.")
        return 0
    for path, *_ in pending:
        print(f"  {path.relative_to(root)}")
    if not confirm(f"Reorder {len(pending)} file(s)?", yes):
        print("Cancelled.")
        return 1
    for path, parsed, variables, records in pending:
        write_file(path, variables, records, header=parsed.header)
    print(f"Reordered {len(pending)} file(s).")
    return 0


def sortable(path):
    if path.stem in GENERATED | RAW:
        warn(f"{path.stem} is not sorted (built by release or copied as-is)")
        return False
    return True


def cmd_sort(args, root):
    try:
        if args.names:
            for name in args.names:
                refuse_generated(name)
            paths = [resolve(root, name, args.yes, allow_create=False) for name in args.names]
            paths = [p for p in paths if p is not None and sortable(p)]
        else:
            paths = [p for p in all_files(root) if p.stem not in GENERATED | RAW]
        return reorder(root, paths, args.yes)
    except Quit:
        print("Cancelled.")
        return 1


def cmd_head(args, root):
    refuse_generated(args.name)
    try:
        path = resolve(root, args.name, allow_create=False)
        if path is None or not sortable(path):
            return 1
        current = load_heads(root).get(path.stem)
        if not args.domains and not args.clear:
            shown = ", ".join(current) if current else ("none" if current == [] else f"not in {HEADS_FILE}")
            print(f"{path.stem}: {shown}")
            return 0
        domains = [] if args.clear else parse_domains(" ".join(args.domains))
        set_head(root, path.stem, domains)
        print(f"{path.stem}: head domain set to {', '.join(domains) or 'none'}")
        return reorder(root, [path], args.yes)
    except Quit:
        print("Cancelled.")
        return 1


def cmd_init(args, root):
    """Working files that are not committed: TempUpdate.txt, GoogleDrive/, Tables/."""
    temp, folders = root / TEMP_FILE, [root / DRIVE_DIR, root / TABLES_DIR]

    if args.clean:
        filled = [f for f in folders if f.is_dir() and any(f.iterdir())]
        if temp.exists() and temp.read_text(encoding="utf-8").strip():
            filled.insert(0, temp)
        if not filled:
            print("Nothing to clean.")
        else:
            for path in filled:
                count = "" if path.is_file() else f" ({sum(1 for _ in path.rglob('*') if _.is_file())} files)"
                print(f"  {path.relative_to(root)}{count}")
            try:
                if not confirm("Empty these?", args.yes):
                    print("Cancelled.")
                    return 1
            except Quit:
                print("Cancelled.")
                return 1
            for path in filled:
                if path.is_file():
                    path.write_text("", encoding="utf-8")
                    continue
                for item in path.iterdir():        # the folder itself stays
                    shutil.rmtree(item) if item.is_dir() else item.unlink()
            print("Cleaned.")

    for folder in folders:
        if not folder.is_dir():
            folder.mkdir()
            print(f"Created {folder.name}/")
    if not temp.exists():
        temp.write_text("", encoding="utf-8")
        print(f"Created {TEMP_FILE}")

    gitignore = root / ".gitignore"
    ignored = gitignore.read_text(encoding="utf-8").split() if gitignore.exists() else []
    missing = [n for n in (TEMP_FILE, f"{DRIVE_DIR}/", f"{TABLES_DIR}/")
               if n not in ignored and n.rstrip("/") not in ignored]
    if missing:
        warn(f"Not in .gitignore: {', '.join(missing)}")
    print("Ready.")
    return 0