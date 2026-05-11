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
		if frappe.db.exists({"doctype": "Resource Booking", "physical_resource": self.name, "status": ("!=", "Cancelada")}):
			frappe.throw(_("No se puede eliminar el recurso porque tiene reservas activas o pendientes. Primero se deben cancelar las reservas asociadas."))
