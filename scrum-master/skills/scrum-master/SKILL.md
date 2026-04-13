---
name: scrum-master
description: >
  Personal scrum master and sprint board — a live local web app that manages your to-do items day by day.
  Use this skill whenever the user wants to open their sprint board, manage their tasks, view their daily schedule, track what they've completed, or act as a personal scrum master / task manager.
  Triggers on: "open scrum board", "show my tasks", "daily standup", "what's on my plate", "manage my sprint", "task board", "to-do board", "plan my day", "what did I complete", "scrum master", "sprint board", "daily tasks", "end scrum", "close the board", "stop the board", "kill scrum", "shut down scrum".
  Always use this skill when the user wants to view, manage, or stop their personal task board — even casual phrases like "end", "close it", "stop scrum", or "kill the board". This skill handles ALL task and sprint management — don't try to answer inline, launch or stop the board using the instructions below.
---

# Scrum Master — Personal Sprint Board

A local web app that gives the user a rolling day-by-day task board with persistence via a local JSON file.

## What this skill does

- Launches a lightweight Python HTTP server that serves the board UI
- Persists data to `~/.scrum-master/data.json` (local to the user's machine)
- Auto-rolls incomplete items to today if they're past-due
- Lets the user add items (title + notes), mark complete, move to another day, and view history

## How to launch

### Step 1: Find the server script

The script is bundled with this skill at:
```
<skill_dir>/scripts/server.py
```

The `<skill_dir>` is the directory containing this SKILL.md file. Use that absolute path.

### Step 2: Check if already running

Before starting, check if a server is already listening on port 4242:

```bash
lsof -ti :4242 2>/dev/null || echo "not running"
```

If it's already running, just open `http://localhost:4242` in the browser and tell the user the board is ready.

### Step 3: Start the server

Run the server in the background:

```bash
nohup python3 "<skill_dir>/scripts/server.py" --port 4242 > /tmp/scrum-master.log 2>&1 &
echo $!
```

Wait about 1 second, then verify it started:

```bash
sleep 1 && curl -s -o /dev/null -w "%{http_code}" http://localhost:4242/
```

If the response is `200`, the server is up.

### Step 4: Open the browser

```bash
open http://localhost:4242
```

Then tell the user:

> Your Scrum Master board is live at **http://localhost:4242**
> 
> Data is stored at `~/.scrum-master/data.json` — only on your machine.
>
> To stop the server when you're done: `kill $(lsof -ti :4242)`

## How the board works

The user sees **one day at a time** — defaulting to today. A sticky strip at the top shows 14 days (3 before today through future days) as clickable chips with colored dots showing activity. Arrow buttons navigate by day or week.

**Each day shows three Kanban columns:**
- **To Do** — items not yet started
- **In Progress** — items being worked on
- **Completed** — finished items with completion timestamp

Items are moved between columns by **drag and drop**. Hover an item to reveal edit (✎), move to another day (⇄), and delete (✕) actions.

**Past days** show only the Completed column (read-only — no editing or drag).

**Auto-rollover:** On each page load, any item not in `done` status with a past date is automatically moved to today (with a "rolled from [date]" badge).

## Data schema

The JSON at `~/.scrum-master/data.json`:

```json
{
  "items": [
    {
      "id": "item_1712345678_abc12",
      "title": "Write the quarterly report",
      "notes": "Focus on Q1 highlights and team metrics",
      "date": "2025-04-13",
      "status": "todo",
      "doneAt": null,
      "originalDate": "2025-04-13",
      "rolledFrom": null
    }
  ]
}
```

## Stopping the server

If the user says anything like **"end"**, **"stop"**, **"close the board"**, **"kill scrum"**, **"end scrum"**, or similar — stop the server immediately:

```bash
kill $(lsof -ti :4242) 2>/dev/null && echo "Server stopped"
```

Then confirm to the user: "Scrum Master stopped. Your data is saved at `~/.scrum-master/data.json`."

## Troubleshooting

**Port in use by something else:**  
Try `--port 4243` (or any other port). Update the open URL accordingly.

**Browser doesn't open automatically:**  
Run `open http://localhost:4242` manually, or pass `--no-browser` to suppress the auto-open and just tell the user the URL.

**Data file location:**  
Default is `~/.scrum-master/data.json`. To use a different directory:  
```bash
python3 server.py --data-dir /path/to/custom/dir
```

## Notes for Claude

- The skill is entirely self-contained — no npm, no build step, no external dependencies beyond Python 3 (stdlib only).
- The HTML/JS frontend is a single file served dynamically by the Python server. It talks to `/data` endpoints on the same origin, so no CORS issues.
- Don't try to manually edit the JSON for the user unless they specifically ask — the UI handles all CRUD.
- If the user asks "what did I complete on Monday" or similar history questions, remind them they can navigate to that day in the board using the arrow nav.
