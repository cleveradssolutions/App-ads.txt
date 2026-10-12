from __future__ import annotations

import json
import re
from pathlib import Path

from .config import EXCHANGE_DIR, GENERATED, HEADS_FILE, MERGE, NETWORKS_DIR
from .model import DIRECT, DOMAIN_RE, build, read_file, to_lines, today, warn, write_file, write_lines

DIRS = {"n": NETWORKS_DIR, "e": EXCHANGE_DIR}   # answer letter -> folder, used when creating a network


class Quit(Exception):
    """The user typed q: stop the whole run (changes applied so far are kept)."""


# ---------------------------------------------------------------- questions

def ask(message):
    try:
        return input(message).strip()
    except EOFError:   # Ctrl+D or closed input: same as q
        print()
        raise Quit


def confirm(message, yes=False):
    """y/n question; q raises Quit; -y answers yes."""
    if yes:
        return True
    while True:
        answer = ask(f"{message} [y/n/q]: ").lower()
        if answer == "q":
            raise Quit
        if answer in ("y", "n"):
            return answer == "y"


# ---------------------------------------------------------------- files and names

def normalize(name):
    """For comparing names: 'MonetriX-EX' -> 'monetrixex', ' Wecallmedia.' -> 'wecallmedia'."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def all_files(root):
    """Every network file in Networks/ and InternalExchange/, sorted by name."""
    return [p for d in DIRS.values() for p in sorted((root / d).glob("*.txt"), key=lambda p: p.name.lower())]


def find_files(root, query):
    """Exact name match, otherwise all files whose name contains the query."""
    files = all_files(root)
    q = normalize(query)
    exact = [p for p in files if normalize(p.stem) == q]
    return exact or [p for p in files if q and q in normalize(p.stem)]


def is_generated(name):
    return normalize(name) in {normalize(n) for n in GENERATED}


def input_folder(value, root):
    """Folder given on the command line: relative to the current folder, or to the repository."""
    folder = Path(value)
    if not folder.is_absolute():
        folder = Path.cwd() / folder if (Path.cwd() / folder).exists() else root / folder
    if not folder.is_dir():
        raise SystemExit(f"Folder not found: {folder}. Create the working folders with: python3 -m appads init")
    return folder


# ---------------------------------------------------------------- networks.json (head domains)

def load_heads(root):
    """{"Streamix-tv": ["streamix-tv.com"], "Madstream": []}; [] = the network has no head domain."""
    path = root / HEADS_FILE
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_heads(root, heads):
    data = {name: heads[name] for name in sorted(heads, key=str.lower)}
    (root / HEADS_FILE).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def set_head(root, name, domains):
    heads = load_heads(root)
    heads[name] = domains
    save_heads(root, heads)


def parse_domains(text):
    domains = [d.strip().lower() for d in text.replace(",", " ").split()]
    bad = [d for d in domains if not DOMAIN_RE.match(d)]
    if bad:
        raise SystemExit(f"Invalid domain: {', '.join(bad)}")
    return list(dict.fromkeys(domains))


def ask_head(name, incoming):
    """Head domain of a network that is not in networks.json yet; suggestions come from the new lines."""
    suggestions = [v.value for v in incoming.variables]
    suggestions += [r.domain for r in incoming.records if r.relation == DIRECT]
    suggestions = list(dict.fromkeys(suggestions))
    print(f"Head domain for {name} is not set.")
    for i, domain in enumerate(suggestions, 1):
        print(f"  {i}) {domain}")
    while True:
        answer = ask("Number or domain (empty = network has no head domain): ")
        if answer.isdigit() and 1 <= int(answer) <= len(suggestions):
            return [suggestions[int(answer) - 1]]
        try:
            return parse_domains(answer) if answer else []
        except SystemExit as error:
            print(f"  {error}")


def check_head(name, heads, records):
    """Warns when there is no head DIRECT line to put on top of the file."""
    if not heads:
        problem = f"{name} has no head domain in {HEADS_FILE}"
    elif not any(r.relation == DIRECT and r.domain in heads for r in records):
        problem = f"{name} has no DIRECT line of its head domain ({', '.join(heads)})"
    else:
        return
    warn(f"{problem}; all DIRECT lines are sorted alphabetically.\n"
         f"      Check the file and set the head domain: python3 -m appads head {name} <domain>")


# ---------------------------------------------------------------- updating one network

def default_mode(name):
    return "merge" if name in MERGE else "force"


def show_changes(root, path, current, variables, records, heads, mode):
    """Prints the new file with [+]/[-] marks. Returns (variables, records), or None if nothing changes."""
    new_lines = to_lines(variables, records)
    print(f"Update {path.relative_to(root)} ({mode}), head: {', '.join(heads) or '-'}")
    check_head(path.stem, heads, records)
    if new_lines == current.lines:
        print("No changes.")
        return None
    old_set, new_set = set(current.lines), set(new_lines)
    for line in new_lines:
        print(f"  {'[+]' if line not in old_set else '   '} {line}")
    for line in current.lines:
        if line not in new_set:
            print(f"  [-] {line}")
    print(f"  Result: {len(new_lines)} lines (was {len(current.lines)})")
    return variables, records


def update_network(root, path, incoming, mode, yes=False):
    """The flow every command uses: head domain -> show changes -> confirm -> write -> networks.json.

    mode: force | merge | remove (see model.build)
    The head domain comes from networks.json; a network missing there is asked for (unless -y
    or remove). networks.json is saved only when the update is applied or nothing changes.
    Returns "updated", "unchanged" or "declined".
    """
    name = path.stem
    known = load_heads(root)
    save = name not in known and not yes and mode != "remove"
    heads = ask_head(name, incoming) if save else known.get(name, [])

    current = read_file(path)
    plan = show_changes(root, path, current, *build(current, incoming, heads, mode), heads, mode)
    if plan is not None:
        if not confirm(f"{'Remove lines from' if mode == 'remove' else 'Update'} {name}?", yes):
            return "declined"
        write_file(path, *plan)
    if save:
        set_head(root, name, heads)
    return "updated" if plan is not None else "unchanged"


def raw_lines(texts):
    """Lines of a RAW network as they are (only empty lines and our old header are dropped)."""
    return [l.rstrip() for t in texts for l in t.splitlines() if l.strip() and not l.strip().startswith("#===")]


def update_raw(path, texts, yes=False):
    """RAW networks (Gadsme): the file content is replaced as-is, only the header is ours."""
    lines = raw_lines(texts)
    current = [l.rstrip() for l in path.read_text(encoding="utf-8").splitlines()[1:]] if path.exists() else []
    print(f"Replace {path.name} as-is (no sorting): {len(lines)} lines (was {len(current)})")
    if lines == current:
        print("No changes.")
        return "unchanged"
    if not confirm(f"Replace {path.stem}?", yes):
        return "declined"
    write_lines(path, f"#=== {path.stem} {today()}", lines)
    return "updated"


def print_summary(result, extra=()):
    """result: {"updated": [names], ...}; empty groups are not shown."""
    print("\nSummary:")
    for key, names in result.items():
        if names:
            print(f"  {key:<10} {len(names):>3}: {', '.join(names)}")
    for line in extra:
        print(f"  {line}")