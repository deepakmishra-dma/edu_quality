# Edu Quality

Edu Quality is a [Frappe](https://frappeframework.com/) application for
educational-institution management. It covers student admissions and
applications, program enrollment, attendance, assessments, fee management,
and parent/teacher communication, with several React single-page apps for
teacher, admin, and scheduling workflows built on top of the Frappe backend.

## Modules

- **Edu Quality** — schools, classes, divisions, assessments, observations,
  CMAP (curriculum mapping), PTM scheduling, and student lifecycle.
- **Fees** — fee structures, receipts, advances, discounts, payment plans,
  refunds, and defaulter reporting.
- **Attendance** — timetables, attendance entry, and working-day calendars.

## Frontends

| App | Path | Purpose |
|-----|------|---------|
| `walsh/` | `/walsh/` | Admin / management portal (Refine + Mantine) |
| `ui/` | `/ui/` | Teacher / principal / student dashboard (React + shadcn/ui) |
| `cmap_mgr/` | `/cmap-tool/` | CMAP scheduling tool (legacy) |

## Installation

Requires an existing [Frappe bench](https://github.com/frappe/bench) (v15).

```bash
# from your bench directory
bench get-app edu_quality <repository-url>
bench --site <site-name> install-app edu_quality
bench --site <site-name> migrate
```

Build the frontends:

```bash
npm install     # installs walsh, ui and walsh-admin deps
npm run build
```

## Configuration

Several integrations read their credentials from the site's
`site_config.json` (never commit real values):

```json
{
  "sms_api_key": "<your SMS gateway key>",
  "sms_sender": "<sender id>",
  "sms_app_name": "<name shown in OTP messages>",
  "sms_login_template_id": "<dlt template id>",
  "sms_update_child_template_id": "<dlt template id>"
}
```

Google Workspace, MGR, and payment-gateway settings are configured through
their respective Settings DocTypes in the Frappe desk. The email domain used
for generated student/guardian accounts is set on **MGR Settings**
(`email_domain`).

## Development

```bash
pre-commit install     # ruff, ruff-format, prettier, eslint
npm run dev            # run the frontends in watch mode
```

## License

[MIT](LICENSE)
