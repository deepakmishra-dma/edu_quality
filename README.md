<div align="center">

# Edu Quality

**A full-stack school-management application for the [Frappe](https://frappeframework.com/) framework.**

Admissions · Enrollment · Fees · Attendance · Assessments · Parent Engagement

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![Frappe](https://img.shields.io/badge/Frappe-v15-0089ff.svg)](https://frappeframework.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab.svg)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://github.com/astral-sh/ruff)

</div>

---

Edu Quality manages the full lifecycle of a K–12 institution — from a prospective
family's first enquiry, through admission, enrollment, fee collection, daily
attendance and assessments, all the way to exit and alumni. It is built on the
Frappe framework (Python + MariaDB) and ships with three purpose-built React
single-page apps for staff, teachers and parents.

## Features

### 🎓 Admissions & student lifecycle
- Lead capture and enquiry funnel, web forms for student and job applications
- Application → approval → enrollment workflow with academic-year rollover
- Division creation and shuffle tools, student groups, houses and batches
- ID cards, birthday cards, bonafide certificates and welcome-kit distribution
- Google Workspace account provisioning for students (optional)

### 💰 Fees
- Fee structures, categories, schedules and multi-company splits
- Payment plans and installments, advances, security deposits
- Discounts — referral, payment-plan and time-based — with approval flows
- Online payment via pluggable gateways (payment-request driven)
- Receipts, refunds, and defaulter / collection reporting
- OTP-gated "rules & regulations" undertakings

### 🗓️ Attendance & academics
- Timetables, working-day calendars and daily attendance entry
- Assessments, observations, marks-entry tools and descriptive reports
- CMAP (curriculum mapping) authoring, tracking and print
- PTM (parent-teacher meeting) scheduling with Google Meet links

### 📣 Communication & integrations
- SMS-based OTP login and notifications (pluggable gateway)
- WhatsApp and email templates for reminders and updates
- Google Workspace (Admin SDK, Calendar, Drive, Meet) via a service account

## Architecture

Edu Quality is a Frappe app (Python backend + MariaDB) with three independent
Vite/React front-ends served through Frappe's website routing. Each front-end
builds into `edu_quality/public/` and is exposed at its own route.

| Front-end | Route | Audience | Stack |
|-----------|-------|----------|-------|
| `walsh/`  | `/walsh/`      | Admin / management portal | Refine + Mantine + React Query |
| `ui/`     | `/ui/`         | Teachers, principals, students | React + shadcn/ui + Tailwind + TanStack Query |
| `cmap_mgr/` | `/cmap-tool/` | CMAP scheduling tool | React + Vite |

The backend is organized into three Frappe modules — **Edu Quality** (core:
schools, students, assessments, CMAP, PTM), **Fees**, and **Attendance** —
plus shared `api/`, `common/`, `overrides/` and `public/py/` helpers.

## Installation

Requires an existing [Frappe bench](https://github.com/frappe/bench) (v15).

```bash
# from your bench directory
bench get-app https://github.com/UnityAppSuite/edu_quality.git
bench --site <site-name> install-app edu_quality
bench --site <site-name> migrate
```

Build the front-ends (each is a standalone Vite app that outputs to
`edu_quality/public/`):

```bash
cd walsh    && yarn install && yarn build   # admin portal
cd ui       && yarn install && yarn build   # teacher / student dashboard
cd cmap_mgr && yarn install && yarn build   # CMAP scheduling tool
```

## Configuration

Third-party credentials are read from the site's `site_config.json` — **never
commit real values**. Set them with `bench set-config` or by editing the file:

```json
{
  "sms_api_key": "<sms gateway key>",
  "sms_sender": "<sender id>",
  "sms_app_name": "<name shown in OTP messages>",
  "sms_login_template_id": "<dlt template id>",
  "sms_update_child_template_id": "<dlt template id>",
  "easebuzz_webhook_secret": "<shared secret for settlement webhook>",
  "magic_link_ttl_days": 30
}
```

The remaining integrations are configured through Settings DocTypes in the
Frappe desk:

| Setting | Where | Purpose |
|---------|-------|---------|
| Email domain for generated accounts | **MGR Settings → `email_domain`** | Student/guardian email addresses |
| Legacy LMS/MGR endpoint (optional) | **MGR Settings → `url`** | External LMS sync (skipped if unset) |
| Refund account | **Fees Settings → `refund_paid_from_account`** | Deposit-refund payment entries |
| Google Workspace | **Google Service Account** | Domain, service-account JSON, impersonation user |
| Payment gateway | **Payment Gateway / Payment Mapping** | Online fee collection |

## Development

```bash
# install the git hooks (ruff, ruff-format, prettier, eslint)
pre-commit install

# run all quality checks locally
pre-commit run --all-files

# front-end dev servers (proxy /api to the Frappe backend)
cd walsh && yarn dev --host
cd ui && yarn dev
```

Tooling and conventions:

- **Python** — formatted and linted with [ruff](https://github.com/astral-sh/ruff)
  (config in `pyproject.toml`); tabs, double quotes, Frappe idioms.
- **Front-end** — [prettier](https://prettier.io/) + [eslint](https://eslint.org/)
  per app.
- **Packaging** — modern flit-based `pyproject.toml`; the app version lives in
  `edu_quality/__init__.py`.
- **Logging** — use `frappe.log_error(title=..., message=frappe.get_traceback())`
  (never `frappe.logger()`), with a static, descriptive title.

Run the test suite:

```bash
bench --site <site-name> run-tests --app edu_quality
```

## Project structure

```
edu_quality/
├── edu_quality/            # core module: schools, students, assessments, CMAP, PTM
│   ├── api/                # REST endpoints (@frappe.whitelist)
│   ├── common/utils/       # shared helpers, incl. access-control (access.py)
│   ├── fees/               # Fees module
│   ├── attendance/         # Attendance module
│   ├── overrides/          # override classes for standard Frappe/ERPNext doctypes
│   ├── public/{py,js}/     # backend helpers + desk client scripts
│   ├── templates/          # print formats, PDFs, jinja includes
│   └── hooks.py            # doc events, scheduled tasks, overrides
├── walsh/  ui/  cmap_mgr/  # React single-page apps
└── pyproject.toml          # packaging + ruff config
```

## Contributing

1. Create a feature branch off the default branch.
2. Ensure `pre-commit run --all-files` passes.
3. Use [conventional-commit](https://www.conventionalcommits.org/) messages
   (`feat:`, `fix:`, `perf:`, `refactor:`, `chore:`, `ci:`, …).
4. Open a pull request describing the change and its rationale.

## License

Edu Quality is licensed under the
[GNU Affero General Public License v3.0](LICENSE). In short: you are free to use,
study, modify and distribute it, and any modified version you run as a network
service must make its source available under the same license.
