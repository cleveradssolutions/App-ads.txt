from __future__ import annotations

import json

from .common import Quit, ask
from .config import (DSP_POOL, EXCHANGE_DIR, GAMES_ONLY, NETWORKS_DIR, PARTNER_EXCLUDE, RELEASE_NETWORKS,
                     RELEASE_TARGETS)
from .model import Record, combine, parse_line, read_file, to_lines, today, warn, write_lines


# ---------------------------------------------------------------- 1. exchanges

def exchange_lines(parsed):
    """Order of the generated files (as in Combine.py): variables, then records by domain/relation/id."""
    variables = sorted(parsed.variables, key=lambda v: (v.name, v.value))
    records = sorted(parsed.records, key=lambda r: (r.domain, r.relation, r.account_id))
    return to_lines(variables, records)


def build_exchange(root, name, sources):
    """Collects the given InternalExchange files into Networks/<name>.txt."""
    parts = []
    for source in sources:
        path = root / EXCHANGE_DIR / f"{source}.txt"
        if path.exists():
            parts.append(read_file(path))
        else:
            warn(f"{name}: {path.relative_to(root)} not found, skipped")
    incoming = combine(parts)
    path = root / NETWORKS_DIR / f"{name}.txt"
    current = read_file(path)

    replace = exchange_lines(incoming)
    if replace == current.lines:
        print(f"{name}: no changes ({len(replace)} lines from {len(parts)} exchanges)")
        return
    added = [l for l in replace if l not in set(current.lines)]
    obsolete = [l for l in current.lines if l not in set(replace)]
    print(f"\nUpdate {name} from {len(parts)} exchanges:")
    for line in added:
        print(f"  [+] {line}")
    for line in obsolete:
        print(f"  [-] {line}   (removed only with f)")

    while True:
        answer = ask("[y] add new lines / [f] replace (remove obsolete) / [n] skip / [q] quit: ").lower()
        if answer == "q":
            raise Quit
        if answer in ("y", "f", "n"):
            break
    if answer == "n":
        print(f"{name}: skipped")
        return
    lines = replace if answer == "f" else exchange_lines(combine([current, incoming]))
    write_lines(path, f"#=== {name} {today()}", lines)
    print(f"{name}: {len(lines)} lines (was {len(current.lines)})")


def cas_pool(root):
    """Every exchange that is not a DSP and not games-only goes to CASExchange."""
    skip = set(DSP_POOL) | set(GAMES_ONLY)
    return sorted((p.stem for p in (root / EXCHANGE_DIR).glob("*.txt") if p.stem not in skip), key=str.lower)


# ---------------------------------------------------------------- 2. the final file

def final_lines(root, partner):
    """Lines of RELEASE_NETWORKS without duplicates. Returns (lines, number of entries)."""
    out, seen = [], set()   # seen: records by identity, variables and comments by text
    for name in RELEASE_NETWORKS:
        if partner and name == "CASExchange":
            continue
        text = (root / NETWORKS_DIR / f"{name}.txt").read_text(encoding="utf-8", errors="replace")
        for number, raw in enumerate(text.splitlines(), 1):
            if not raw.strip() or raw.startswith("/"):
                continue
            if raw.startswith("#"):
                key = line = raw
            else:
                entry = parse_line(raw, f"{name}:{number}")
                if entry is None:
                    continue
                if partner and isinstance(entry, Record) and PARTNER_EXCLUDE in entry.domain:
                    continue
                key = entry if isinstance(entry, Record) else entry.to_line()
                line = entry.to_line()
            if key not in seen:
                seen.add(key)
                out.append(line)
    return out, len(out)


def games_only_lines(root, written):
    """GAMES_ONLY files as-is, skipping lines already in the file."""
    out = []
    for name in GAMES_ONLY:
        path = root / EXCHANGE_DIR / f"{name}.txt"
        if not path.exists():
            warn(f"{path.relative_to(root)} not found, skipped")
            continue
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if raw.strip() and raw not in written:
                written.add(raw)
                out.append(raw)
    return out


def run(args, root):
    partner = args.target == "partner"
    file_name, head_lines = RELEASE_TARGETS[args.target]

    extra = [p.stem for p in (root / NETWORKS_DIR).glob("*.txt") if p.stem not in RELEASE_NETWORKS]
    if extra:
        warn(f"Not in RELEASE_NETWORKS, not released: {', '.join(sorted(extra, key=str.lower))}")
    missing = [n for n in RELEASE_NETWORKS if not (root / NETWORKS_DIR / f"{n}.txt").exists()]
    if missing:
        raise SystemExit(f"Missing files in {NETWORKS_DIR}/: {', '.join(missing)} (see RELEASE_NETWORKS in config.py)")

    try:
        build_exchange(root, "DSPExchange", DSP_POOL)
        if not partner:
            build_exchange(root, "CASExchange", cas_pool(root))
    except Quit:
        print(f"Cancelled, {file_name} is not built.")
        return 1

    lines, entries = final_lines(root, partner)
    out = head_lines + lines
    if args.target in ("games", "partner"):
        out += games_only_lines(root, set(out))

    path = root / file_name
    was = max(len(path.read_text(encoding="utf-8").splitlines()) - 1, 0) if path.exists() else 0
    write_lines(path, f"# CAS.ai Updated {today()}", out)
    (root / "Shield.json").write_text(json.dumps(
        {"schemaVersion": 1, "label": "app-ads.txt", "message": today(), "color": "orange"}), encoding="utf-8")
    print(f"\nCombined {file_name} with {entries} (was {was}) inventories for {len(RELEASE_NETWORKS)} networks.")
    return 0