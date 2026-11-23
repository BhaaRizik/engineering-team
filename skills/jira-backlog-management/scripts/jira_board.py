#!/usr/bin/env python3
"""Put Jira issues on the board: sprints and assignees.

Scrum boards show only the issues in the active sprint. Issues left in the
backlog never appear on the board, even when their status changes. This
script adds issues to a sprint and assigns them. Use it together with
jira_transition.py, which changes status.

Usage
  jira_board.py sprints PROJECT                         boards and sprints (read-only)
  jira_board.py board   PROJECT                         issues in the active sprint (read-only)
  jira_board.py me                                      the connected Jira user (read-only)
  jira_board.py add-to-sprint KEY [KEY ...]             move issues into a sprint (WRITE)
        --project PROJECT [--sprint active|future|ID] [--dry-run]
  jira_board.py assign KEY [KEY ...] --to me|ACCOUNT_ID [--dry-run]   (WRITE)

Epics are not added to sprints; add their stories and tasks instead.
Credentials are the same as jira_transition.py and are never printed.
Exit codes: 0 ok, 1 usage/config error, 2 Jira/API error or partial failure.
"""
import argparse
import importlib.util
import os
import sys
import urllib.parse

_spec = importlib.util.spec_from_file_location(
    "jira_transition", os.path.join(os.path.dirname(os.path.abspath(__file__)), "jira_transition.py"))
_jt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_jt)


def boards(jira, project):
    p = urllib.parse.quote(project)
    return jira.call("GET", f"/rest/agile/1.0/board?projectKeyOrId={p}").get("values", [])


def sprints(jira, board_id):
    try:
        return jira.call("GET", f"/rest/agile/1.0/board/{board_id}/sprint?maxResults=50").get("values", [])
    except RuntimeError:
        return []


def find_sprint(jira, project, which):
    found = []
    for b in boards(jira, project):
        for s in sprints(jira, b["id"]):
            if which.isdigit() and str(s["id"]) == which:
                return s, b
            if s["state"] == which:
                found.append((s, b))
    if not found:
        raise RuntimeError(f"no {which} sprint found for project {project}")
    if which == "future":
        return found[0]
    if len(found) > 1:
        names = ", ".join(f"{s['id']}:{s['name']}" for s, _ in found)
        raise RuntimeError(f"several {which} sprints ({names}); pass --sprint ID")
    return found[0]


def issue_info(jira, key):
    k = urllib.parse.quote(key)
    d = jira.call("GET", f"/rest/api/3/issue/{k}?fields=summary,status,assignee,issuetype,sprint,customfield_10020")
    f = d["fields"]
    sprint_field = f.get("sprint") or f.get("customfield_10020") or []
    if isinstance(sprint_field, dict):
        sprint_field = [sprint_field]
    return {
        "key": d["key"], "summary": f["summary"], "status": f["status"]["name"],
        "type": f["issuetype"]["name"],
        "assignee": (f.get("assignee") or {}).get("displayName"),
        "assignee_id": (f.get("assignee") or {}).get("accountId"),
        "sprint_ids": [s.get("id") for s in sprint_field if isinstance(s, dict)],
    }


def cmd_sprints(jira, project):
    bs = boards(jira, project)
    if not bs:
        print(f"no boards found for {project}")
    for b in bs:
        print(f"board {b['id']} '{b['name']}' type={b.get('type')}")
        ss = sprints(jira, b["id"])
        if not ss:
            print("  no sprints (kanban board, or sprints disabled)")
        for s in ss:
            print(f"  sprint {s['id']:<5} {s['state']:<7} {s['name']}  {s.get('startDate', '')[:10]} .. {s.get('endDate', '')[:10]}")
    return 0


def cmd_board(jira, project):
    s, b = find_sprint(jira, project, "active")
    d = jira.call("GET", f"/rest/agile/1.0/sprint/{s['id']}/issue?fields=summary,status,assignee&maxResults=100")
    print(f"active sprint {s['id']} '{s['name']}' on board {b['id']} '{b['name']}': {d.get('total', 0)} issue(s)")
    for i in d.get("issues", []):
        f = i["fields"]
        print(f"  {i['key']}\t{f['status']['name']}\t{(f.get('assignee') or {}).get('displayName') or 'Unassigned'}\t{f['summary']}")
    return 0


def cmd_me(jira):
    u = jira.call("GET", "/rest/api/3/myself")
    print(f"{u['displayName']}\taccountId={u['accountId']}")
    return 0


def cmd_add_to_sprint(jira, keys, project, which, dry_run):
    s, _ = find_sprint(jira, project, which)
    rc = 0
    todo = []
    for key in keys:
        try:
            info = issue_info(jira, key)
        except RuntimeError as e:
            print(f"{key}: FAILED — {e}", file=sys.stderr)
            rc = 2
            continue
        if info["type"].lower() == "epic":
            print(f"{key}: skipped — epics are not added to sprints; add its stories instead")
            continue
        if s["id"] in info["sprint_ids"]:
            print(f"{key}: already in sprint {s['id']} '{s['name']}' — skipped")
            continue
        todo.append(key)
    if not todo:
        return rc
    if dry_run:
        for key in todo:
            print(f"{key}: would add to sprint {s['id']} '{s['name']}' ({s['state']})")
        return rc
    try:
        jira.call("POST", f"/rest/agile/1.0/sprint/{s['id']}/issue", {"issues": todo})
    except RuntimeError as e:
        print(f"FAILED adding {', '.join(todo)} to sprint {s['id']} — {e}", file=sys.stderr)
        return 2
    for key in todo:
        ok = s["id"] in issue_info(jira, key)["sprint_ids"]
        print(f"{key}: added to sprint {s['id']} '{s['name']}' {'(verified)' if ok else '(WARNING: not found in sprint)'}")
        if not ok:
            rc = 2
    return rc


def cmd_assign(jira, keys, to, dry_run):
    if to == "me":
        u = jira.call("GET", "/rest/api/3/myself")
        account, name = u["accountId"], u["displayName"]
    else:
        u = jira.call("GET", f"/rest/api/3/user?accountId={urllib.parse.quote(to)}")
        account, name = u["accountId"], u["displayName"]
    rc = 0
    for key in keys:
        try:
            info = issue_info(jira, key)
            if info["assignee_id"] == account:
                print(f"{key}: already assigned to {name} — skipped")
                continue
            if dry_run:
                print(f"{key}: would assign {info['assignee'] or 'Unassigned'} -> {name}")
                continue
            jira.call("PUT", f"/rest/api/3/issue/{urllib.parse.quote(key)}/assignee", {"accountId": account})
            ok = issue_info(jira, key)["assignee_id"] == account
            print(f"{key}: assigned to {name} {'(verified)' if ok else '(WARNING: not applied)'}")
            if not ok:
                rc = 2
        except RuntimeError as e:
            print(f"{key}: FAILED — {e}", file=sys.stderr)
            rc = 2
    return rc


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sprints").add_argument("project")
    sub.add_parser("board").add_argument("project")
    sub.add_parser("me")
    a2s = sub.add_parser("add-to-sprint")
    a2s.add_argument("keys", nargs="+")
    a2s.add_argument("--project", required=True)
    a2s.add_argument("--sprint", default="active", help="active (default), future, or a sprint id")
    a2s.add_argument("--dry-run", action="store_true")
    asg = sub.add_parser("assign")
    asg.add_argument("keys", nargs="+")
    asg.add_argument("--to", required=True, help="me, or an Atlassian accountId")
    asg.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    jira = _jt.Jira()
    try:
        if a.cmd == "sprints":
            return cmd_sprints(jira, a.project)
        if a.cmd == "board":
            return cmd_board(jira, a.project)
        if a.cmd == "me":
            return cmd_me(jira)
        if a.cmd == "add-to-sprint":
            return cmd_add_to_sprint(jira, a.keys, a.project, a.sprint, a.dry_run)
        return cmd_assign(jira, a.keys, a.to, a.dry_run)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
