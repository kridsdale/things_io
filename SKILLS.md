# things-io

CLI tool for reading and writing Things 3 data on macOS. Run via `uv run things-io` from this directory. All output is JSON on stdout; errors are JSON on stderr with a non-zero exit code.

## Reads

Reads query the Things SQLite database directly and return arrays of task/area/tag objects.

```bash
uv run things-io read inbox
uv run things-io read today
uv run things-io read upcoming
uv run things-io read anytime
uv run things-io read someday
uv run things-io read logbook          # completed + canceled, sorted by stop_date
uv run things-io read logtoday         # completed today
uv run things-io read createdtoday     # created today
uv run things-io read trash
uv run things-io read todos            # all incomplete to-dos
uv run things-io read projects         # all incomplete projects
uv run things-io read areas
uv run things-io read tags
uv run things-io read deadlines        # tasks with deadlines, sorted ascending
uv run things-io read completed
uv run things-io read canceled
uv run things-io read search "query"   # full-text search on title + notes
uv run things-io read get <uuid>       # fetch any object by UUID
```

### Task object shape

```json
{
  "uuid": "6Hf2qWBjWhq7B1xszwdo34",
  "type": "to-do",
  "title": "Buy groceries",
  "status": "incomplete",
  "notes": "",
  "start": "Anytime",
  "start_date": null,
  "deadline": null,
  "stop_date": null,
  "project": null,
  "project_title": null,
  "area": null,
  "area_title": null,
  "heading": null,
  "heading_title": null,
  "tags": [],
  "checklist": false,
  "today_index": 0,
  "index": 5,
  "created": "2024-01-15T09:00:00",
  "modified": "2024-01-15T09:00:00"
}
```

## Writes

Writes use the Things URL scheme (`things:///`) and require Things 3 to be running on macOS. On success, returns `{"status": "ok", "url": "things:///..."}`.

### Create a to-do

```bash
uv run things-io write add-todo --title "Buy groceries"
uv run things-io write add-todo \
  --title "Prepare slides" \
  --notes "Use the Q3 template" \
  --when today \
  --deadline 2024-03-01 \
  --tags "Work,Important" \
  --list-id <project-uuid>
```

`--when` accepts: `today`, `tomorrow`, `evening`, `anytime`, `someday`, or `YYYY-MM-DD`

`--list` / `--list-id`: project to add to (prefer `--list-id` to avoid title ambiguity)

`--heading`: heading title within the project

### Create a project

```bash
uv run things-io write add-project --title "Q2 Planning" --area-id <area-uuid>
uv run things-io write add-project \
  --title "Website Redesign" \
  --notes "See brief in Notion" \
  --when anytime \
  --tags "Work" \
  --area "Design"
```

### Update a to-do

```bash
uv run things-io write update --id <uuid> --title "New title"
uv run things-io write update --id <uuid> --append-notes "Follow-up: done"
uv run things-io write update --id <uuid> --when tomorrow --deadline 2024-04-01
uv run things-io write update --id <uuid> --completed
uv run things-io write update --id <uuid> --canceled
uv run things-io write update --id <uuid> --tags "Work,Urgent"   # replaces all tags
uv run things-io write update --id <uuid> --add-tags "Urgent"    # adds without replacing
```

### Update a project

Same flags as `update`:

```bash
uv run things-io write update-project --id <uuid> --title "New name" --completed
```

### Update a checklist item

```bash
uv run things-io write update-checklist-item --id <uuid> --completed
uv run things-io write update-checklist-item --id <uuid> --title "Revised step"
```

### Convenience commands

```bash
uv run things-io write complete <uuid>   # mark a to-do or project complete
uv run things-io write show <uuid>       # open item in Things app
```

## Workflow example

```bash
# Find the project UUID
uv run things-io read projects | python3 -c "import sys,json; [print(p['uuid'], p['title']) for p in json.load(sys.stdin)]"

# Add a to-do to that project
uv run things-io write add-todo --title "Draft proposal" --list-id <uuid> --when today

# Later, complete it
uv run things-io write complete <task-uuid>
```

## Notes

- **Reads** work even when Things is closed (direct SQLite access).
- **Writes** require Things 3 to be running; the URL scheme triggers the app.
- UUIDs are the stable identifier — always prefer `--list-id` / `--area-id` over title-based args to avoid ambiguity.
- The auth token for `update` commands is read automatically from the database.
