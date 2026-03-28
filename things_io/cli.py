#!/usr/bin/env python3
"""things-io: Read and write Things 3 data. Designed for use as a Claude skill."""

import argparse
import json
import os
import sys
from datetime import date
from shlex import quote

import things


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _output(data):
    print(json.dumps(data, default=str))


def _die(message: str):
    print(json.dumps({"error": message}), file=sys.stderr)
    sys.exit(1)


def _open_url(url: str) -> dict:
    ret = os.system(f"open {quote(url)}")
    if ret != 0:
        _die(f"open command failed with exit code {ret}")
    return {"status": "ok", "url": url}


def _write_url(command: str, params: dict) -> str:
    """Build a things:/// URL, stripping None values and injecting auth where needed."""
    clean = {k: v for k, v in params.items() if v is not None}
    uuid = clean.pop("id", None)

    if command in ("update", "update-project", "update-checklist-item"):
        auth = things.token()
        if not auth:
            _die("Could not read Things auth token from database")
        clean["auth-token"] = auth

    return things.url(uuid=uuid, command=command, **clean)


# ---------------------------------------------------------------------------
# Read commands
# ---------------------------------------------------------------------------

_READ_DISPATCH = {
    "inbox":       things.inbox,
    "today":       things.today,
    "upcoming":    things.upcoming,
    "anytime":     things.anytime,
    "someday":     things.someday,
    "logbook":     things.logbook,
    "trash":       things.trash,
    "todos":       things.todos,
    "projects":    things.projects,
    "areas":       things.areas,
    "tags":        things.tags,
    "deadlines":   things.deadlines,
    "completed":   things.completed,
    "canceled":    things.canceled,
    "logtoday":    lambda: things.logbook(stop_date=date.today().isoformat()),
    "createdtoday": lambda: things.last("1d"),
}


def cmd_read(args):
    command = args.read_command

    if command == "get":
        result = things.get(args.uuid)
        if result is None:
            _die(f"No object found with uuid: {args.uuid}")
        _output(result)
        return

    if command == "search":
        _output(things.search(args.query))
        return

    _output(_READ_DISPATCH[command]())


# ---------------------------------------------------------------------------
# Write commands
# ---------------------------------------------------------------------------


def cmd_write(args):
    command = args.write_command

    if command == "add-todo":
        url = _write_url("add", {
            "title":    args.title,
            "notes":    args.notes,
            "when":     args.when,
            "deadline": args.deadline,
            "tags":     args.tags,
            "list":     args.list,
            "list-id":  args.list_id,
            "heading":  args.heading,
        })

    elif command == "add-project":
        url = _write_url("add-project", {
            "title":    args.title,
            "notes":    args.notes,
            "when":     args.when,
            "deadline": args.deadline,
            "tags":     args.tags,
            "area":     args.area,
            "area-id":  args.area_id,
        })

    elif command == "update":
        url = _write_url("update", {
            "id":            args.id,
            "title":         args.title,
            "notes":         args.notes,
            "prepend-notes": args.prepend_notes,
            "append-notes":  args.append_notes,
            "when":          args.when,
            "deadline":      args.deadline,
            "tags":          args.tags,
            "add-tags":      args.add_tags,
            "completed":     "true" if args.completed else None,
            "canceled":      "true" if args.canceled else None,
        })

    elif command == "update-project":
        url = _write_url("update-project", {
            "id":            args.id,
            "title":         args.title,
            "notes":         args.notes,
            "prepend-notes": args.prepend_notes,
            "append-notes":  args.append_notes,
            "when":          args.when,
            "deadline":      args.deadline,
            "tags":          args.tags,
            "add-tags":      args.add_tags,
            "completed":     "true" if args.completed else None,
            "canceled":      "true" if args.canceled else None,
        })

    elif command == "update-checklist-item":
        url = _write_url("update-checklist-item", {
            "id":        args.id,
            "title":     args.title,
            "completed": "true" if args.completed else None,
        })

    elif command == "complete":
        url = _write_url("update", {"id": args.uuid, "completed": "true"})

    elif command == "show":
        url = things.url(uuid=args.uuid, command="show")

    _output(_open_url(url))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _add_todo_args(p, require_title=True):
    p.add_argument("--title", required=require_title)
    p.add_argument("--notes")
    p.add_argument("--when", help="today|tomorrow|evening|anytime|someday|YYYY-MM-DD")
    p.add_argument("--deadline", metavar="YYYY-MM-DD")
    p.add_argument("--tags", help="Comma-separated tag names")


def _add_update_args(p):
    p.add_argument("--id", required=True, help="UUID of the item to update")
    _add_todo_args(p, require_title=False)
    p.add_argument("--prepend-notes", dest="prepend_notes")
    p.add_argument("--append-notes", dest="append_notes")
    p.add_argument("--add-tags", dest="add_tags", help="Add tags without replacing existing")
    p.add_argument("--completed", action="store_true", default=False)
    p.add_argument("--canceled", action="store_true", default=False)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="things-io",
        description="Read and write Things 3 data. All output is JSON.",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    # --- read ---
    read_p = sub.add_parser("read", help="Read data from Things 3 (SQLite, read-only)")
    read_sub = read_p.add_subparsers(dest="read_command", required=True)

    for name in _READ_DISPATCH:
        read_sub.add_parser(name)

    search_p = read_sub.add_parser("search", help="Full-text search across titles and notes")
    search_p.add_argument("query")

    get_p = read_sub.add_parser("get", help="Fetch any object by UUID")
    get_p.add_argument("uuid")

    # --- write ---
    write_p = sub.add_parser("write", help="Write to Things 3 via URL scheme (macOS only)")
    write_sub = write_p.add_subparsers(dest="write_command", required=True)

    # add-todo
    p = write_sub.add_parser("add-todo", help="Create a new to-do")
    _add_todo_args(p)
    p.add_argument("--list", dest="list", help="Project title to add to")
    p.add_argument("--list-id", dest="list_id", help="Project UUID to add to")
    p.add_argument("--heading", help="Heading title within the project")

    # add-project
    p = write_sub.add_parser("add-project", help="Create a new project")
    _add_todo_args(p)
    p.add_argument("--area", help="Area title to add to")
    p.add_argument("--area-id", dest="area_id", help="Area UUID to add to")

    # update
    _add_update_args(write_sub.add_parser("update", help="Update an existing to-do"))

    # update-project
    _add_update_args(write_sub.add_parser("update-project", help="Update an existing project"))

    # update-checklist-item
    p = write_sub.add_parser("update-checklist-item", help="Update a checklist item")
    p.add_argument("--id", required=True, help="UUID of the checklist item")
    p.add_argument("--title")
    p.add_argument("--completed", action="store_true", default=False)

    # complete (convenience)
    p = write_sub.add_parser("complete", help="Mark a to-do or project complete")
    p.add_argument("uuid")

    # show (convenience)
    p = write_sub.add_parser("show", help="Open an item in the Things app")
    p.add_argument("uuid")

    return parser


def main():
    args = build_parser().parse_args()
    if args.mode == "read":
        cmd_read(args)
    elif args.mode == "write":
        cmd_write(args)


if __name__ == "__main__":
    main()
