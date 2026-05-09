import frappe


def execute():
	"""Reemplaza el campo padre de Program Module de Course → Program.

	El campo 'course' (Link a Course) se renombró a 'program' (Link a Program)
	para reflejar correctamente la jerarquía: Program → Program Module → Course.
	Las tablas están vacías por lo que no hay datos que migrar.
	"""
	frappe.reload_doc("education", "doctype", "program_module", force=True)
	frappe.reload_doc("education", "doctype", "program", force=True)
