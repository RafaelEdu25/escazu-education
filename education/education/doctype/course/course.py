# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.model.document import Document


class Course(Document):
	def validate(self):
		self._calcular_horas_totales()
		self.validate_assessment_criteria()
		self.validate_course_documents()

	def _calcular_horas_totales(self):
		self.total_hours = (self.theory_hours or 0) + (self.practical_hours or 0)

	def validate_course_documents(self):
			"""RF-17: eliminar filas vacías y validar campos requeridos."""
			docs_validos = []
			for row in self.course_documents:
				tiene_nombre = bool(row.document_name and row.document_name.strip())
				tiene_archivo = bool(row.document_file)
				
				if not tiene_nombre and not tiene_archivo:
					# Fila completamente vacía → ignorar silenciosamente
					continue
				
				if tiene_nombre and tiene_archivo:
					docs_validos.append(row)
				else:
					# Fila parcialmente llena → error claro
					frappe.throw(
						_("Fila {0} en Documentos: debe completar tanto <b>Nombre</b> como <b>Archivo</b>.").format(
							row.idx
						)
					)

			self.course_documents = docs_validos

	def validate_assessment_criteria(self):
		if self.assessment_criteria:
			total_weightage = 0
			for criteria in self.assessment_criteria:
				total_weightage += criteria.weightage or 0
			if total_weightage != 100:
				frappe.throw(_("Total Weightage of all Assessment Criteria must be 100%"))

	def after_insert(self):
		"""Hook llamado después de insertar el documento."""
		from education.moodle_integration.events import on_course_created
		on_course_created(self, "after_insert")

	def on_update(self):
		"""Hook llamado después de actualizar el documento."""
		# Solo sincronizar si ya tiene moodle_course_id (ya existe en Moodle)
		if self.moodle_course_id:
			from education.moodle_integration.events import on_course_updated
			on_course_updated(self, "on_update")

	def on_rename(self, old_name, new_name, merge=False):
		"""Hook llamado después de renombrar el documento."""
		from education.moodle_integration.events import sync_course_to_moodle

		if self.moodle_course_id:
			frappe.enqueue(
				sync_course_to_moodle,
				course_name=new_name,
				queue="short",
				enqueue_after_commit=True,
			)

	def get_topics(self):
		topic_data = []
		for topic in self.topics:
			topic_doc = frappe.get_doc("Topic", topic.topic)
			if topic_doc.topic_content:
				topic_data.append(topic_doc)
		return topic_data


@frappe.whitelist()
def add_course_to_programs(course, programs, mandatory=False):
	programs = json.loads(programs)
	for entry in programs:
		program = frappe.get_doc("Program", entry)
		program.append(
			"courses", {"course": course, "course_name": course, "mandatory": mandatory}
		)
		program.flags.ignore_mandatory = True
		program.save()
	frappe.msgprint(
		_("Course {0} has been added to all the selected programs successfully.").format(
			frappe.bold(course)
		),
		title=_("Programs updated"),
		indicator="green",
	)


@frappe.whitelist()
def get_programs_without_course(course):
	data = []
	for entry in frappe.db.get_all("Program"):
		program = frappe.get_doc("Program", entry.name)
		courses = [c.course for c in program.courses]
		if not courses or course not in courses:
			data.append(program.name)
	return data

	