# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_years, date_diff, getdate, nowdate


class StudentApplicant(Document):
	def autoname(self):
		from frappe.model.naming import set_name_by_naming_series

		if self.student_admission:
			naming_series = None
			if self.program:
				# set the naming series from the student admission if provided.
				student_admission = get_student_admission_data(self.student_admission, self.program)
				if student_admission:
					naming_series = student_admission.get("applicant_naming_series")
				else:
					naming_series = None
			else:
				frappe.throw(_("Select the program first"))

			if naming_series:
				self.naming_series = naming_series

		set_name_by_naming_series(self)

	def validate(self):
		self.set_title()
		self.validate_dates()
		self.validate_term()

		if self.student_admission and self.program and self.date_of_birth:
			self.validation_from_student_admission()

		if self.program:
			self.validate_program_eligibility()

	def set_title(self):
		self.title = " ".join(
			filter(None, [self.first_name, self.middle_name, self.last_name])
		)

	def validate_dates(self):
		if self.date_of_birth and getdate(self.date_of_birth) >= getdate():
			frappe.throw(_("Date of Birth cannot be greater than today."))

	def validate_term(self):
		if self.academic_year and self.academic_term:
			actual_academic_year = frappe.db.get_value(
				"Academic Term", self.academic_term, "academic_year"
			)
			if actual_academic_year != self.academic_year:
				frappe.throw(
					_("Academic Term {0} does not belong to Academic Year {1}").format(
						self.academic_term, self.academic_year
					)
				)

	def validation_from_student_admission(self):

		student_admission = get_student_admission_data(self.student_admission, self.program)

		if (
			student_admission
			and student_admission.min_age
			and date_diff(
				nowdate(), add_years(getdate(self.date_of_birth), student_admission.min_age)
			)
			< 0
		):
			frappe.throw(
				_("Not eligible for the admission in this program as per Date Of Birth")
			)

		if (
			student_admission
			and student_admission.max_age
			and date_diff(
				nowdate(), add_years(getdate(self.date_of_birth), student_admission.max_age)
			)
			> 0
		):
			frappe.throw(
				_("Not eligible for the admission in this program as per Date Of Birth")
			)

	def validate_program_eligibility(self):
		"""RT-2: valida los criterios de elegibilidad configurados en el Program."""
		program = frappe.db.get_value(
			"Program",
			self.program,
			[
				"program_status", "min_age", "max_age", "min_education_level",
				"accepts_disability", "disability_types",
				"required_profession", "work_location", "min_entrepreneurship_years",
			],
			as_dict=True,
		)

		if not program:
			return

		# Programa inactivo no acepta aspirantes
		if program.program_status == "Inactivo":
			frappe.throw(
				_("El programa <b>{0}</b> está inactivo y no acepta nuevas solicitudes.").format(self.program),
				title=_("Programa inactivo"),
			)

		# Validar rango de edad
		if self.date_of_birth and (program.min_age or program.max_age):
			from frappe.utils import add_years, date_diff, getdate, nowdate
			age_days = date_diff(nowdate(), getdate(self.date_of_birth))
			age_years = age_days / 365.25

			if program.min_age and age_years < program.min_age:
				frappe.throw(
					_("No cumple la edad mínima requerida de {0} años para el programa <b>{1}</b>.").format(
						program.min_age, self.program
					),
					title=_("Criterio de edad no cumplido"),
				)
			if program.max_age and age_years > program.max_age:
				frappe.throw(
					_("Supera la edad máxima permitida de {0} años para el programa <b>{1}</b>.").format(
						program.max_age, self.program
					),
					title=_("Criterio de edad no cumplido"),
				)

		# Validar nivel de estudios
		if program.min_education_level:
			education_order = ["Primaria", "Secundaria", "Bachiller", "Técnico", "Licenciatura", "Ingeniería"]
			applicant_level = self.get("custom_estudios_previos") or ""
			required_idx = education_order.index(program.min_education_level) if program.min_education_level in education_order else -1
			applicant_idx = education_order.index(applicant_level) if applicant_level in education_order else -1

			if required_idx >= 0 and applicant_idx < required_idx:
				frappe.throw(
					_("El programa <b>{0}</b> requiere al menos nivel de estudios: <b>{1}</b>.").format(
						self.program, program.min_education_level
					),
					title=_("Nivel de estudios insuficiente"),
				)

		# Validar discapacidad
		if not program.accepts_disability:
			applicant_disability = self.get("custom_discapacidad") or "Ninguna"
			if applicant_disability and applicant_disability != "Ninguna":
				frappe.throw(
					_("El programa <b>{0}</b> no está configurado para personas con discapacidad.").format(
						self.program
					),
					title=_("Criterio de discapacidad no cumplido"),
				)
		elif program.accepts_disability and program.disability_types:
			applicant_disability = self.get("custom_discapacidad") or ""
			if applicant_disability and applicant_disability != "Ninguna" and applicant_disability != program.disability_types:
				frappe.throw(
					_("El programa <b>{0}</b> solo acepta el tipo de discapacidad: <b>{1}</b>.").format(
						self.program, program.disability_types
					),
					title=_("Tipo de discapacidad no compatible"),
				)

		# Validar profesión
		if program.required_profession:
			applicant_profession = self.get("custom_profesión") or ""
			if program.required_profession.lower() not in applicant_profession.lower():
				frappe.throw(
					_("El programa <b>{0}</b> requiere la profesión: <b>{1}</b>.").format(
						self.program, program.required_profession
					),
					title=_("Profesión requerida no cumplida"),
				)

		# Validar ubicación de trabajo
		if program.work_location:
			applicant_location = self.get("custom_ubicación_de_trabajo") or ""
			if program.work_location.lower() not in applicant_location.lower():
				frappe.throw(
					_("El programa <b>{0}</b> requiere ubicación de trabajo: <b>{1}</b>.").format(
						self.program, program.work_location
					),
					title=_("Ubicación de trabajo no cumplida"),
				)

		# Validar años de emprendimiento
		if program.min_entrepreneurship_years:
			applicant_years = int(self.get("custom_experiencia_en_emprendimiento_años") or 0)
			if applicant_years < program.min_entrepreneurship_years:
				frappe.throw(
					_("El programa <b>{0}</b> requiere al menos {1} año(s) de experiencia en emprendimiento.").format(
						self.program, program.min_entrepreneurship_years
					),
					title=_("Experiencia en emprendimiento insuficiente"),
				)

	def on_payment_authorized(self, *args, **kwargs):
		self.db_set("paid", 1)


def get_student_admission_data(student_admission, program):

	admission_programs = frappe.get_all(
		"Student Admission Program",
		{"parenttype": "Student Admission", "parent": student_admission, "program": program},
		["applicant_naming_series", "min_age", "max_age"],
	)

	if admission_programs:
		return admission_programs[0]
	return None
