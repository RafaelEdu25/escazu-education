# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Frappe/ERPNext app for education management (schools). Custom fork of `frappe/education`, maintained by Edupan. Targets Frappe v16 + ERPNext. 117 doctypes covering students, courses, fees, attendance, assessments, and Moodle LMS sync.

## Commands

### Running tests
```bash
bench --site education.test run-tests --app education
# Single module:
bench --site education.test run-tests --app education --module education.education.doctype.student.test_student
```

### Linting / formatting
```bash
# Python
black education/
flake8 --config .github/helper/flake8.conf education/

# JS/Vue
cd frontend && yarn prettier --write src/
```

### Frontend dev
```bash
yarn dev          # Vite dev server on :8080, proxies Frappe on :8000
yarn build        # Builds to education/public/frontend/
```

### Docker
```bash
yarn docker:init  # First-time setup inside container
yarn docker:prod  # Production setup inside container
```

### Local site setup (no Docker)
```bash
bench get-app erpnext && bench get-app payments
bench new-site education.test --install-app erpnext
bench --site education.test install-app education
bench start
```

## Architecture

### Backend — Python / Frappe

- **`education/hooks.py`** — app wiring: scheduler jobs, doc events, global search doctypes, portal menu, default roles. Read this to understand what triggers what.
- **`education/education/api.py`** — whitelisted REST endpoints consumed by frontend (enroll_student, mark_attendance, etc.).
- **`education/education/utils.py`** — scheduling conflict detection (`validate_overlap_for`, `get_overlap_for`).
- **`education/education/scheduler.py`** — cron job: `auto_promote_scholars` runs daily at 02:00 on Jan 1.
- **`education/education/billing.py`** — fee management logic.
- **`education/install.py`** — one-time setup: fixtures, custom fields on Sales Invoice/Order, Student role.
- **`education/patches/`** — DB migrations; v14_0 and v15_0 subdirectories.

### Moodle Integration

- **`moodle_integration/moodle_client.py`** — HTTP client for Moodle REST API.
- **`moodle_integration/api.py`** — higher-level operations (create/update/delete courses, enroll students).
- **`moodle_integration/sync_manager.py`** — sync orchestration between Frappe and Moodle.
- **`moodle_integration/events.py`** — doc event handlers wired from `hooks.py` on Course after_insert/save/rename.

### Frontend — Vue 3 / Frappe UI

Student Portal SPA at `frontend/src/`:
- **`stores/`** — Pinia stores: `session.js` (auth), `student.js`, `user.js`, `leave.js`.
- **`pages/`** — route-level components: Home, Attendance, Fees, Leaves, Schedule, Grades, SchoolDiary.
- **`components/`** — shared UI pieces, mostly wrapping Frappe UI primitives.
- **`router.js`** — Vue Router 4 config.

Built output lands in `education/public/frontend/` and is served at `/assets/education/frontend/`.

## Key conventions

- **Python style**: Black, line length 110, tabs for indentation (Ruff config in `pyproject.toml`).
- **Frappe doc events**: wire via `hooks.py` `doc_events`, implement in `events.py` inside the relevant module.
- **Whitelisted APIs**: use `@frappe.whitelist()` in `api.py`; frontend calls via `frappe.call`.
- **Translations**: Spanish translations live in `education/translations/es.csv`; new translated doctypes go in `hooks.py` under `translated_doctypes`.
- **Patches**: add migration scripts under `education/patches/` and register in `patches.txt`.
- **Scheduler jobs**: define in `hooks.py` `scheduler_events`, implement in `scheduler.py`.

## CI

GitHub Actions (`.github/workflows/ci.yml`): Python 3.14, Node 24, MariaDB 10.6. Runs pre-commit (Black, Flake8, Prettier) then `bench run-tests`. Triggers on PR and daily cron.
