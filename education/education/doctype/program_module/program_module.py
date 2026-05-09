import frappe
from frappe.model.document import Document


class ProgramModule(Document):

	def validate(self):
		self._calcular_horas_totales()
		self._validar_tipo_curso()
		self._validar_asignaturas_duplicadas()
		self._validar_prerrequisito_circular()

	def _calcular_horas_totales(self):
		"""Suma horas teóricas y prácticas en el campo total_hours."""
		self.total_hours = (self.theory_hours or 0) + (self.practical_hours or 0)

	def _validar_tipo_curso(self):
		"""El curso asociado debe ser de tipo Modular o Técnico, no Libre."""
		if not self.course:
			return
		course_type = frappe.db.get_value("Course", self.course, "course_type")
		if course_type == "Libre":
			frappe.throw(
				"No se pueden crear módulos para un Curso de tipo Libre. "
				"Solo los cursos de tipo Modular o Técnico admiten módulos."
			)

	def _validar_asignaturas_duplicadas(self):
		"""No permite agregar la misma asignatura dos veces en el módulo."""
		cursos_vistos = []
		for row in self.courses_in_module:
			if row.course in cursos_vistos:
				frappe.throw(
					f"La asignatura '{row.course}' está duplicada en la tabla "
					f"de asignaturas del módulo. Cada asignatura debe aparecer "
					f"una sola vez."
				)
			cursos_vistos.append(row.course)

	def _validar_prerrequisito_circular(self):
		"""Un módulo no puede ser prerrequisito de sí mismo."""
		for row in self.prerequisites:
			if row.prerequisite_module == self.name:
				frappe.throw(
					"Un módulo no puede ser prerrequisito de sí mismo."
				)
