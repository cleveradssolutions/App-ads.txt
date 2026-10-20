from __future__ import annotations

import difflib

from .common import DIRS, Quit, all_files, ask, find_files, is_generated, normalize
from .config import RELEASE_NETWORKS
from .model import warn


def networks(root):
    """Networks that can be chosen (files built by release are excluded)."""
    return [p for p in all_files(root) if not is_generated(p.stem)]


def clean_name(name):
    """Name written as a domain: ' benefit.media' -> 'benefit', 'Streamix-tv.com' -> 'Streamix-tv'."""
    name = name.strip().strip(".")
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return name.strip()


def match_network(root, name):
    """Exact match (also without a domain ending), otherwise a unique partial match. None if unsure."""
    keys = [normalize(name), normalize(clean_name(name))]
    for path in networks(root):
        if normalize(path.stem) in keys:
            return path
    for key in dict.fromkeys(keys):
        hits = [p for p in find_files(root, key) if not is_generated(p.stem)]
        if len(hits) == 1:
            return hits[0]
    return None


def resolve(root, name, yes=False, allow_create=True):
    """The network for a name; asks the user when unsure. None = skipped."""
    path = match_network(root, name)
    if path is not None:
        if normalize(path.stem) != normalize(name):
            print(f"Using {path.stem} for '{name.strip()}'.")
        return path
    return pick_network(root, name, yes, allow_create)


# ---------------------------------------------------------------- asking the user

def print_columns(paths, columns=3, width=28):
    rows = (len(paths) + columns - 1) // columns
    for row in range(rows):
        line = ""
        for col in range(columns):
            i = col * rows + row
            if i < len(paths):
                line += f"{i + 1:3}: {paths[i].stem:<{width}}"
        print(line.rstrip())


def similar(paths, name, limit=6):
    """Indexes of networks that contain the name, then of the closest spellings."""
    q = normalize(clean_name(name)) or normalize(name)
    keys = {normalize(p.stem): i for i, p in enumerate(paths)}
    partial = [i for k, i in keys.items() if q and (q in k or k in q)]
    close = [keys[m] for m in difflib.get_close_matches(q, list(keys), n=limit, cutoff=0.5)]
    return list(dict.fromkeys(partial + close[:max(limit - len(partial), 2)]))


def choose(paths, root):
    """Several files match a typed name: pick one by number."""
    if len(paths) == 1:
        return paths[0]
    for i, path in enumerate(paths, 1):
        print(f"  {i}) {path.relative_to(root)}")
    answer = ask("Choose a number (empty to cancel): ")
    if answer.isdigit() and 1 <= int(answer) <= len(paths):
        return paths[int(answer) - 1]
    return None


def create_network(root, name):
    """Asks for the folder and the file name of a new network. Returns the path or None (back)."""
    default = clean_name(name)
    while True:
        answer = ask(f"Create '{default}' in [n] Networks / [e] InternalExchange (empty = back): ").lower()
        if not answer:
            return None
        if answer in DIRS:
            break
    new_name = ask(f"File name [{default}]: ") or default
    existing = [p for p in all_files(root) if normalize(p.stem) == normalize(new_name)]
    if existing:
        print(f"  {existing[0].stem} already exists, using it.")
        return existing[0]
    path = root / DIRS[answer] / f"{new_name}.txt"
    print(f"  New network: {path.relative_to(root)} (the file is created when the update is applied)")
    if answer == "n" and new_name not in RELEASE_NETWORKS:
        print("  Note: add it to RELEASE_NETWORKS in appads/config.py to include it in the release.")
    return path


def pick_network(root, name, yes=False, allow_create=True):
    """The network was not found: choose by index or (part of) name, or create one. None = skip."""
    if yes:
        warn(f"'{name}': network not found, skipped (-y)")
        return None
    paths = networks(root)
    warn(f"'{name}': network not found")
    print_columns(paths)
    near = similar(paths, name)
    if near:
        print("  Similar: " + ", ".join(f"{i + 1}) {paths[i].stem}" for i in near))
    options = "index or name" + (", c = create new" if allow_create else "") + ", empty = skip, q = quit"
    while True:
        answer = ask(f"Network ({options}): ")
        if not answer:
            return None
        if answer.lower() == "q":
            raise Quit
        if allow_create and answer.lower() == "c":
            path = create_network(root, name)
            if path is not None:
                return path
            continue
        if answer.isdigit():
            if 1 <= int(answer) <= len(paths):
                return paths[int(answer) - 1]
            print("  No such index.")
            continue
        hits = [p for p in find_files(root, answer) if not is_generated(p.stem)]
        if not hits:
            print("  Not found, try again.")
            continue
        path = choose(hits, root)
        if path is not None:
            return path