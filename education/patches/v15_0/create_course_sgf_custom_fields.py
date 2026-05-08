import frappe


def execute():
	"""Apply SGF Escazú academic custom fields (Course, Topic) on existing sites.

	These were defined in setup/custom_fields.py (commit c564587) but only ran
	on after_install. This patch backfills them for already-installed sites.
	"""
	from education.education.setup.custom_fields import create_custom_fields

	create_custom_fields()
