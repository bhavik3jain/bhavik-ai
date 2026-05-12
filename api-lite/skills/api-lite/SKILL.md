---
name: api-lite
description: >
  API Lite — a local Postman replacement for sending HTTP requests, managing collections, and testing APIs.
  Use this skill whenever the user wants to open API Lite, send an HTTP request, test an API endpoint, import a Postman collection, manage REST collections, or use a local API client.
  Triggers on: "open api lite", "launch api lite", "open api client", "test an api", "send a request", "import postman collection", "replace postman", "local postman", "api testing", "http client", "rest client", "start api lite", "close api lite", "stop api lite", "kill api lite".
  Always use this skill for any API testing or HTTP request tooling request — do not try to answer inline.
---

# API Lite — Local HTTP Client

A Postman-style local web app that runs entirely on your machine. No cloud sync, no account.

## Features

- **Collections**: import from Postman (auto-detect or drag-and-drop JSON), create new, save requests
- **Request builder**: method selector, URL bar, params, headers, body (JSON/raw/form), auth (Bearer, API key, Basic)
- **Environment variables**: `{{variable}}` substitution across URL, headers, and body
- **Response pane**: syntax-highlighted JSON, raw view, response headers, status + timing + size
- **Request history**: last 200 requests, click to replay
- **Resizable panes**: drag the handle between builder and response

## How to launch

### Step 1: Find the server script

The script lives at:
```
<skill_dir>/scripts/server.py
```

`<skill_dir>` is the directory containing this SKILL.md file. Use that absolute path.

### Step 2: Check if already running

```bash
lsof -ti :4747 2>/dev/null || echo "not running"
```

If already running, just open `http://localhost:4747` and tell the user.

### Step 3: Start the server

```bash
nohup python3 "<skill_dir>/scripts/server.py" --port 4747 > /tmp/api-lite.log 2>&1 &
echo $!
```

Wait ~1 second, then verify:

```bash
sleep 1 && curl -s -o /dev/null -w "%{http_code}" http://localhost:4747/
```

If `200`, the server is up.

### Step 4: Open the browser

```bash
open http://localhost:4747
```

Tell the user:

> **API Lite is live at http://localhost:4747**
>
> - Import your Postman collections via the **Import Collection** button (auto-scans your Postman app data, or drag-and-drop a JSON file)
> - Create collections, save requests, set environment variables, and view syntax-highlighted responses
> - Data is stored at `~/.api-lite/data.json` — only on your machine
>
> To stop: `kill $(lsof -ti :4747)`

## How to stop

If the user says "stop", "close", "kill", or "end" API Lite:

```bash
kill $(lsof -ti :4747) 2>/dev/null && echo "Stopped"
```

Confirm: "API Lite stopped. Your collections and history are saved at `~/.api-lite/data.json`."

## Data

All state is persisted to `~/.api-lite/data.json`:
- `collections` — imported/created request collections
- `history` — last 200 requests with full request + response
- `environments` — named env var sets
- `activeEnv` — currently selected environment ID

## Postman collection import

The server's `GET /postman-collections` endpoint scans:
- `~/Library/Application Support/Postman/` (macOS)
- `~/.config/Postman/` (Linux)
- `~/AppData/Roaming/Postman/` (Windows)

It identifies v2.x collections by `info.schema` containing "collection" and v1 collections by presence of `requests` + `id` + `name`. The UI also accepts drag-and-drop of exported `.json` files.

## Troubleshooting

**Port in use:** Try `--port 4748`. Update the open URL accordingly.

**Browser doesn't open:** Run `open http://localhost:4747` manually, or pass `--no-browser`.

**Postman collections not found:** Export the collection from Postman as v2.1 JSON and drag it into the import dialog.

## Notes for Claude

- No npm, no build step, stdlib Python only.
- The `/proxy` endpoint executes HTTP requests server-side so the browser never hits CORS issues.
- Don't manually edit `~/.api-lite/data.json` for the user unless they specifically ask — the UI handles all state.
