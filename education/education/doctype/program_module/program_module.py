import frappe
from frappe.model.document import Document


class ProgramModule(Document):

	def validate(self):
		self._calcular_horas_totales()
		self._validar_tipo_programa()
		self._validar_tipo_asignaturas()
		self._validar_asignaturas_duplicadas()
		self._validar_prerrequisito_circular()

	def _calcular_horas_totales(self):
		"""Suma horas de las asignaturas; si no hay filas usa los campos manuales."""
		if self.courses_in_module:
			self.theory_hours = sum(r.theory_hours or 0 for r in self.courses_in_module)
			self.practical_hours = sum(r.practical_hours or 0 for r in self.courses_in_module)
		self.total_hours = (self.theory_hours or 0) + (self.practical_hours or 0)

	def _validar_tipo_programa(self):
		"""El programa asociado debe ser de tipo Modular o Técnico, no Libre."""
		if not self.program:
			return
		program_type = frappe.db.get_value("Program", self.program, "program_type")
		if program_type not in ("Modular", "Técnico"):
			frappe.throw(
				f"El programa '{self.program}' es de tipo '{program_type or 'sin definir'}'. "
				"Solo los programas de tipo Modular o Técnico admiten módulos."
			)

	def _validar_tipo_asignaturas(self):
		"""Una asignatura de tipo Libre no puede agregarse a un módulo."""
		for row in self.courses_in_module:
			if not row.course:
				continue
			course_type = frappe.db.get_value("Course", row.course, "course_type")
			if course_type not in ("Modular", "Técnico"):
				frappe.throw(
					f"La asignatura '{row.course}' es de tipo '{course_type or 'sin definir'}' y no puede "
					f"agregarse a un módulo. Solo asignaturas de tipo Modular o Técnico "
					f"pueden pertenecer a un módulo."
				)

	def _validar_asignaturas_duplicadas(self):
		"""No permite agregar la misma asignatura dos veces en el módulo."""
		cursos_vistos = set()
		for row in self.courses_in_module:
			if not row.course:
				continue
			if row.course in cursos_vistos:
				frappe.throw(
					f"La asignatura '{row.course}' está duplicada en la tabla "
					f"de asignaturas del módulo. Cada asignatura debe aparecer "
					f"una sola vez."
				)
			cursos_vistos.add(row.course)

	def _validar_prerrequisito_circular(self):
		"""Un módulo no puede ser prerrequisito de sí mismo."""
		for row in self.prerequisites:
			if row.prerequisite_module == self.name:
				frappe.throw(
					"Un módulo no puede ser prerrequisito de sí mismo."
				)
