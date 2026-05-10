import frappe


def execute():
	"""Aplica los nuevos custom fields del SGF:
	- Course.total_hours (calculado automáticamente)
	- Student Group.program_module (link a Program Module)
	- Corrige insert_after de modality (después de total_hours)
	- Agrega fetch_from en Program Module Course (theory_hours, practical_hours, credits)
	"""
	from education.education.setup.custom_fields import create_custom_fields

	create_custom_fields()
	frappe.reload_doc("education", "doctype", "program_module_course", force=True)
