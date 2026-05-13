# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt


from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_courses_for_student_group(doctype, txt, searchfield, start, page_len, filters):
	"""Retorna los cursos del Program Module vinculado al Student Group."""
	student_group = filters.get("student_group")
	if not student_group:
		return []

	program_module = frappe.db.get_value("Student Group", student_group, "program_module")
	if not program_module:
		return frappe.db.sql(
			"""SELECT name, course_name FROM `tabCourse`
			WHERE (name LIKE %(txt)s OR course_name LIKE %(txt)s)
			ORDER BY name LIMIT %(start)s, %(page_len)s""",
			{"txt": f"%{txt}%", "start": start, "page_len": page_len},
		)

	return frappe.db.sql(
		"""SELECT pmc.course, c.course_name
		FROM `tabProgram Module Course` pmc
		INNER JOIN `tabCourse` c ON c.name = pmc.course
		WHERE pmc.parent = %(module)s
		AND (pmc.course LIKE %(txt)s OR c.course_name LIKE %(txt)s)
		ORDER BY pmc.order_no, pmc.course
		LIMIT %(start)s, %(page_len)s""",
		{"module": program_module, "txt": f"%{txt}%", "start": start, "page_len": page_len},
	)


class CourseSchedule(Document):
	def validate(self):
		self.instructor_name = frappe.db.get_value(
			"Instructor", self.instructor, "instructor_name"
		)
		self.validate_instructor_active()
		self.set_title()
		self.validate_course()
		self.validate_date()
		self.validate_time()
		self.validate_overlap()

	def validate_instructor_active(self):
		status = frappe.db.get_value("Instructor", self.instructor, "status")
		if status == "Inactive":
			frappe.throw(
				_(
					"El instructor {0} está desactivado y no puede ser asignado a nuevos cursos. "
					"Por favor seleccione un instructor activo."
				).format(self.instructor),
				title=_("⚠️ Instructor Inactivo")
			)

	def before_save(self):
		self.set_hex_color()

	def set_title(self):
		"""Set document Title"""
		self.title = (
			self.course
			+ " by "
			+ (self.instructor_name if self.instructor_name else self.instructor)
		)

	def validate_course(self):
		group_based_on, course = frappe.db.get_value(
			"Student Group", self.student_group, ["group_based_on", "course"]
		)
		if group_based_on == "Course":
			self.course = course

	def validate_date(self):
		academic_year, academic_term = frappe.db.get_value(
			"Student Group", self.student_group, ["academic_year", "academic_term"]
		)
		self.schedule_date = frappe.utils.getdate(self.schedule_date)

		if academic_term:
			start_date, end_date = frappe.db.get_value(
				"Academic Term", academic_term, ["term_start_date", "term_end_date"]
			)
			if (
				start_date
				and end_date
				and (self.schedule_date < start_date or self.schedule_date > end_date)
			):
				frappe.throw(
					_(
						"Schedule date selected does not lie within the Academic Term of the Student Group {0}."
					).format(self.student_group)
				)

		elif academic_year:
			start_date, end_date = frappe.db.get_value(
				"Academic Year", academic_year, ["year_start_date", "year_end_date"]
			)
			if self.schedule_date < start_date or self.schedule_date > end_date:
				frappe.throw(
					_(
						"Schedule date selected does not lie within the Academic Year of the Student Group {0}."
					).format(self.student_group)
				)

	def validate_time(self):
		"""Validates if from_time is greater than to_time"""
		if self.from_time > self.to_time:
			frappe.throw(_("From Time cannot be greater than To Time."))

		"""Handles specicfic case to update schedule date in calendar """
		if isinstance(self.from_time, str):
			try:
				datetime_obj = datetime.strptime(self.from_time, "%Y-%m-%d %H:%M:%S")
				self.schedule_date = datetime_obj
			except ValueError:
				pass

	def validate_overlap(self):
		"""Validates overlap for Student Group, Instructor, Room"""

		from education.education.utils import validate_overlap_for, get_overlap_for

		# Validate overlapping course schedules.
		if self.student_group:
			validate_overlap_for(self, "Course Schedule", "student_group")

		instructor_overlap = get_overlap_for(self, "Course Schedule", "instructor")
		if instructor_overlap:
			frappe.msgprint(_("Advertencia: El instructor tiene otro horario en este bloque."), alert=True)

		validate_overlap_for(self, "Course Schedule", "room")

		# validate overlapping assessment schedules.
		if self.student_group:
			validate_overlap_for(self, "Assessment Plan", "student_group")

		validate_overlap_for(self, "Assessment Plan", "room")
		validate_overlap_for(self, "Assessment Plan", "supervisor", self.instructor)

	def set_hex_color(self):
		colors = {
			"blue": "#EDF6FD",
			"green": "#E4F5E9",
			"red": "#FFF0F0",
			"orange": "#FFF1E7",
			"yellow": "#FFF7D3",
			"teal": "#E6F7F4",
			"violet": "#F5F2FF",
			"cyan": "#E0F8FF",
			"amber": "#FCF3CF",
			"pink": "#FEEEF8",
			"purple": "#F9F0FF",
		}
		self.color = colors[self.class_schedule_color or "green"]


@frappe.whitelist()
def check_conflicts(doc_name, instructor, room, schedule_date, from_time, to_time):
    """
    Función para verificar conflictos antes de guardar.
    Retorna una lista de mensajes de advertencia.
    """
    from education.education.utils import get_overlap_for
    
    # Creamos un objeto temporal para usar las funciones de overlap existentes
    tmp_doc = frappe._dict({
        "doctype": "Course Schedule",
        "name": doc_name,
        "instructor": instructor,
        "room": room,
        "schedule_date": schedule_date,
        "from_time": from_time,
        "to_time": to_time
    })

    warnings = []

    # Verificar Instructor
    instructor_overlap = get_overlap_for(tmp_doc, "Course Schedule", "instructor")
    if instructor_overlap:
        warnings.append(_("El Instructor {0} ya tiene una clase asignada en este horario.").format(instructor))

    # Verificar Salón (Room)
    room_overlap = get_overlap_for(tmp_doc, "Course Schedule", "room")
    if room_overlap:
        warnings.append(_("El Salón {0} ya se encuentra ocupado en este horario.").format(room))

    return warnings