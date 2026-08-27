# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A small Flask app for the SSAOS 2026 conference: participants open a per-record
URL and edit their talk info / upload a LaTeX abstract or PDF slides, or submit
arrival/departure details. Each submission rewrites a YAML file on disk and (when
deployed) emails a confirmation to the organizer. There is also a read-only
program view that pulls the schedule from an external URL.

Almost all logic lives in `main.py` (~470 lines). `unicodemail.py` is a
standalone SMTP sender. Templates are in `template/`.

## Commands

- **Run dev server:** `source run.sh` — activates `.venv`, runs
  `runserver.py` (`app.run(debug=True)`), serves on `http://127.0.0.1:5000`.
  Local login is username `user` / password `veslo`.
- **Deploy:** `sudo ./deploy.sh` — copies code to `/usr/local/lib/yadata_editable`,
  installs `yadata_editable.service`, restarts the gunicorn systemd unit
  (bind `localhost:8000`). Run on the target host (`www-kmadg` or `mpm`).
  Note: `deploy.sh` does **not** copy `creds.txt`; it must already exist on the
  server (create with `mkcreds.sh`, which runs `mkcreds.py`).
- **Deps:** `.venv/bin/pip install flask flask-httpauth pyyaml requests gunicorn`
  (no `requirements.txt`; versions are pinned only by whatever is in `.venv`).

There are **no tests and no linter** configured.

## Deploy detection

`main.py` decides it is "deployed" purely from `socket.gethostname()` being
`www-kmadg`/`mpm` **and** running as user `www-data` (`DEPLOYED` constant).
That single flag switches: data directories (`/var/lib/ssaos_2026_*` vs local
`./data`, `./data2`), template dir, credential source (`creds.txt` vs hardcoded),
logging wiring, `ProxyFix`, and whether confirmation emails are actually sent.
When editing, keep both branches working.

Two serving paths exist: the systemd gunicorn unit (primary), and CGI via Apache
(`main.cgi` + `apache-yadata_editable.conf`) under a `/yadata_editable` URL
prefix. `url_for` honours `SCRIPT_NAME`, so keep internal links going through it.

## Data model

No database. Each record is a directory named by an opaque hash id (`code` /
`objid`), containing `data.yaml` plus optional payload files:

- **Talks** — `DATADIR_TALKS` (`./data`): `data.yaml`, `abstract.tex`, `slides.pdf`.
- **Participants** — `DATADIR_PARTICIPANTS` (`./data2`): `data.yaml` only.

`data2/` holds a subset of ids present in `data/`. The `_key` field is a
human-readable label; `code` is the id used in URLs and directory names.

## Form → YAML flow (the core pattern)

Every `*_form` route follows the same shape:

1. GET: `yaml.load` the record, render the form template with `obj`.
2. POST: for each field in `request.form`, **only overwrite keys that already
   exist in `obj`** (`if name in obj`) — this is the whitelist. Unknown fields
   are silently ignored.
3. Uploaded file (`abstract_tex` / `slides_pdf`) is validated by extension only
   and saved to the fixed path.
4. Write YAML atomically: `tempfile.NamedTemporaryFile(delete=False)` +
   `shutil.move` over the real path. Never write the target file in place.
5. Redirect to the matching `thanks*` route, which re-renders and, if `DEPLOYED`,
   calls `unicodemail.send(...)` with the rendered `.txt` body, `.html` body, and
   the uploaded file as an attachment.

`arrival_departure_form` is currently **not routed** (the `@app.route` decorator
is commented out) even though `thanks_arrival_departure` links to it.

## Templates

Jinja2 is configured with `line_statement_prefix='#'` (see the `Environment` in
`main.py`), so control flow is written as `# if ...` / `# for ...` / `# endif` at
the start of a line, **not** `{% ... %}`. Expressions still use `{{ ... }}`.
`loopcontrols` extension is enabled. Form templates extend `base_form.html`;
others extend `base.html`. `thanks_*` come in `.html` + `.txt` pairs (email).

## YAML handling

`main.py` registers custom constructors/representers so all scalars load as
`str` (not bytes/other) and `str` dumps as plain unicode scalars. Always dump
with `allow_unicode=True` (the code already does). `program_day` deliberately
feeds `response.content` (bytes) to `yaml.safe_load_all` to avoid `requests`
mis-guessing the charset of the external `program.yaml`.

## Auth

`flask_httpauth.HTTPBasicAuth`, sha256-hashed password compare. Only
`/test_login` and `/data_yaml` require it; all the participant-facing form routes
are unauthenticated (security rests on the unguessable `code`). `/data_yaml`
GET exports all talks as multi-doc YAML; POST bulk-imports, creating a directory
per doc keyed by `code`, skipping ids that already exist.

## External dependency

`/program` and `/program_day/<n>` fetch `https://www.math.sk/ssaos2026/program.yaml`
at request time. Offline, those routes fail.
