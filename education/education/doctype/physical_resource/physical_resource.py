import frappe
from frappe.model.document import Document
from frappe import _

class PhysicalResource(Document):
	def validate(self):
		self.validate_room_status()
		self.validate_code_unique()

	def validate_room_status(self):
		if self.room:
			status = frappe.db.get_value("Room", self.room, "status")
			if status and status != "Disponible":
				frappe.throw(_("El aula {0} no está disponible para asignar recursos porque su estado es {1}. Cambie el estado del aula antes de asignar recursos.").format(self.room, status))

	def validate_code_unique(self):
		if frappe.db.exists({"doctype": "Physical Resource", "resource_code": self.resource_code, "name": ("!=", self.name)}):
			frappe.throw(_("El código {0} ya está en uso por otro recurso.").format(self.resource_code))

	def on_trash(self):
		# 1. Verificar reservas (Lógica existente)
		if frappe.db.exists({"doctype": "Resource Booking", "physical_resource": self.name, "status": ("!=", "Cancelada")}):
			frappe.throw(_("No se puede eliminar el recurso porque tiene reservas activas o pendientes. Primero se deben cancelar las reservas asociadas."))

		# 2. Verificar si el aula está "activa" (Nueva lógica)
		if self.room:
			# A. Tiempo de Clase (Course Schedule ahora mismo)
			now_time = frappe.utils.nowtime()
			today_date = frappe.utils.today()
			
			active_class = frappe.db.sql("""
				SELECT name FROM `tabCourse Schedule` 
				WHERE room = %s AND schedule_date = %s 
				AND %s BETWEEN from_time AND to_time
			""", (self.room, today_date, now_time))

			if active_class:
				frappe.throw(_("No se puede eliminar este recurso porque está activo (Hay una clase en curso en el aula {0}).").format(self.room))

			# B. Matrícula Activa (Cualquier admisión abierta)
			active_enrollment_period = frappe.db.exists("Student Admission", {"status": "Open"})
			if active_enrollment_period:
				# Si hay una matrícula abierta, verificamos si el aula pertenece a un grupo activo
				is_room_in_use = frappe.db.exists("Student Group", {"room": self.room, "status": "Activo"})
				if is_room_in_use:
					frappe.throw(_("No se puede eliminar este recurso porque está activo (Periodo de matrícula activo y aula asignada a un grupo)."))
