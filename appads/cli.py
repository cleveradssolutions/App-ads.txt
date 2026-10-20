from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from .config import CERT_FILE, DRIVE_DIR, HEADS_FILE, TABLES_DIR, TEMP_FILE
from .model import CERTS

ROOT = Path(__file__).resolve().parent.parent   # the repository: the folder that contains appads/


def command(target):
    """'manual:cmd_update' -> calls appads.manual.cmd_update(args, root); modules load on demand."""
    module, func = target.split(":")

    def run(args, root):
        return getattr(importlib.import_module(f"appads.{module}"), func)(args, root)
    return run


def build_parser():
    parser = argparse.ArgumentParser(prog="python3 -m appads", description="app-ads.txt maintenance.")
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    def add(name, target, text):
        p = sub.add_parser(name, help=text, description=text)
        p.set_defaults(func=command(target))
        return p

    def yes(p, text="Do not ask for confirmation."):
        p.add_argument("-y", "--yes", action="store_true", help=text)

    p = add("update", "manual:cmd_update", f"Update a network from {TEMP_FILE}; without -f/-m/-r the mode is asked.")
    p.add_argument("name", help="Network name or part of it.")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("-f", "--force", action="store_true", help="Remove lines missing from the update.")
    mode.add_argument("-m", "--merge", action="store_true", help="Keep existing lines, only add new ones.")
    mode.add_argument("-r", "--remove", action="store_true",
                      help="Remove the lines of TempUpdate.txt from the network (an emptied network is deleted).")
    yes(p, "Do not ask for confirmation (the mode must be given).")

    p = add("init", "manual:cmd_init", f"Create {TEMP_FILE}, {DRIVE_DIR}/ and {TABLES_DIR}/ if missing.")
    p.add_argument("--clean", action="store_true", help="Empty them first (after the update is done).")
    yes(p)

    p = add("remove", "manual:cmd_remove", f"Delete a network file and its entry in {HEADS_FILE}.")
    p.add_argument("name", help="Network name or part of it.")
    yes(p)

    p = add("sort", "manual:cmd_sort", "Reorder network files (header dates are kept).")
    p.add_argument("names", nargs="*", help="Networks to sort (default: all).")
    yes(p)

    p = add("head", "manual:cmd_head", "Show or set the head domain(s) of a network, then reorder its file.")
    p.add_argument("name", help="Network name or part of it.")
    p.add_argument("domains", nargs="*", help="New head domain(s); without them the current ones are shown.")
    p.add_argument("--clear", action="store_true", help="The network has no head domain.")
    yes(p)

    p = add("drive", "drive:run", "Update networks from files downloaded from Google Drive.")
    p.add_argument("folder", nargs="?", default=DRIVE_DIR, help=f"Folder with .txt/.docx files (default: {DRIVE_DIR}).")
    yes(p, "Apply without asking (unknown names are skipped).")

    p = add("table", "table:run", "Add or remove lines listed in tables (.tsv/.csv).")
    tsub = p.add_subparsers(dest="action", required=True, metavar="action")
    for action, text in (("update", "Add lines from the tables to the networks."),
                         ("remove", "Remove lines listed in the tables from the networks.")):
        t = tsub.add_parser(action, help=text, description=text)
        t.add_argument("folder", nargs="?", default=TABLES_DIR, help=f"Folder with tables (default: {TABLES_DIR}).")
        yes(t, "Apply without asking (unknown names are skipped).")

    p = add("release", "release:run", "Build a final app-ads file.")
    rsub = p.add_subparsers(dest="target", required=True, metavar="target")
    for target, text in (("main", "app-ads.txt for the public repository."),
                         ("games", "app-ads-games.txt: main + games-only partners."),
                         ("partner", "app-ads-partner.txt: without CASExchange and cas.ai domains.")):
        rsub.add_parser(target, help=text, description=text)
    return parser


def main(argv=None, root=None):
    args = build_parser().parse_args(argv)
    root = root or ROOT
    CERTS.load(root / CERT_FILE)
    try:
        return args.func(args, root)
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130
    finally:
        CERTS.save()   # certification ids learned from new lines (as Combine.py did)


if __name__ == "__main__":
    sys.exit(main())