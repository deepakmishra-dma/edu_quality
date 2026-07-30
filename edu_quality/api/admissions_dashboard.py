# Copyright (c) 2026, Walnut and contributors
# For license information, please see license.txt

"""Live aggregates for the CRM / Admissions MIS dashboard (``/ui/dashboard``).

Every figure served from here is derived from the ERP at request time:

    Enquiries      Lead                (bucketed on ``creation``)
    Waiting list   Lead                (the "waiting" option of ``status``)
    Admissions     Student Applicant   (the "admitted" option of ``application_status``,
                                        bucketed on ``application_date``)
    Strength       Program Enrollment  (submitted, on-roll statuses)
    Capacity       Student Group       (sum of ``max_strength`` over division groups)
    Divisions      Student Group       (count of the same groups)
    Target         Admission Target

Nothing about a particular school is written into this module. Branches, class
names, class order, and the status values that count as on-roll / admitted /
waiting are all read from the site being served:

* Branches group by ``School.location`` where it is filled in, otherwise one
  branch per School record.
* Class names come from ``Program.program_name``.
* Class order follows the ``Program.previous_class`` progression chain, falling
  back to ``Program.sequence`` and then to a numeric/alphabetical ordering.
* Status values are matched against the Select options actually defined on the
  site, so a site that words them differently still reports correctly.

Fields that some sites customise away (``Lead.center``, ``Program Enrollment``'s
``custom_status``, and so on) are feature-detected; the dashboard drops the
affected breakdown rather than erroring.
"""

import re
from collections import defaultdict, deque

import frappe
from frappe import _
from frappe.utils import getdate, nowdate

# Enrolment statuses meaning the pupil is no longer on the roll. Matched as
# substrings against whatever Select options the site defines.
OFF_ROLL_KEYWORDS = (
	"cancel",
	"alumni",
	"exit",
	"left",
	"leaving",
	"inactive",
	"not attending",
	"drop",
	"transferred",
	"discontinu",
)
ADMITTED_KEYWORDS = ("admit", "enrol", "enroll")
WAITING_KEYWORDS = ("wait",)
DIVISION_GROUP_KEYWORDS = ("batch", "division")

MONTH_LABEL = "%b %Y"
DAY_LABEL = "%b %d"


# Each figure is read from one of these. Sites grant them to different roles,
# so access is checked per source rather than against a single gatekeeper.
SOURCE_DOCTYPES = (
	"Program Enrollment",
	"Student Applicant",
	"Lead",
	"Student Group",
	"Admission Target",
)


def _can_read(doctype):
	"""Whether the current user may read a source doctype.

	The aggregates below run raw queries, which bypass permissions, so every
	source is gated on this explicitly. A viewer entitled to only some of them
	sees those figures and zeroes elsewhere.
	"""
	try:
		return bool(frappe.has_permission(doctype, "read"))
	except Exception:
		return False


def _check_permission():
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to view the admissions dashboard."), frappe.PermissionError)

	if not any(_can_read(doctype) for doctype in SOURCE_DOCTYPES):
		frappe.throw(
			_("You do not have permission to read any admissions data."), frappe.PermissionError
		)


def _percent(numerator, denominator):
	"""Percentage rounded to one decimal, guarding the empty-denominator case."""
	if not denominator:
		return 0.0

	return round((numerator / float(denominator)) * 100.0, 1)


# ---------------------------------------------------------------------------
# Schema probing -- keeps the dashboard working on sites that customise fields
# ---------------------------------------------------------------------------


def _has_field(doctype, fieldname):
	try:
		return bool(frappe.get_meta(doctype).has_field(fieldname))
	except Exception:
		return False


def _select_options(doctype, fieldname):
	"""The Select options defined for a field on this site, in order."""
	try:
		field = frappe.get_meta(doctype).get_field(fieldname)
	except Exception:
		return []

	if not field or not field.options:
		return []

	return [option.strip() for option in field.options.split("\n") if option.strip()]


def _match_option(options, keywords):
	"""First option whose label contains one of ``keywords``."""
	for option in options:
		lowered = option.lower()
		if any(keyword in lowered for keyword in keywords):
			return option

	return None


def _on_roll_statuses():
	"""Enrolment statuses that mean the pupil counts towards strength.

	Returns None when the site has no such field, in which case submission
	alone decides whether an enrolment counts.
	"""
	options = _select_options("Program Enrollment", "custom_status")
	if not options:
		return None

	on_roll = [
		option
		for option in options
		if not any(keyword in option.lower() for keyword in OFF_ROLL_KEYWORDS)
	]

	return on_roll or None


def _admitted_status():
	options = _select_options("Student Applicant", "application_status")
	return _match_option(options, ADMITTED_KEYWORDS)


def _waiting_status():
	return _match_option(_select_options("Lead", "status"), WAITING_KEYWORDS)


def _division_group_type():
	return _match_option(_select_options("Student Group", "group_based_on"), DIVISION_GROUP_KEYWORDS)


# ---------------------------------------------------------------------------
# Branches and classes
# ---------------------------------------------------------------------------


def _school_index():
	"""School -> branch, plus the branches in a stable display order.

	Sites that fill in ``School.location`` are grouped by it, so several School
	records serving one campus report as a single branch. Sites that leave the
	field empty fall back to one branch per School, which keeps the dashboard
	populated instead of blank.
	"""
	fields = ["name"]
	if _has_field("School", "location"):
		fields.append("location")

	schools = frappe.get_all("School", fields=fields, limit_page_length=0)

	school_to_location = {}
	for school in schools:
		location = (school.get("location") or "").strip()
		if location:
			school_to_location[school.name] = location

	if not school_to_location:
		school_to_location = {school.name: school.name for school in schools}

	locations = sorted(set(school_to_location.values()))
	return school_to_location, locations


def _program_school_fields():
	"""Whichever School link fields this site defines on Program."""
	return [field for field in ("school", "custom_school") if _has_field("Program", field)]


def _short_label(name):
	"""A compact column heading derived from the class name itself."""
	if len(name) <= 3:
		return name

	words = [word for word in re.split(r"[\s.\-_/]+", name) if word]
	if len(words) > 1:
		return "".join(word[0] for word in words).upper()

	return name[:3]


def _ranks_from_chain(names):
	"""Order classes by the ``previous_class`` progression, if it covers them all."""
	if not _has_field("Program", "previous_class"):
		return None

	edges = frappe.db.sql(
		"""
		select distinct prev.program_name as from_class, p.program_name as to_class
		from `tabProgram` p
		join `tabProgram` prev on prev.name = p.previous_class
		where ifnull(p.previous_class, '') != ''
			and ifnull(prev.program_name, '') != ''
			and ifnull(p.program_name, '') != ''
			and prev.program_name != p.program_name
		""",
		as_dict=True,
	)

	covered = {edge.from_class for edge in edges} | {edge.to_class for edge in edges}
	if not edges or not names.issubset(covered):
		return None

	successors = defaultdict(set)
	indegree = {name: 0 for name in names}
	for edge in edges:
		if edge.from_class not in names or edge.to_class not in names:
			continue
		if edge.to_class not in successors[edge.from_class]:
			successors[edge.from_class].add(edge.to_class)
			indegree[edge.to_class] += 1

	# Longest-path depth, so a class always sorts after every class feeding it.
	depth = {name: 0 for name in names}
	queue = deque(sorted(name for name in names if not indegree[name]))
	visited = 0
	while queue:
		current = queue.popleft()
		visited += 1
		for following in sorted(successors[current]):
			depth[following] = max(depth[following], depth[current] + 1)
			indegree[following] -= 1
			if not indegree[following]:
				queue.append(following)

	if visited != len(names):
		return None  # the chain loops back on itself

	return {name: (0, depth[name], name.lower()) for name in names}


def _ranks_from_sequence(programs, names):
	"""Order classes by ``Program.sequence`` when it distinguishes every class."""
	lowest = {}
	for program in programs:
		name = (program.program_name or "").strip()
		if not name or not program.get("sequence"):
			continue
		sequence = program.get("sequence")
		lowest[name] = min(lowest.get(name, sequence), sequence)

	if set(lowest) != names or len(set(lowest.values())) != len(names):
		return None

	return {name: (0, lowest[name], name.lower()) for name in names}


def _ranks_from_name(names):
	"""Last resort: numbered classes in numeric order, named ones ahead of them."""
	ranks = {}
	for name in names:
		if name.isdigit():
			ranks[name] = (1, int(name), name.lower())
		else:
			ranks[name] = (0, 0, name.lower())

	return ranks


def _class_ranks(programs):
	names = {
		(program.program_name or "").strip()
		for program in programs
		if (program.program_name or "").strip()
	}
	if not names:
		return {}

	ranks = _ranks_from_chain(names)
	if ranks is None and _has_field("Program", "sequence"):
		ranks = _ranks_from_sequence(programs, names)
	if ranks is None:
		ranks = _ranks_from_name(names)

	return ranks


def _program_index(school_to_location):
	"""Program -> the class and branch it belongs to, with its display order."""
	fields = ["name", "program_name"] + _program_school_fields()
	if _has_field("Program", "sequence"):
		fields.append("sequence")

	programs = frappe.get_all("Program", fields=fields, limit_page_length=0)
	ranks = _class_ranks(programs)

	index = {}
	for program in programs:
		school = None
		for field in _program_school_fields():
			school = program.get(field)
			if school:
				break

		class_key = (program.program_name or "").strip()
		index[program.name] = {
			"class_key": class_key,
			"label": class_key,
			"short": _short_label(class_key) if class_key else "",
			"sort": ranks.get(class_key, (2, 0, class_key.lower())),
			"school": school,
			"location": school_to_location.get(school),
		}

	return index


def _class_columns(program_index):
	"""Every distinct class across all programs, in teaching order."""
	seen = {}
	for info in program_index.values():
		key = info["class_key"]
		if key and key not in seen:
			seen[key] = info

	ordered = sorted(seen.values(), key=lambda info: info["sort"])
	return [{"key": info["class_key"], "label": info["label"], "short": info["short"]} for info in ordered]


# ---------------------------------------------------------------------------
# Academic years
# ---------------------------------------------------------------------------


def _academic_years():
	"""Academic years that actually carry admissions data, newest first."""
	sources = [("Program Enrollment", "docstatus = 1")]
	if _has_field("Lead", "academic_year"):
		sources.append(("Lead", None))
	if _has_field("Student Applicant", "academic_year"):
		sources.append(("Student Applicant", None))

	used = set()
	for doctype, condition in sources:
		clause = "ifnull(academic_year, '') != ''"
		if condition:
			clause = "%s and %s" % (condition, clause)
		rows = frappe.db.sql(
			"select distinct academic_year from `tab{0}` where {1}".format(doctype, clause)
		)
		used.update(row[0] for row in rows)

	years = frappe.get_all(
		"Academic Year",
		fields=["name"],
		order_by="year_start_date desc",
		limit_page_length=0,
	)

	return [year.name for year in years if year.name in used]


def _leading_year(name):
	"""The four-digit year a name such as "2025-2026" starts with."""
	match = re.match(r"^\s*(\d{4})", name or "")
	return int(match.group(1)) if match else None


def _previous_academic_year(academic_year):
	"""The academic year immediately before ``academic_year``, or None."""
	years = frappe.get_all(
		"Academic Year", fields=["name", "year_start_date"], limit_page_length=0
	)
	names = {year.name for year in years}

	# Prefer the name this site would give the preceding year.
	match = re.match(r"^(\d{4})\s*-\s*(\d{2,4})$", (academic_year or "").strip())
	if match:
		start = int(match.group(1))
		tail = match.group(2)
		guess = "%d-%d" % (start - 1, start) if len(tail) == 4 else "%d-%s" % (start - 1, str(start)[2:])
		if guess in names:
			return guess

	selected = next((year for year in years if year.name == academic_year), None)
	if not selected:
		return None

	# Then the year starting closest before this one.
	if selected.year_start_date:
		earlier = [
			year
			for year in years
			if year.year_start_date
			and year.name != academic_year
			and getdate(year.year_start_date) < getdate(selected.year_start_date)
		]
		if earlier:
			return max(earlier, key=lambda year: getdate(year.year_start_date)).name

	# Sites that leave the dates blank fall back to the closest lower year number.
	# Never the positional neighbour: with no dates that can return a later year.
	selected_number = _leading_year(academic_year)
	if selected_number is None:
		return None

	numbered = [
		(number, year.name)
		for year in years
		for number in [_leading_year(year.name)]
		if number is not None and number < selected_number
	]

	return max(numbered)[1] if numbered else None


def _default_academic_year(candidates):
	"""The year in progress today, falling back to the most recent with data.

	Stray records can push an academic year years into the future into the list,
	so the newest entry is a poor default -- prefer the year actually running.
	"""
	if not candidates:
		return None

	today = nowdate()
	running = frappe.get_all(
		"Academic Year",
		filters={"year_start_date": ("<=", today), "year_end_date": (">=", today)},
		fields=["name"],
		order_by="year_start_date desc",
		limit_page_length=0,
	)
	for year in running:
		if year.name in candidates:
			return year.name

	return candidates[0]


def _resolve_academic_year(academic_year):
	if academic_year:
		return academic_year

	default = _default_academic_year(_academic_years())
	if not default:
		frappe.throw(_("No academic year has any admissions data yet."))

	return default


# ---------------------------------------------------------------------------
# Aggregates
# ---------------------------------------------------------------------------


def _enrolment_students(academic_year, school_to_location, program_index):
	"""On-roll students for a year, as sets keyed by branch and by (branch, class)."""
	if not _can_read("Program Enrollment"):
		return defaultdict(set), defaultdict(set)

	has_school = _has_field("Program Enrollment", "custom_school")
	statuses = _on_roll_statuses()

	conditions = ["docstatus = 1", "academic_year = %(academic_year)s", "ifnull(student, '') != ''"]
	values = {"academic_year": academic_year}
	if statuses:
		conditions.append("custom_status in %(statuses)s")
		values["statuses"] = tuple(statuses)

	school_column = "custom_school" if has_school else "null"
	rows = frappe.db.sql(
		"""
		select {school_column} as custom_school, program, student
		from `tabProgram Enrollment`
		where {conditions}
		""".format(school_column=school_column, conditions=" and ".join(conditions)),
		values,
		as_dict=True,
	)

	by_location = defaultdict(set)
	by_location_class = defaultdict(set)

	for row in rows:
		info = program_index.get(row.program) or {}
		location = school_to_location.get(row.custom_school) or info.get("location")
		if not location:
			continue

		by_location[location].add(row.student)

		class_key = info.get("class_key")
		if class_key:
			by_location_class[(location, class_key)].add(row.student)

	return by_location, by_location_class


def _admissions(academic_year, school_to_location, program_index):
	"""Admitted applicants for a year, resolved to a branch and a class."""
	if not _can_read("Student Applicant"):
		return []

	admitted = _admitted_status()
	if not admitted:
		return []

	optional = [
		field
		for field in ("school", "school_name", "program", "seeking_admission_in_class", "application_date")
		if _has_field("Student Applicant", field)
	]

	rows = frappe.get_all(
		"Student Applicant",
		filters={"academic_year": academic_year, "application_status": admitted},
		fields=["name"] + optional,
		limit_page_length=0,
	)

	resolved = []
	for row in rows:
		program = row.get("program") or row.get("seeking_admission_in_class")
		info = program_index.get(program) or {}
		school = row.get("school") or row.get("school_name")
		location = school_to_location.get(school) or info.get("location")
		if not location:
			continue

		resolved.append(
			{
				"location": location,
				"class_key": info.get("class_key"),
				"date": row.get("application_date"),
			}
		)

	return resolved


def _enquiry_counts(academic_year, group_by, status=None):
	"""Lead counts for a year grouped by branch and either month, day or class.

	``group_by`` is one of "month", "day" or "class"; ``status`` optionally
	narrows to a single CRM status (used for the waiting list).
	"""
	if not _can_read("Lead") or not _has_field("Lead", "academic_year"):
		return []

	center_expr = "l.`center`" if _has_field("Lead", "center") else "null"
	class_expr = "l.`class`" if _has_field("Lead", "class") else "null"
	buckets = {"month": "left(l.creation, 7)", "day": "date(l.creation)", "class": class_expr}
	bucket_expr = buckets[group_by]

	conditions = ["l.academic_year = %(academic_year)s"]
	values = {"academic_year": academic_year}
	if status:
		conditions.append("l.status = %(status)s")
		values["status"] = status

	group_parts = []
	for expr in (center_expr, class_expr, bucket_expr):
		if expr != "null" and expr not in group_parts:
			group_parts.append(expr)

	query = """
		select {center} as center, {klass} as program, {bucket} as bucket, count(*) as cnt
		from `tabLead` l
		where {conditions}
	""".format(
		center=center_expr,
		klass=class_expr,
		bucket=bucket_expr,
		conditions=" and ".join(conditions),
	)
	if group_parts:
		query += " group by %s" % ", ".join(group_parts)

	return frappe.db.sql(query, values, as_dict=True)


def _capacity(academic_year, program_index):
	"""Seats and division counts per branch, and per (branch, class)."""
	if not _can_read("Student Group") or not _has_field("Student Group", "max_strength"):
		return defaultdict(lambda: {"capacity": 0, "divisions": 0}), defaultdict(
			lambda: {"capacity": 0, "divisions": 0}
		)

	conditions = ["academic_year = %(academic_year)s"]
	values = {"academic_year": academic_year}

	group_type = _division_group_type()
	if group_type and _has_field("Student Group", "group_based_on"):
		conditions.append("group_based_on = %(group_based_on)s")
		values["group_based_on"] = group_type

	rows = frappe.db.sql(
		"""
		select program, sum(ifnull(max_strength, 0)) as capacity, count(*) as divisions
		from `tabStudent Group`
		where {conditions}
		group by program
		""".format(conditions=" and ".join(conditions)),
		values,
		as_dict=True,
	)

	by_location = defaultdict(lambda: {"capacity": 0, "divisions": 0})
	by_location_class = defaultdict(lambda: {"capacity": 0, "divisions": 0})

	for row in rows:
		info = program_index.get(row.program) or {}
		location = info.get("location")
		if not location:
			continue

		capacity = int(row.capacity or 0)
		divisions = int(row.divisions or 0)

		by_location[location]["capacity"] += capacity
		by_location[location]["divisions"] += divisions

		class_key = info.get("class_key")
		if class_key:
			bucket = by_location_class[(location, class_key)]
			bucket["capacity"] += capacity
			bucket["divisions"] += divisions

	return by_location, by_location_class


def _targets(academic_year, program_index):
	"""Configured admission targets per branch and per (branch, class)."""
	if not _can_read("Admission Target"):
		return defaultdict(int), defaultdict(int), set()

	rows = frappe.get_all(
		"Admission Target",
		filters={"academic_year": academic_year},
		fields=["program", "target"],
		limit_page_length=0,
	)

	by_location = defaultdict(int)
	by_location_class = defaultdict(int)
	configured = set()

	for row in rows:
		info = program_index.get(row.program) or {}
		location = info.get("location")
		if not location:
			continue

		target = int(row.target or 0)
		by_location[location] += target
		configured.add(location)

		class_key = info.get("class_key")
		if class_key:
			by_location_class[(location, class_key)] += target

	return by_location, by_location_class, configured


def _location_of(row, school_to_location, program_index):
	"""Branch for a Lead row, from its centre or failing that its class."""
	return school_to_location.get(row.center) or (program_index.get(row.program) or {}).get("location")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_dashboard_meta():
	"""Academic years, branches and classes the dashboard can be filtered by."""
	_check_permission()

	school_to_location, locations = _school_index()
	program_index = _program_index(school_to_location)
	academic_years = _academic_years()

	return {
		"academic_years": academic_years,
		"default_academic_year": _default_academic_year(academic_years),
		"locations": locations,
		"classes": _class_columns(program_index),
	}


@frappe.whitelist()
def get_strength_analysis(academic_year=None):
	"""Branch-level strength, admissions, attrition and occupancy for a year."""
	_check_permission()

	academic_year = _resolve_academic_year(academic_year)
	previous_year = _previous_academic_year(academic_year)

	school_to_location, locations = _school_index()
	program_index = _program_index(school_to_location)

	current_students, _current_by_class = _enrolment_students(
		academic_year, school_to_location, program_index
	)
	previous_students = {}
	if previous_year:
		previous_students, _previous_by_class = _enrolment_students(
			previous_year, school_to_location, program_index
		)

	admissions_by_location = defaultdict(int)
	for admission in _admissions(academic_year, school_to_location, program_index):
		admissions_by_location[admission["location"]] += 1

	enquiries_by_location = defaultdict(int)
	for row in _enquiry_counts(academic_year, "class"):
		location = _location_of(row, school_to_location, program_index)
		if location:
			enquiries_by_location[location] += int(row.cnt or 0)

	capacity_by_location, _capacity_by_class = _capacity(academic_year, program_index)
	targets_by_location, _targets_by_class, targets_configured = _targets(academic_year, program_index)

	rows = []
	for location in locations:
		current = current_students.get(location, set())
		previous = previous_students.get(location, set())

		strength_current = len(current)
		strength_previous = len(previous)
		# Students on last year's roll who are not on this year's -- i.e. did not continue.
		cancelled = len(previous - current)
		new_admissions = admissions_by_location.get(location, 0)
		enquiries = enquiries_by_location.get(location, 0)
		capacity = capacity_by_location.get(location, {}).get("capacity", 0)
		target = targets_by_location.get(location, 0)
		# With no Admission Target on file there is nothing to measure against,
		# so the balance stays blank rather than reading as a large shortfall.
		has_target = location in targets_configured

		rows.append(
			{
				"location": location,
				"target": target if has_target else None,
				# Admissions still needed to reach the configured target.
				"balance": (target - new_admissions) if has_target else None,
				"strength_current": strength_current,
				"strength_previous": strength_previous,
				"new_admissions": new_admissions,
				"admission_percent": _percent(new_admissions, strength_previous),
				"cancelled": cancelled,
				"cancelled_percent": _percent(cancelled, strength_previous),
				"added_students": strength_current - strength_previous,
				"added_percent": _percent(strength_current - strength_previous, strength_previous),
				"enquiries": enquiries,
				"convert_percent": _percent(new_admissions, enquiries),
				"capacity": capacity,
				"full_percent": _percent(strength_current, capacity),
			}
		)

	rows.append(_total_strength_row(rows))

	return {
		"academic_year": academic_year,
		"previous_academic_year": previous_year,
		"rows": rows,
	}


def _total_strength_row(rows):
	"""Totals row -- counts are summed, percentages recomputed from the totals."""
	has_target = any(row["target"] is not None for row in rows)
	total = {
		"location": _("Total"),
		"is_total": True,
		"target": sum(row["target"] or 0 for row in rows) if has_target else None,
		"balance": sum(row["balance"] or 0 for row in rows) if has_target else None,
		"strength_current": sum(row["strength_current"] for row in rows),
		"strength_previous": sum(row["strength_previous"] for row in rows),
		"new_admissions": sum(row["new_admissions"] for row in rows),
		"cancelled": sum(row["cancelled"] for row in rows),
		"enquiries": sum(row["enquiries"] for row in rows),
		"capacity": sum(row["capacity"] for row in rows),
	}

	total["added_students"] = total["strength_current"] - total["strength_previous"]
	total["admission_percent"] = _percent(total["new_admissions"], total["strength_previous"])
	total["cancelled_percent"] = _percent(total["cancelled"], total["strength_previous"])
	total["added_percent"] = _percent(total["added_students"], total["strength_previous"])
	total["convert_percent"] = _percent(total["new_admissions"], total["enquiries"])
	total["full_percent"] = _percent(total["strength_current"], total["capacity"])

	return total


@frappe.whitelist()
def get_class_distribution(academic_year=None):
	"""Target against admissions, per branch and class."""
	_check_permission()

	academic_year = _resolve_academic_year(academic_year)

	school_to_location, locations = _school_index()
	program_index = _program_index(school_to_location)
	classes = _class_columns(program_index)

	_targets_by_location, targets_by_class, _configured = _targets(academic_year, program_index)

	admissions_by_class = defaultdict(int)
	for admission in _admissions(academic_year, school_to_location, program_index):
		if admission["class_key"]:
			admissions_by_class[(admission["location"], admission["class_key"])] += 1

	rows = []
	for location in locations:
		target = {}
		admissions = {}
		for column in classes:
			key = column["key"]
			target[key] = targets_by_class.get((location, key), 0)
			admissions[key] = admissions_by_class.get((location, key), 0)

		target["total"] = sum(target.values())
		admissions["total"] = sum(admissions.values())

		rows.append({"location": location, "target": target, "admissions": admissions})

	return {
		"academic_year": academic_year,
		"classes": classes + [{"key": "total", "label": _("Total"), "short": _("Total")}],
		"rows": rows,
	}


@frappe.whitelist()
def get_branch_report(academic_year=None):
	"""Month-by-month enquiries against admissions, per branch."""
	_check_permission()

	academic_year = _resolve_academic_year(academic_year)

	school_to_location, locations = _school_index()
	program_index = _program_index(school_to_location)

	enquiries = defaultdict(int)
	for row in _enquiry_counts(academic_year, "month"):
		location = _location_of(row, school_to_location, program_index)
		if location and row.bucket:
			enquiries[(location, row.bucket)] += int(row.cnt or 0)

	admissions = defaultdict(int)
	for admission in _admissions(academic_year, school_to_location, program_index):
		if admission["date"]:
			admissions[(admission["location"], getdate(admission["date"]).strftime("%Y-%m"))] += 1

	branches = []
	for location in locations:
		months = sorted(
			{key[1] for key in enquiries if key[0] == location}
			| {key[1] for key in admissions if key[0] == location}
		)

		series = []
		for month in months:
			series.append(
				{
					"month": month,
					"label": getdate("%s-01" % month).strftime(MONTH_LABEL),
					"enquiries": enquiries.get((location, month), 0),
					"admissions": admissions.get((location, month), 0),
				}
			)

		total_enquiries = sum(entry["enquiries"] for entry in series)
		total_admissions = sum(entry["admissions"] for entry in series)
		peak = max(series, key=lambda entry: entry["enquiries"], default=None)

		branches.append(
			{
				"location": location,
				"months": series,
				"stats": {
					"total_enquiries": total_enquiries,
					"total_admissions": total_admissions,
					"conversion_rate": _percent(total_admissions, total_enquiries),
					"peak_month": peak["label"] if peak and peak["enquiries"] else "-",
				},
			}
		)

	return {"academic_year": academic_year, "branches": branches}


def _matrix_row(label, values, classes):
	"""One dashboard table row: a label plus a value per class and a total."""
	data = [values.get(column["key"], 0) for column in classes]
	return {"name": label, "data": data + [sum(data)]}


def _percent_row(label, values, classes):
	data = [values.get(column["key"], 0.0) for column in classes]
	numbers = [value for value in data if value]
	average = round(sum(numbers) / len(numbers), 1) if numbers else 0.0
	return {"name": label, "data": data + [average]}


def _date_matrix(entries, classes):
	"""Turn (date, class) pairs into one row per date, plus a leading total row."""
	by_date = defaultdict(lambda: defaultdict(int))
	for entry_date, class_key in entries:
		if not entry_date or not class_key:
			continue
		by_date[getdate(entry_date)][class_key] += 1

	rows = []
	totals = defaultdict(int)
	for entry_date in sorted(by_date):
		counts = by_date[entry_date]
		for key, value in counts.items():
			totals[key] += value
		rows.append(_matrix_row(entry_date.strftime(DAY_LABEL), counts, classes))

	if not rows:
		return []

	return [_matrix_row(_("Total"), totals, classes)] + rows


@frappe.whitelist()
def get_admission_detail(academic_year=None, location=None):
	"""Class-wise summary plus date-wise admissions and waiting list for a branch."""
	_check_permission()

	academic_year = _resolve_academic_year(academic_year)
	previous_year = _previous_academic_year(academic_year)

	school_to_location, locations = _school_index()
	if not location:
		if not locations:
			frappe.throw(_("No School records exist, so branches cannot be listed."))
		location = locations[0]

	program_index = _program_index(school_to_location)
	classes = _class_columns(program_index)

	current_totals, current_by_class = _enrolment_students(
		academic_year, school_to_location, program_index
	)
	previous_by_class = {}
	if previous_year:
		_previous_totals, previous_by_class = _enrolment_students(
			previous_year, school_to_location, program_index
		)

	current_students = current_totals.get(location, set())
	_capacity_totals, capacity_by_class = _capacity(academic_year, program_index)

	admissions = [
		admission
		for admission in _admissions(academic_year, school_to_location, program_index)
		if admission["location"] == location
	]

	enquiries_by_class = defaultdict(int)
	for row in _enquiry_counts(academic_year, "class"):
		if _location_of(row, school_to_location, program_index) != location:
			continue
		class_key = (program_index.get(row.program) or {}).get("class_key")
		if class_key:
			enquiries_by_class[class_key] += int(row.cnt or 0)

	admissions_by_class = defaultdict(int)
	for admission in admissions:
		if admission["class_key"]:
			admissions_by_class[admission["class_key"]] += 1

	strength_current = {}
	strength_previous = {}
	cancellations = {}
	cancellation_percent = {}
	capacity = {}
	divisions = {}
	vacancies = {}
	conversion = {}

	for column in classes:
		key = column["key"]
		current = current_by_class.get((location, key), set())
		previous = previous_by_class.get((location, key), set())
		seats = capacity_by_class.get((location, key), {})

		strength_current[key] = len(current)
		strength_previous[key] = len(previous)
		# Last year's pupils in this class who are no longer on the branch roll.
		cancellations[key] = len(previous - current_students)
		cancellation_percent[key] = _percent(cancellations[key], len(previous))
		capacity[key] = seats.get("capacity", 0)
		divisions[key] = seats.get("divisions", 0)
		vacancies[key] = seats.get("capacity", 0) - len(current)
		conversion[key] = _percent(admissions_by_class.get(key, 0), enquiries_by_class.get(key, 0))

	previous_label = previous_year or _("Previous Year")

	stats_rows = [
		_matrix_row(_("{0} Strength").format(academic_year), strength_current, classes),
		_matrix_row(_("{0} Strength").format(previous_label), strength_previous, classes),
		_matrix_row(_("Divisions"), divisions, classes),
		_matrix_row(_("Capacity"), capacity, classes),
		_matrix_row(_("Vacancies"), vacancies, classes),
		_matrix_row(_("Admissions"), dict(admissions_by_class), classes),
		_matrix_row(_("Enquiries"), dict(enquiries_by_class), classes),
		_matrix_row(_("Cancellations"), cancellations, classes),
		# Percentages are per class, so the trailing figure is an average.
		_percent_row(_("Cancellation %"), cancellation_percent, classes),
		_percent_row(_("Conversion %"), conversion, classes),
	]

	admission_rows = _date_matrix(
		[(admission["date"], admission["class_key"]) for admission in admissions], classes
	)

	waiting_counts = []
	waiting_status = _waiting_status()
	if waiting_status:
		for row in _enquiry_counts(academic_year, "day", status=waiting_status):
			if _location_of(row, school_to_location, program_index) != location:
				continue
			class_key = (program_index.get(row.program) or {}).get("class_key")
			waiting_counts.extend([(row.bucket, class_key)] * int(row.cnt or 0))

	return {
		"academic_year": academic_year,
		"previous_academic_year": previous_year,
		"location": location,
		"locations": locations,
		"columns": [column["short"] for column in classes] + [_("Total")],
		"stats": stats_rows,
		"admissions": admission_rows,
		"waiting_list": _date_matrix(waiting_counts, classes),
	}
