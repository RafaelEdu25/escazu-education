# Copyright (c) 2026, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe.utils import flt


class FeeRequest(Document):
	def before_save(self):
		if self.fee_components:
			total_amount = sum([flt(component.amount) for component in self.fee_components])
			self.total_amount = total_amount
			self.outstanding_amount = total_amount

	def on_cancel(self):
		if self.payments:
			if any(
				frappe.get_doc("Fee Request Payment", payment.fee_request_payment).docstatus == 1
				for payment in self.payments
			):
				frappe.throw(
					"Cannot cancel Fee Request as there are submitted Fee Request Payment(s) linked to it. Cancel the linked Fee Request Payment(s) before cancelling this Fee Request."
				)


@frappe.whitelist()
def get_fee_structure_template(fee_structure_template):
	fee_component_doc = frappe.get_doc("Fee Structure", fee_structure_template)
	return fee_component_doc.components
