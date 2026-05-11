# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class Program(Document):
	def validate(self):
		self._validate_age_range()
		self._sync_program_modules()
		self._calculate_duration()

	def on_update(self):
		self._sync_program_modules()
		self._calculate_duration()

	def _validate_age_range(self):
		"""RT-2: edad mínima no puede superar la máxima."""
		if self.min_age and self.max_age and int(self.min_age) > int(self.max_age):
			frappe.throw(
				_("La edad mínima ({0}) no puede ser mayor que la edad máxima ({1}).").format(
					self.min_age, self.max_age
				),
				title=_("Rango de edad inválido"),
			)

	def _sync_program_modules(self):
		"""RT-4: sincroniza la tabla program_modules con los Program Module vinculados a este programa."""
		if self.program_type not in ("Modular", "Técnico"):
			self.set("program_modules", [])
			return

		if self.is_new():
			return

		modules = frappe.get_all(
			"Program Module",
			filters={"program": self.name},
			fields=["name", "module_name", "order_no", "status", "total_hours"],
			order_by="order_no asc, module_name asc",
		)

		fetched_names = {m.name for m in modules}
		existing_names = {row.module for row in self.get("program_modules", [])}

		# Agregar módulos nuevos
		for m in modules:
			if m.name not in existing_names:
				self.append("program_modules", {
					"module": m.name,
					"module_name": m.module_name or "",
					"order_no": m.order_no or 0,
					"status": m.status or "",
					"total_hours": m.total_hours or 0,
				})

		# Remover filas de módulos que ya no existen
		self.set(
			"program_modules",
			[row for row in self.get("program_modules", []) if row.module in fetched_names],
		)

	def _calculate_duration(self):
		"""Calcula la duración total sumando total_hours de todos los módulos vinculados."""
		if self.program_type not in ("Modular", "Técnico") or self.is_new():
			return

		result = frappe.db.sql(
			"SELECT COALESCE(SUM(total_hours), 0) FROM `tabProgram Module` WHERE program = %s",
			self.name,
		)
		self.program_duration = result[0][0] if result else 0

	def get_course_list(self):
		course_list = [
			frappe.get_doc("Course", pc.course) for pc in self.courses
		]
		return course_list
