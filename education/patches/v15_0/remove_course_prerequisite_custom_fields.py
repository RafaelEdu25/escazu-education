import frappe


def execute():
	"""Remove stale Custom Fields on Course doctype for prerequisites.

	These were created manually in DB in earlier versions.
	Prerequisites are now defined natively in course.json via course_prerequisites Table field.
	"""
	stale_fields = frappe.get_all(
		"Custom Field",
		filters={
			"dt": "Course",
			"options": "Course Prerequisite Custom",
		},
		pluck="name",
	)

	for field_name in stale_fields:
		frappe.delete_doc("Custom Field", field_name, ignore_missing=True)

	if stale_fields:
		frappe.db.commit()
