from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from . import model
from .cli import ROOT
from .common import Quit, all_files, input_folder, is_generated
from .config import CERT_FILE, TABLES_DIR
from .model import CERTS, parse_text
from .names import match_network, pick_network
from .table import read_tables

REPORT_FILE = "remove-check.tsv"

ONLY_HERE = "in network only"
MISSING_ELSEWHERE = "network missing, in other networks"
ABSENT_ELSEWHERE = "not in network, in other networks"
HERE_AND_ELSEWHERE = "in network and in other networks"
NOWHERE = "not found anywhere"
REPORTED = [MISSING_ELSEWHERE, ABSENT_ELSEWHERE, HERE_AND_ELSEWHERE, NOWHERE]   # order in the report


def build_index(root):
    """{line: [network names that contain it]} over every network file, quietly."""
    index = {}
    loud, model.warn = model.warn, lambda *a, **k: None      # broken lines in the files are not our topic here
    try:
        for path in all_files(root):
            if is_generated(path.stem):
                continue
            parsed = parse_text(path.read_text(encoding="utf-8", errors="replace"), path.stem)
            for entry in parsed.records + parsed.variables:
                index.setdefault(entry, []).append(path.stem)
    finally:
        model.warn = loud
    return index


def resolve_names(root, groups, yes):
    """[(names as written, network or None, entries)]; different spellings of one network are merged.
    Unknown names are asked (an empty answer = the network does not exist)."""
    merged = {}
    for name, entries in groups.values():
        name = name.strip()
        path = match_network(root, name)
        if path is None and not yes:
            print(f"\nChoose the network for '{name}'; an empty answer means it does not exist.")
            path = pick_network(root, name, allow_create=False)
        network = path.stem if path is not None else None
        if network and network.lower() != name.lower():
            print(f"Using {network} for '{name}'.")
        names, collected = merged.setdefault(network or f"?{name.lower()}", ([], []))
        names.append(name)
        collected.extend(entries)
    return [(", ".join(names), None if key.startswith("?") else key, entries)
            for key, (names, entries) in merged.items()]


def classify(network, entry, index):
    holders = index.get(entry, [])
    others = [n for n in holders if n != network]
    here = network is not None and network in holders
    if here:
        return (HERE_AND_ELSEWHERE if others else ONLY_HERE), others
    if others:
        return (ABSENT_ELSEWHERE if network else MISSING_ELSEWHERE), others
    return NOWHERE, []


def run(folder, output, yes, root):
    CERTS.load(root / CERT_FILE)
    CERTS.learn = False                     # a check must not change CertificationIds.json
    groups = read_tables(input_folder(folder, root))
    try:
        resolved = resolve_names(root, groups, yes)
    except Quit:
        print("Cancelled.")
        return 1
    index = build_index(root)

    rows, counts = [], {status: 0 for status in [ONLY_HERE] + REPORTED}
    for name, network, entries in resolved:
        for entry in dict.fromkeys(entries):          # same line twice in the tables: once
            status, others = classify(network, entry, index)
            counts[status] += 1
            if status != ONLY_HERE:
                rows.append((name, network or "-", entry.to_line(), status, ", ".join(others)))

    rows.sort(key=lambda r: (REPORTED.index(r[3]), r[1].lower(), r[0].lower(), r[2]))
    path = Path(output) if Path(output).is_absolute() else root / output
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["table name", "network", "line", "status", "also in"])
        writer.writerows(rows)

    print("\nSummary (nothing was changed):")
    for status, count in counts.items():
        if count:
            print(f"  {status:<36} {count:>4}")
    try:
        shown = path.relative_to(root)
    except ValueError:
        shown = path
    print(f"Report: {shown} ({len(rows)} lines)")
    return 0


def main(argv=None, root=None):
    parser = argparse.ArgumentParser(prog="python3 -m appads.check",
                                     description="Check removal tables without changing anything.")
    parser.add_argument("folder", nargs="?", default=TABLES_DIR, help=f"Folder with tables (default: {TABLES_DIR}).")
    parser.add_argument("-o", "--output", default=REPORT_FILE, help=f"Report file (default: {REPORT_FILE}).")
    parser.add_argument("-y", "--yes", action="store_true", help="Do not ask about unknown names (= network missing).")
    args = parser.parse_args(argv)
    try:
        return run(args.folder, args.output, args.yes, root or ROOT)
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
