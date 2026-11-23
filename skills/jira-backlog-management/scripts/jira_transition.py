#!/usr/bin/env python3
"""Move Jira issues between workflow statuses (To Do / In Progress / Done ...).

Many Jira MCP servers can read, create and comment on issues but cannot change
their status. This script fills that gap with the Jira Cloud REST API v3.

Usage
  jira_transition.py status  KEY [KEY ...]           current status (read-only)
  jira_transition.py list    KEY                     available transitions (read-only)
  jira_transition.py move    KEY [KEY ...] TARGET    change status (WRITE)
        [--comment TEXT] [--dry-run]

TARGET matches, case- and space-insensitively, a transition's target status name,
the transition's own name, or its numeric id. Aliases: todo, inprogress, review,
done. Examples: "In Progress", inprogress, done, 31.

Credentials (never printed):
  1. env ATLASSIAN_BASE_URL / ATLASSIAN_EMAIL / ATLASSIAN_API_TOKEN
     (or JIRA_BASE_URL / JIRA_EMAIL / JIRA_API_TOKEN), else
  2. the `env` block of the MCP server named $JIRA_MCP_SERVER (default "jira")
     in ~/.claude.json, so the token configured for the Jira MCP is reused.

Exit codes: 0 ok, 1 usage/config error, 2 Jira/API error or partial failure.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ALIASES = {
    "todo": ["to do", "todo", "open", "backlog", "selected for development"],
    "inprogress": ["in progress", "inprogress", "in development", "doing"],
    "review": ["in review", "review", "code review", "qa"],
    "done": ["done", "closed", "resolved", "complete", "completed"],
}


def norm(s):
    return "".join(str(s).lower().split()).replace("-", "").replace("_", "")


def load_credentials():
    def pick(env, *names):
        for n in names:
            if env.get(n):
                return env[n]
        return None

    sources = [os.environ]
    cfg_path = os.path.expanduser("~/.claude.json")
    server = os.environ.get("JIRA_MCP_SERVER", "jira")
    try:
        with open(cfg_path) as f:
            cfg = json.load(f)
        sources.append(cfg.get("mcpServers", {}).get(server, {}).get("env", {}) or {})
    except (OSError, ValueError):
        pass

    for env in sources:
        base = pick(env, "ATLASSIAN_BASE_URL", "JIRA_BASE_URL", "JIRA_URL")
        email = pick(env, "ATLASSIAN_EMAIL", "JIRA_EMAIL", "JIRA_USERNAME")
        token = pick(env, "ATLASSIAN_API_TOKEN", "JIRA_API_TOKEN")
        if base and email and token:
            return base.rstrip("/"), email, token
    sys.exit(
        "error: Jira credentials not found. Set ATLASSIAN_BASE_URL, ATLASSIAN_EMAIL and "
        f"ATLASSIAN_API_TOKEN, or configure them on MCP server '{server}' in {cfg_path}."
    )


class Jira:
    def __init__(self):
        self.base, email, token = load_credentials()
        raw = f"{email}:{token}".encode()
        self.auth = "Basic " + base64.b64encode(raw).decode()

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Authorization", self.auth)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode()
                return json.loads(text) if text else None
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            hint = {401: " (bad email/API token)", 403: " (no permission)",
                    404: " (issue not found or not visible)"}.get(e.code, "")
            raise RuntimeError(f"HTTP {e.code}{hint}: {detail}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"network error: {e.reason}") from None

    def issue_status(self, key):
        k = urllib.parse.quote(key)
        d = self.call("GET", f"/rest/api/3/issue/{k}?fields=status,summary")
        st = d["fields"]["status"]
        return {"key": d["key"], "summary": d["fields"]["summary"],
                "status": st["name"], "category": st["statusCategory"]["name"]}

    def transitions(self, key):
        k = urllib.parse.quote(key)
        d = self.call("GET", f"/rest/api/3/issue/{k}/transitions")
        return [{"id": t["id"], "name": t["name"], "to": t["to"]["name"],
                 "to_category": t["to"]["statusCategory"]["name"]}
                for t in d.get("transitions", [])]

    def transition(self, key, tid, comment=None):
        body = {"transition": {"id": tid}}
        if comment:
            body["update"] = {"comment": [{"add": {"body": {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph",
                             "content": [{"type": "text", "text": comment}]}]}}}]}
        k = urllib.parse.quote(key)
        self.call("POST", f"/rest/api/3/issue/{k}/transitions", body)


def resolve(target, transitions):
    t = norm(target)
    if target.isdigit():
        return [x for x in transitions if x["id"] == target]
    for field in ("to", "name"):
        hits = [x for x in transitions if norm(x[field]) == t]
        if hits:
            return hits
    for alias, names in ALIASES.items():
        if t == alias or t in {norm(n) for n in names}:
            wanted = {norm(n) for n in names}
            hits = [x for x in transitions if norm(x["to"]) in wanted]
            if hits:
                return hits
            # fall back to the status category (To Do / In Progress / Done)
            cat = {"todo": "todo", "inprogress": "inprogress", "done": "done"}.get(alias)
            if cat:
                return [x for x in transitions if norm(x["to_category"]) == cat]
    return []


def cmd_status(jira, keys):
    rc = 0
    for key in keys:
        try:
            s = jira.issue_status(key)
            print(f"{s['key']}\t{s['status']}\t[{s['category']}]\t{s['summary']}")
        except RuntimeError as e:
            print(f"{key}\tERROR\t{e}", file=sys.stderr)
            rc = 2
    return rc


def cmd_list(jira, key):
    s = jira.issue_status(key)
    print(f"{s['key']} — {s['summary']}\ncurrent status: {s['status']} [{s['category']}]")
    ts = jira.transitions(key)
    if not ts:
        print("no transitions available to this account")
    for x in ts:
        print(f"  id={x['id']:<5} {x['name']!r:<28} -> {x['to']} [{x['to_category']}]")
    return 0


def cmd_move(jira, keys, target, comment, dry_run):
    rc = 0
    for key in keys:
        try:
            before = jira.issue_status(key)
            if norm(before["status"]) == norm(target):
                print(f"{key}: already in '{before['status']}' — skipped")
                continue
            ts = jira.transitions(key)
            hits = resolve(target, ts)
            if len(hits) != 1:
                opts = ", ".join(f"{x['id']}:{x['name']}->{x['to']}" for x in ts) or "none"
                why = "no transition matches" if not hits else "ambiguous target"
                print(f"{key}: FAILED — {why} '{target}' from '{before['status']}'. "
                      f"Available: {opts}", file=sys.stderr)
                rc = 2
                continue
            t = hits[0]
            if dry_run:
                print(f"{key}: would move '{before['status']}' -> '{t['to']}' "
                      f"via transition {t['id']} '{t['name']}'")
                continue
            jira.transition(key, t["id"], comment)
            after = jira.issue_status(key)
            ok = norm(after["status"]) == norm(t["to"])
            print(f"{key}: '{before['status']}' -> '{after['status']}' "
                  f"{'(verified)' if ok else '(WARNING: expected ' + repr(t['to']) + ')'}")
            if not ok:
                rc = 2
        except RuntimeError as e:
            print(f"{key}: FAILED — {e}", file=sys.stderr)
            rc = 2
    return rc


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status", help="show current status (read-only)")
    s.add_argument("keys", nargs="+")
    l = sub.add_parser("list", help="list available transitions (read-only)")
    l.add_argument("key")
    m = sub.add_parser("move", help="transition issue(s) to a status (WRITE)")
    m.add_argument("args", nargs="+", metavar="KEY... TARGET")
    m.add_argument("--comment", help="add this comment with the transition")
    m.add_argument("--dry-run", action="store_true", help="resolve only; change nothing")
    a = p.parse_args()

    jira = Jira()
    try:
        if a.cmd == "status":
            return cmd_status(jira, a.keys)
        if a.cmd == "list":
            return cmd_list(jira, a.key)
        if len(a.args) < 2:
            p.error("move needs at least one KEY and a TARGET")
        return cmd_move(jira, a.args[:-1], a.args[-1], a.comment, a.dry_run)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
