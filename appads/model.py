from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from .config import BANNED_DOMAINS, VARIABLES

DIRECT, RESELLER = "DIRECT", "RESELLER"

DOMAIN_RE = re.compile(r"^([a-z0-9_-]{1,63}\.)+[a-z]{2,9}$")
ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")   # letters, digits, dot, underscore, dash
CERT_RE = re.compile(r"^[a-z0-9]+$")


def warn(message, line=""):
    """Yellow warning; the offending line (if any) is printed below it."""
    text = f"   Warning: {message}"
    if line.strip():
        text += f"\n      {line.strip()}"
    print(f"\033[93m{text}\033[0m")


def today():
    return date.today().strftime("%b %d, %Y")


# ---------------------------------------------------------------- data

@dataclass(frozen=True)
class Record:
    """Two records are the same line when domain, account id and relation match;
    the certification id is not part of the identity."""
    domain: str
    account_id: str
    relation: str
    cert: Optional[str] = field(default=None, compare=False)

    def to_line(self):
        parts = [self.domain, self.account_id, self.relation]
        if self.cert:
            parts.append(self.cert)
        return ", ".join(parts)


@dataclass(frozen=True)
class Variable:
    name: str
    value: str

    def to_line(self):
        return f"{self.name}={self.value}"


@dataclass
class Parsed:
    """Content of one file (or of several files combined)."""
    variables: list = field(default_factory=list)
    records: list = field(default_factory=list)  # file order, without duplicates
    lines: list = field(default_factory=list)    # non-comment lines exactly as written (to detect changes)
    header: Optional[str] = None                 # "#=== Name date" first line, if any

    @property
    def empty(self):
        return not self.variables and not self.records


def combine(parts):
    """Merges several Parsed into one, without duplicates (a line with a certification id wins)."""
    records, variables = {}, {}
    for part in parts:
        for v in part.variables:
            variables.setdefault(v, v)
        for r in part.records:
            if r not in records or (r.cert and not records[r].cert):
                records[r] = r
    return Parsed(variables=list(variables), records=list(records))


# ---------------------------------------------------------------- certification ids

class Certs:
    """CertificationIds.json, with the rules of Combine.py:
      invalid id, domain known    -> replaced with the known id
      invalid id, domain unknown  -> dropped
      domain known with ""        -> id dropped (this domain must not have one)
      valid id of unknown domain  -> learned and saved to the file
      valid id differs from known -> kept as written
    """

    def __init__(self):
        self.path = None
        self.known = {}
        self.changed = False
        self.learn = True    # False: unknown valid ids are kept but not saved (table remove)

    def load(self, path: Path):
        self.path = path
        self.known = json.loads(path.read_text(encoding="utf-8") or "{}") if path.exists() else {}
        self.changed = False

    def save(self):
        if self.path is not None and self.changed:
            self.path.write_text(json.dumps(self.known, indent=2, sort_keys=True), encoding="utf-8")
            self.changed = False

    def resolve(self, domain, cert, source, raw):
        if not (len(cert) in (9, 16) and CERT_RE.match(cert)):
            if domain in self.known:
                warn(f"{source}: invalid certification id, replaced with the known one", raw)
                return self.known[domain] or None
            warn(f"{source}: invalid certification id, dropped", raw)
            return None
        if domain in self.known:
            if not self.known[domain]:
                warn(f"{source}: {domain} must not have a certification id, dropped", raw)
                return None
            return cert
        if not self.learn:
            return cert
        warn(f"{source}: new certification id {cert} for {domain} saved to {self.path.name if self.path else 'memory'}")
        self.known[domain] = cert
        self.changed = True
        return cert


CERTS = Certs()   # loaded by cli.main() before a command, saved after it


# ---------------------------------------------------------------- parsing

def parse_line(raw, source):
    """Returns Record, Variable or None (empty line, comment, or invalid line - reported)."""
    text = raw.replace("﻿", "").split("#", 1)[0].strip()
    if not text or text.startswith("/"):
        return None

    if "=" in text:
        name, value = (part.strip().lower() for part in text.split("=", 1))
        if name not in VARIABLES:
            warn(f"{source}: unsupported variable skipped", raw)
        elif not DOMAIN_RE.match(value):
            warn(f"{source}: invalid domain in variable, skipped", raw)
        else:
            return Variable(name, value)
        return None

    fields = [f.strip() for f in text.split(",")]
    if len(fields) not in (3, 4):
        warn(f"{source}: expected 3 or 4 fields, skipped", raw)
        return None
    domain, account_id, relation = fields[0].lower(), fields[1], fields[2].upper()
    if not DOMAIN_RE.match(domain):
        warn(f"{source}: invalid domain, skipped", raw)
    elif domain in BANNED_DOMAINS:
        warn(f"{source}: banned domain, skipped", raw)
    elif not ID_RE.match(account_id):
        warn(f"{source}: invalid publisher id, skipped", raw)
    elif relation not in (DIRECT, RESELLER):
        warn(f"{source}: relation must be DIRECT or RESELLER, skipped", raw)
    else:
        cert = fields[3].lower() if len(fields) == 4 and fields[3] else None
        if cert:
            cert = CERTS.resolve(domain, cert, source, raw)
        return Record(domain, account_id, relation, cert)
    return None


def parse_text(text, source) -> Parsed:
    parsed = Parsed()
    records, variables = {}, {}
    for number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.replace("﻿", "").strip()
        if number == 1 and stripped.startswith("#==="):
            parsed.header = stripped
        if stripped and not stripped.startswith(("#", "/")):
            parsed.lines.append(stripped)
        entry = parse_line(raw, source)
        if isinstance(entry, Variable):
            variables.setdefault(entry, entry)
        elif isinstance(entry, Record):
            if entry in records:
                warn(f"{source}: duplicate line skipped", raw)
            else:
                records[entry] = entry
    parsed.variables, parsed.records = list(variables), list(records)
    return parsed


def read_file(path: Path, source=None) -> Parsed:
    """A missing file reads as empty (a new network)."""
    if not path.exists():
        return Parsed()
    return parse_text(path.read_text(encoding="utf-8", errors="replace"), source or path.stem)


# ---------------------------------------------------------------- building a file

def order(records, heads):
    """With head domains: head DIRECT, head RESELLER, then the rest alphabetically.
    Without head domains: all DIRECT alphabetically, then the rest alphabetically."""
    rank = {domain: i for i, domain in enumerate(heads)}

    def key(r):
        if rank:
            if r.domain in rank:
                return (0, r.relation != DIRECT, rank[r.domain], r.account_id)
        elif r.relation == DIRECT:
            return (0, 0, r.domain, r.account_id)
        return (1, r.domain, r.relation, r.account_id)

    return sorted(records, key=key)


def build(current: Parsed, incoming: Parsed, heads, mode):
    """Returns (variables, records) of the updated file. Modes:
      force:  incoming lines replace the file, but existing DIRECT lines and head-domain
              lines are always kept (sources such as Google Drive often have only a part of them)
      merge:  incoming lines are added, existing lines are kept
      remove: incoming lines are removed from the file
    """
    old = {r: r for r in current.records}

    if mode == "remove":
        existing = set(old) | set(current.variables)
        for entry in incoming.variables + incoming.records:
            if entry not in existing:
                warn("line to remove is not in the file", entry.to_line())
            elif isinstance(entry, Record) and entry.relation == DIRECT and entry.domain in heads:
                warn("the DIRECT line of the head domain will be removed", entry.to_line())
        drop = set(incoming.records) | set(incoming.variables)
        records = {r: r for r in old if r not in drop}
        variables = [v for v in current.variables if v not in drop]
    else:
        new = {}
        for r in incoming.records:
            if not r.cert and r in old and old[r].cert:   # the update lost the certification id: keep it
                r = old[r]
            new[r] = r
        if mode == "merge":
            records = {**old, **new}
            variables = list(dict.fromkeys(current.variables + incoming.variables))
        else:
            records = dict(new)
            kept = [r for r in old if r not in new and (r.relation == DIRECT or r.domain in heads)]
            if kept:
                print(f"  Kept {len(kept)} existing DIRECT/head line(s) missing from the update "
                      f"(remove them with `table remove` if needed):")
                for r in order(kept, heads):
                    print(f"    [keep] {r.to_line()}")
                records.update({r: r for r in kept})
            variables = incoming.variables or current.variables

    variables = sorted(variables, key=lambda v: (v.name, v.value))
    return variables, order(records.values(), heads)


def to_lines(variables, records):
    return [v.to_line() for v in variables] + [r.to_line() for r in records]


def write_lines(path: Path, header, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([header] + lines) + "\n", encoding="utf-8")


def write_file(path: Path, variables, records, header=None):
    """Writes a network file; a new header with today's date unless one is given (sort keeps the old one)."""
    write_lines(path, header or f"#=== {path.stem} {today()}", to_lines(variables, records))